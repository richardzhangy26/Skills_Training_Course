import importlib.util
import base64
import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    PROJECT_ROOT
    / ".claude"
    / "skills"
    / "training-background-generator"
    / "scripts"
    / "generate_background.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "training_background_generator", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_pro_stage_uses_card_and_background_descriptions() -> None:
    generator = load_generator()
    content = """### 阶段1: 冲突识别
**卡片描述**: 识别急诊候诊冲突并完成首次回应
**背景图描述**: 夜间儿童医院急诊分诊台，家属在候诊区焦急等待

**阶段剧本提示词**:
<script_prompt>
【阶段触发条件】
训练开始。
</script_prompt>
"""

    stages = generator.parse_script_markdown(content)

    assert len(stages) == 1
    assert stages[0].description == "识别急诊候诊冲突并完成首次回应"
    assert stages[0].scene_config == "夜间儿童医院急诊分诊台，家属在候诊区焦急等待"


def write_secrets(tmp_path, **image_overrides):
    image = {
        "url": "https://images.example/v1/images/generations",
        "api_key": "test-image-key",
        "model": "gpt-image-2",
        "size": "2560x1440",
        "fallback_url": "https://fallback.example/images/generations",
        "fallback_api_key": "test-fallback-key",
        "fallback_model": "seedream-test",
    }
    image.update(image_overrides)
    path = tmp_path / "secrets.json"
    path.write_text(json.dumps({"providers": {"image": image, "llm": {
        "url": "https://text.example/v1", "api_key": "test-text-key",
        "model": "text-test",
    }}}))
    return path


def test_secrets_image_takes_priority_over_legacy_environment(tmp_path, monkeypatch):
    generator = load_generator()
    path = write_secrets(tmp_path)
    monkeypatch.setenv("BAILIAN_API_KEY", "legacy-key")
    config = generator.resolve_image_config(secrets_file=path)
    assert (config.model, config.size, config.api_key) == (
        "gpt-image-2", "2560x1440", "test-image-key"
    )
    assert config.url == "https://images.example/v1/images/generations"
    assert config.api_key not in repr(config)


def test_explicit_model_and_size_override_secrets_defaults(tmp_path):
    generator = load_generator()
    config = generator.resolve_image_config(
        secrets_file=write_secrets(tmp_path), model="custom-image", size="1920x1080"
    )
    assert (config.model, config.size) == ("custom-image", "1920x1080")


def test_explicit_fallback_model_uses_matching_url_and_key(tmp_path):
    generator = load_generator()
    config = generator.resolve_image_config(
        secrets_file=write_secrets(tmp_path), model="seedream-test"
    )
    assert config.url == "https://fallback.example/images/generations"
    assert config.api_key == "test-fallback-key"
    assert config.fallback is None


def test_default_config_keeps_fallback_with_its_own_url_and_key(tmp_path):
    generator = load_generator()
    config = generator.resolve_image_config(secrets_file=write_secrets(tmp_path), size="1920x1080")
    assert config.fallback is not None
    assert (config.fallback.url, config.fallback.model, config.fallback.size) == (
        "https://fallback.example/images/generations", "seedream-test", "1920x1080"
    )
    assert config.fallback.api_key == "test-fallback-key"
    assert "test-fallback-key" not in repr(config)


def test_missing_default_secrets_preserves_bailian_mode(tmp_path, monkeypatch):
    generator = load_generator()
    monkeypatch.setattr(generator, "DEFAULT_SECRETS_FILE", tmp_path / "missing.json")
    monkeypatch.setenv("BAILIAN_API_KEY", "legacy-key")
    config = generator.resolve_image_config()
    assert (config.model, config.size, config.api_key, config.url) == (
        generator.DEFAULT_IMAGE_MODEL, generator.DEFAULT_SIZE,
        "legacy-key", generator.BAILIAN_IMAGE_URL,
    )


def test_incomplete_secrets_does_not_silently_use_other_credentials(tmp_path, monkeypatch):
    generator = load_generator()
    path = write_secrets(tmp_path, api_key="")
    monkeypatch.setenv("BAILIAN_API_KEY", "legacy-key")
    with pytest.raises(ValueError, match="providers.image.api_key"):
        generator.resolve_image_config(secrets_file=path)


@pytest.mark.parametrize("response", [
    {"data": [{"url": "https://result.example/image.png"}]},
    {"data": [{"b64_json": base64.b64encode(b"image-bytes").decode()}]},
])
def test_openai_image_response_can_be_saved(tmp_path, monkeypatch, response):
    generator = load_generator()
    calls = []

    class Response:
        content = b"image-bytes"

        def raise_for_status(self):
            pass

        def json(self):
            return response

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(generator.requests, "post", post)
    monkeypatch.setattr(generator.requests, "get", lambda *a, **k: Response())
    result = generator.generate_image(
        "教室", "gpt-image-2", "2560x1440", "test-key",
        api_url="https://images.example/v1/images/generations",
    )
    output = tmp_path / "image.png"
    generator.download_image(result, output)
    assert output.read_bytes() == b"image-bytes"
    assert calls[0][1]["json"] == {
        "model": "gpt-image-2", "prompt": "教室", "size": "2560x1440", "n": 1,
    }


def test_process_uses_secrets_for_cover_and_stage_and_keeps_record_secret_free(tmp_path, monkeypatch):
    generator = load_generator()
    secrets = write_secrets(tmp_path)
    md = tmp_path / "训练剧本配置.md"
    md.write_text("""## 基础配置
- **任务名称**: 教学实训
- **任务描述**: 课堂训练

## 阶段配置
### 阶段1: 开场
**背景图**: 待生成
""")
    calls = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": [{"b64_json": base64.b64encode(b"png-test").decode()}]}

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(generator.requests, "post", post)
    monkeypatch.setattr(generator.time, "sleep", lambda _: None)
    record = generator.process(str(md), secrets_file=secrets, use_llm_prompt=False)
    assert len(calls) == 2
    assert all(c[1]["json"]["model"] == "gpt-image-2" for c in calls)
    assert all(c[1]["headers"]["Authorization"] == "Bearer test-image-key" for c in calls)
    assert record["model"] == "gpt-image-2"
    assert record["size"] == "2560x1440"
    assert len(record["success"]) == 1
    saved = tmp_path / "backgrounds" / "generation_record.json"
    assert "test-image-key" not in saved.read_text()
    assert "base64" not in saved.read_text()
    assert str(Path(record["success"][0]["file"]).resolve()) in md.read_text()


def test_text_client_uses_secrets_without_legacy_key(tmp_path, monkeypatch):
    generator = load_generator()
    monkeypatch.delenv("BAILIAN_API_KEY", raising=False)
    client = generator._get_text_client(secrets_file=write_secrets(tmp_path))
    assert client.api_key == "test-text-key"
    assert str(client.base_url).rstrip("/") == "https://text.example/v1"


def test_cli_defers_defaults_until_secrets_are_loaded():
    args = load_generator().parse_args(["test.md"])
    assert args.model is None
    assert args.size is None


def test_dashscope_request_remains_compatible(monkeypatch):
    generator = load_generator()
    calls = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"output": {"choices": [{"message": {
                "content": [{"image": "https://result.example/legacy.png"}]
            }}]}}

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(generator.requests, "post", post)
    url = generator.generate_image("教室", "qwen-image-test", "1664x928", "legacy-key")
    assert url == "https://result.example/legacy.png"
    assert calls[0][0] == generator.BAILIAN_IMAGE_URL
    assert calls[0][1]["json"]["parameters"]["size"] == "1664*928"


def test_primary_failure_falls_back_to_seedream(tmp_path, monkeypatch):
    generator = load_generator()
    md = tmp_path / "test.md"
    md.write_text("### 阶段1: 开场\n**背景图**: 待生成\n")
    calls = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": [{"url": "https://result.example/seedream.png"}]}

    def post(url, **kwargs):
        calls.append((url, kwargs))
        if url == "https://images.example/v1/images/generations":
            raise generator.requests.HTTPError("429 Too Many Requests")
        return Response()

    monkeypatch.setattr(generator.requests, "post", post)
    monkeypatch.setattr(generator, "download_image", lambda url, path: path.write_bytes(b"png"))
    monkeypatch.setattr(generator.time, "sleep", lambda _: None)
    record = generator.process(
        str(md), secrets_file=write_secrets(tmp_path), use_llm_prompt=False
    )
    assert [c[0] for c in calls] == [
        "https://images.example/v1/images/generations",
        "https://fallback.example/images/generations",
    ]
    assert calls[1][1]["headers"]["Authorization"] == "Bearer test-fallback-key"
    assert calls[1][1]["json"]["model"] == "seedream-test"
    assert record["failed"] == []
    assert record["fallback_model"] == "seedream-test"
    assert record["success"][0]["model"] == "seedream-test"
    assert "429" in record["success"][0]["primary_error"]


def test_primary_and_fallback_failures_are_both_recorded(tmp_path, monkeypatch):
    generator = load_generator()
    md = tmp_path / "test.md"
    md.write_text("### 阶段1: 开场\n**背景图**: 待生成\n")
    calls = []

    def post(url, **kwargs):
        calls.append(url)
        raise generator.requests.HTTPError("500 Server Error")

    monkeypatch.setattr(generator.requests, "post", post)
    record = generator.process(
        str(md), secrets_file=write_secrets(tmp_path), use_llm_prompt=False
    )
    assert calls == [
        "https://images.example/v1/images/generations",
        "https://fallback.example/images/generations",
    ]
    assert record["success"] == []
    assert "备用 seedream-test 失败" in record["failed"][0]["error"]


def test_primary_failure_without_fallback_is_recorded(tmp_path, monkeypatch):
    generator = load_generator()
    md = tmp_path / "test.md"
    md.write_text("### 阶段1: 开场\n**背景图**: 待生成\n")
    calls = []

    def post(url, **kwargs):
        calls.append(url)
        raise generator.requests.HTTPError("429 Too Many Requests")

    monkeypatch.setattr(generator.requests, "post", post)
    record = generator.process(
        str(md), secrets_file=write_secrets(tmp_path, fallback_model=""),
        use_llm_prompt=False,
    )
    assert calls == ["https://images.example/v1/images/generations"]
    assert len(record["failed"]) == 1
    assert record["success"] == []


def test_seedream_request_disables_watermark(monkeypatch):
    generator = load_generator()
    calls = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": [{"url": "https://result.example/seedream.png"}]}

    monkeypatch.setattr(generator.requests, "post", lambda url, **k: calls.append(k) or Response())
    generator.generate_image(
        "教室", "seedream-test", "2560x1440", "key",
        api_url="https://ark.cn-beijing.volces.com/api/v3/images/generations",
    )
    assert calls[0]["json"]["watermark"] is False


def test_malformed_json_reports_location_without_echoing_contents(tmp_path):
    generator = load_generator()
    path = tmp_path / "secrets.json"
    path.write_text('{"api_key": "private-test-value", broken}')
    with pytest.raises(ValueError) as exc:
        generator.resolve_image_config(secrets_file=path)
    assert "private-test-value" not in str(exc.value)
    assert "有效 JSON" in str(exc.value)


def test_process_uses_llm_model_and_credentials_from_same_secrets(tmp_path, monkeypatch):
    generator = load_generator()
    md = tmp_path / "test.md"
    md.write_text("### 阶段1: 开场\n**背景图**: 待生成\n")
    seen = []

    def generate_prompt(client, stage, style_suffix, text_model):
        seen.append((client.api_key, str(client.base_url).rstrip("/"), text_model))
        return "教室，自然光"

    monkeypatch.setattr(generator, "generate_prompt_via_llm", generate_prompt)
    monkeypatch.setattr(generator, "generate_image", lambda *a, **k: (
        "data:image/png;base64," + base64.b64encode(b"png-test").decode()
    ))
    monkeypatch.setattr(generator.time, "sleep", lambda _: None)
    record = generator.process(str(md), secrets_file=write_secrets(tmp_path))
    assert seen == [("test-text-key", "https://text.example/v1", "text-test")]
    assert record["text_model"] == "text-test"
    assert len(record["success"]) == 1
