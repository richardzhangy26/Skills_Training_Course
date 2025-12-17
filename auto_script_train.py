import requests
import json
import time
import os
import difflib
import math
import re
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from typing import Optional, List, Dict
from workflow_tester_base import WorkflowTesterBase


class DialogueEntry:
    """对话日志条目"""
    def __init__(self, timestamp: str, step_id: str, source: str,
                 ai_text: Optional[str] = None, user_text: Optional[str] = None,
                 round_num: Optional[int] = None):
        self.timestamp = timestamp
        self.step_id = step_id
        self.source = source  # "runCard" 或 "chat"
        self.ai_text = ai_text
        self.user_text = user_text
        self.round_num = round_num

    def __repr__(self):
        return f"DialogueEntry(timestamp={self.timestamp}, step_id={self.step_id}, " \
               f"source={self.source}, round={self.round_num})"


class DialogueLogParser:
    """对话日志解析器"""

    @staticmethod
    def parse_log_file(log_path: str) -> List[DialogueEntry]:
        """
        解析对话日志文件

        Args:
            log_path: 日志文件路径

        Returns:
            解析后的对话条目列表
        """
        entries = []

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 读取日志文件失败: {str(e)}")
            return entries

        # 按分隔符分割对话块（处理可能的换行符差异）
        separator = '-' * 80
        # 替换所有可能的分隔符变体为统一格式
        normalized_content = content.replace(separator + '\r\n', separator + '\n')
        normalized_content = normalized_content.replace(separator + '\r', separator + '\n')
        blocks = normalized_content.split(separator + '\n')

        for block in blocks:
            if not block.strip():
                continue

            entry = DialogueLogParser._parse_block(block)
            if entry:
                entries.append(entry)

        print(f"✅ 解析日志文件完成，共 {len(entries)} 个对话条目")
        return entries

    @staticmethod
    def _parse_block(block: str) -> Optional[DialogueEntry]:
        """解析单个对话块"""
        lines = block.strip().split('\n')
        if not lines:
            return None

        # 解析头部信息
        header = lines[0]
        timestamp, step_id, round_num, source = DialogueLogParser._parse_header(header)

        # 解析用户和AI文本
        ai_text = None
        user_text = None

        for line in lines[1:]:
            line = line.strip()
            if line.startswith('AI:'):
                ai_text = line[3:].strip()
            elif line.startswith('用户:'):
                user_text = line[3:].strip()

        return DialogueEntry(
            timestamp=timestamp,
            step_id=step_id,
            source=source,
            ai_text=ai_text,
            user_text=user_text,
            round_num=round_num
        )

    @staticmethod
    def _parse_header(header: str) -> tuple:
        """解析头部信息"""
        # 示例: [2025-11-28 16:01:21] Step GnxX4RzREzTrXNmRGxq0 | 第 1 轮 | 来源: chat
        timestamp = ""
        step_id = ""
        round_num = None
        source = "chat"

        try:
            # 提取时间戳
            if header.startswith('['):
                end_idx = header.find(']')
                if end_idx > 0:
                    timestamp = header[1:end_idx].strip()

            # 提取步骤ID
            step_start = header.find('Step ')
            if step_start > 0:
                step_end = header.find(' |', step_start)
                if step_end > 0:
                    step_id = header[step_start + 5:step_end].strip()

            # 提取轮次
            round_start = header.find('第 ')
            if round_start > 0:
                round_end = header.find(' 轮', round_start)
                if round_end > 0:
                    round_str = header[round_start + 2:round_end].strip()
                    try:
                        round_num = int(round_str)
                    except ValueError:
                        round_num = None

            # 提取来源
            source_start = header.find('来源: ')
            if source_start > 0:
                source = header[source_start + 4:].strip()
        except Exception as e:
            print(f"⚠️  解析头部信息失败: {header}, 错误: {str(e)}")

        return timestamp, step_id, round_num, source

    @staticmethod
    def extract_dialogue_pairs(entries: List[DialogueEntry]) -> List[Dict]:
        """
        从对话条目中提取AI提问-用户回答对

        Args:
            entries: 对话条目列表

        Returns:
            [{"ai": ai_text, "user": user_text}, ...]
        """
        # Important: chat blocks contain A_i (user) and Q_{i+1} (AI).
        # We pair each user answer with the most recent AI question seen earlier.
        pairs: List[Dict] = []
        last_ai_text: Optional[str] = None
        last_ai_meta: Dict = {}

        for entry in entries:
            if entry.user_text and last_ai_text:
                pairs.append({
                    "ai": last_ai_text,
                    "user": entry.user_text,
                    "timestamp": entry.timestamp,
                    "step_id": last_ai_meta.get("step_id") or entry.step_id,
                    "round_num": entry.round_num,
                })

            if entry.ai_text:
                last_ai_text = entry.ai_text
                last_ai_meta = {
                    "timestamp": entry.timestamp,
                    "step_id": entry.step_id,
                    "round_num": entry.round_num,
                }

        print(f"✅ 提取到 {len(pairs)} 个对话对")
        return pairs


class DialogueMatcher:
    """对话匹配器"""

    def __init__(self, similarity_threshold: float = 0.7):
        """
        初始化匹配器

        Args:
            similarity_threshold: 相似度阈值，默认0.7
        """
        self.threshold = similarity_threshold

    def find_best_match(
        self,
        ai_question: str,
        dialogue_pairs: List[Dict],
        step_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        查找最佳匹配的用户回答

        Args:
            ai_question: 当前AI提问
            dialogue_pairs: 历史对话对列表

        Returns:
            匹配的用户回答，或None表示未找到
        """
        if not dialogue_pairs:
            return None

        candidates = dialogue_pairs
        if step_id:
            step_candidates = [p for p in dialogue_pairs if p.get("step_id") == step_id]
            if step_candidates:
                candidates = step_candidates

        best_match = None
        best_similarity = 0.0
        best_pair_info = None

        for pair in candidates:
            historical_ai = pair.get("ai", "")
            if not historical_ai:
                continue

            similarity = self.calculate_similarity(ai_question, historical_ai)

            if similarity > best_similarity and similarity >= self.threshold:
                best_similarity = similarity
                best_match = pair.get("user")
                best_pair_info = {
                    "similarity": similarity,
                    "historical_ai": historical_ai,
                    "timestamp": pair.get("timestamp"),
                    "step_id": pair.get("step_id"),
                    "round_num": pair.get("round_num")
                }

        if best_match:
            print(f"✅ 找到匹配回答，相似度: {best_similarity:.2f}")
            if best_pair_info:
                print(f"   原始AI提问: {best_pair_info['historical_ai'][:50]}...")
                print(f"   时间: {best_pair_info.get('timestamp')}, 步骤: {best_pair_info.get('step_id')}")
        else:
            print(f"❌ 未找到匹配回答 (最高相似度: {best_similarity:.2f}, 阈值: {self.threshold})")

        return best_match

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0

        # 预处理：去除多余空格和换行符
        text1_clean = ' '.join(text1.split())
        text2_clean = ' '.join(text2.split())

        # 使用difflib计算相似度
        return difflib.SequenceMatcher(None, text1_clean, text2_clean).ratio()


class DialogueReplayEngine:
    """对话回放引擎"""

    def __init__(self, log_path: str, similarity_threshold: float = 0.7):
        """
        初始化回放引擎

        Args:
            log_path: 日志文件路径
            similarity_threshold: 相似度阈值
        """
        self.log_path = log_path
        self.threshold = similarity_threshold
        self.parser = DialogueLogParser()
        self.matcher = DialogueMatcher(similarity_threshold)
        self.dialogue_pairs = None
        self.loaded = False

    def load_log(self) -> bool:
        """加载和解析日志文件"""
        try:
            entries = self.parser.parse_log_file(self.log_path)
            self.dialogue_pairs = self.parser.extract_dialogue_pairs(entries)
            self.loaded = True
            return True
        except Exception as e:
            print(f"❌ 加载日志失败: {str(e)}")
            return False

    def get_answer(self, ai_question: str, step_id: Optional[str] = None) -> Optional[str]:
        """
        获取匹配的回答

        Args:
            ai_question: AI提问
            step_id: 当前步骤ID（可选，用于过滤候选）

        Returns:
            匹配的用户回答，或None表示未找到
        """
        if not self.loaded or not self.dialogue_pairs:
            print("⚠️  日志未加载或为空")
            return None

        return self.matcher.find_best_match(ai_question, self.dialogue_pairs, step_id=step_id)

    def get_match_info(self, ai_question: str, step_id: Optional[str] = None) -> Dict:
        """
        获取匹配的详细信息

        Args:
            ai_question: AI提问
            step_id: 当前步骤ID（可选）

        Returns:
            匹配信息字典
        """
        if not self.loaded or not self.dialogue_pairs:
            return {"error": "日志未加载或为空"}

        best_match = None
        best_similarity = 0.0
        best_pair = None

        candidates = self.dialogue_pairs
        if step_id:
            step_candidates = [p for p in self.dialogue_pairs if p.get("step_id") == step_id]
            if step_candidates:
                candidates = step_candidates

        for pair in candidates:
            historical_ai = pair.get("ai", "")
            if not historical_ai:
                continue

            similarity = self.matcher.calculate_similarity(ai_question, historical_ai)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = pair.get("user")
                best_pair = pair

        return {
            "matched": best_similarity >= self.threshold,
            "similarity": best_similarity,
            "answer": best_match,
            "threshold": self.threshold,
            "historical_ai": best_pair.get("ai") if best_pair else None,
            "timestamp": best_pair.get("timestamp") if best_pair else None,
            "step_id": best_pair.get("step_id") if best_pair else None,
            "round_num": best_pair.get("round_num") if best_pair else None,
            "total_pairs": len(candidates)
        }


class EmbeddingClient:
    """OpenAI-compatible embedding client using api-key header."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://llm-service.polymas.com/api/openai/v1",
        model: str = "text-embedding-3-small",
        max_batch_size: int = 25,
        timeout: int = 60,
    ):
        self.api_key = api_key
        base_url = base_url.rstrip("/")
        self.embed_url = base_url if base_url.endswith("/embeddings") else base_url + "/embeddings"
        self.model = model
        self.max_batch_size = max_batch_size
        self.timeout = timeout
        self.session = requests.Session()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        embeddings: List[List[float]] = []
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i : i + self.max_batch_size]
            payload = {"input": batch, "model": self.model}
            resp = self.session.post(self.embed_url, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json() or {}
            items = data.get("data") or []
            # Ensure original ordering by index if provided.
            items = sorted(items, key=lambda x: x.get("index", 0))
            embeddings.extend([it.get("embedding") for it in items])

        return embeddings


class JsonDialogueReplayEngine:
    """Replay engine based on exported dialogue JSON + embeddings."""

    def __init__(
        self,
        json_path: str,
        similarity_threshold: float = 0.8,
        embedding_model: str = "text-embedding-3-large",
        embedding_base_url: str = "https://llm-service.polymas.com/api/openai/v1",
    ):
        self.json_path = json_path
        self.threshold = similarity_threshold
        self.embedding_model = embedding_model
        self.embedding_base_url = embedding_base_url
        self.dialogue_pairs: List[Dict] = []
        self.loaded = False
        self.embed_client: Optional[EmbeddingClient] = None
        self._last_query_key = None
        self._last_match_info: Optional[Dict] = None

    @staticmethod
    def _normalize_question(text: str) -> str:
        # Strip think tags / artifacts.
        text = re.sub(r"</?think[^>]*>", "", text or "")
        text = text.strip()
        if not text:
            return text
        # Take the last sentence ending with '?' or '？' to reduce noise.
        matches = re.findall(r"[^。！？\n\r]*[？\?]", text)
        if matches:
            return matches[-1].strip()
        return text

    def _parse_json_pairs(self, data: Dict) -> List[Dict]:
        pairs: List[Dict] = []
        last_ai_raw: Optional[str] = None
        last_ai_norm: Optional[str] = None
        last_step_id: Optional[str] = None
        last_stage_index: Optional[int] = None

        for stage in data.get("stages", []) or []:
            step_id = stage.get("step_id") or stage.get("stepId")
            stage_index = stage.get("stage_index") or stage.get("stageIndex")
            for m in stage.get("messages", []) or []:
                role = m.get("role")
                content = (m.get("content") or "").strip()
                if not content:
                    continue
                if role == "assistant":
                    last_ai_raw = content
                    last_ai_norm = self._normalize_question(content)
                    last_step_id = step_id
                    last_stage_index = stage_index
                elif role == "user" and last_ai_norm:
                    pairs.append({
                        "ai": last_ai_norm,
                        "ai_raw": last_ai_raw,
                        "user": content,
                        "step_id": last_step_id,
                        "round_num": m.get("round"),
                        "stage_index": last_stage_index,
                    })
        return pairs

    def load_log(self) -> bool:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 读取 JSON 回放文件失败: {str(e)}")
            return False

        self.dialogue_pairs = self._parse_json_pairs(data)
        if not self.dialogue_pairs:
            print("⚠️  JSON 中未提取到可用对话对")
            return False

        # Try load cached embeddings to avoid recomputation.
        cache_path = Path(self.json_path).with_name(Path(self.json_path).stem + "_replay_index.json")
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                if isinstance(cached, list) and all("emb" in p for p in cached):
                    self.dialogue_pairs = cached
                    self.loaded = True
                    print(f"✅ 已加载 embedding 索引缓存: {str(cache_path)}")
                    return True
            except Exception:
                pass

        api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("ARK_API_KEY")
        if not api_key:
            print("❌ 未设置 EMBEDDING_API_KEY，无法生成 embedding")
            return False

        self.embed_client = EmbeddingClient(
            api_key=api_key,
            base_url=self.embedding_base_url,
            model=self.embedding_model,
            max_batch_size=6 if "embedding-v3" in self.embedding_model or self.embedding_model.endswith("v3") else 25,
        )

        try:
            texts = [p["ai"] for p in self.dialogue_pairs]
            embs = self.embed_client.embed_texts(texts)
            if len(embs) != len(self.dialogue_pairs):
                print("⚠️  embedding 数量与对话对数量不一致，将回退到普通模式")
                return False
            for p, e in zip(self.dialogue_pairs, embs):
                p["emb"] = e
            # Write cache.
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(self.dialogue_pairs, f, ensure_ascii=False)
                print(f"✅ 已写入 embedding 索引缓存: {str(cache_path)}")
            except Exception:
                pass
            self.loaded = True
            return True
        except Exception as e:
            print(f"❌ 生成 embedding 失败: {str(e)}")
            return False

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb + 1e-9)

    def get_answer(self, ai_question: str, step_id: Optional[str] = None) -> Optional[str]:
        if not self.loaded or not self.dialogue_pairs or not self.embed_client:
            print("⚠️  JSON 回放引擎未加载")
            return None

        q_norm = self._normalize_question(ai_question)
        q_emb = self.embed_client.embed_texts([q_norm])[0]

        candidates = self.dialogue_pairs
        if step_id:
            step_candidates = [p for p in self.dialogue_pairs if p.get("step_id") == step_id]
            if step_candidates:
                candidates = step_candidates

        best_pair = None
        best_sim = 0.0
        for p in candidates:
            emb = p.get("emb")
            if not emb:
                continue
            sim = self._cosine(q_emb, emb)
            if sim > best_sim:
                best_sim = sim
                best_pair = p

        self._last_query_key = (ai_question, step_id)
        self._last_match_info = {
            "matched": bool(best_pair and best_sim >= self.threshold),
            "similarity": best_sim,
            "answer": best_pair.get("user") if best_pair else None,
            "threshold": self.threshold,
            "historical_ai": (best_pair.get("ai_raw") or best_pair.get("ai")) if best_pair else None,
            "step_id": best_pair.get("step_id") if best_pair else None,
            "round_num": best_pair.get("round_num") if best_pair else None,
            "total_pairs": len(candidates),
        }

        if best_pair and best_sim >= self.threshold:
            print(f"✅ JSON 回放命中，相似度: {best_sim:.3f}")
            return best_pair.get("user")

        print(f"❌ JSON 回放未命中 (最高相似度: {best_sim:.3f}, 阈值: {self.threshold})")
        return None

    def get_match_info(self, ai_question: str, step_id: Optional[str] = None) -> Dict:
        key = (ai_question, step_id)
        if self._last_query_key == key and self._last_match_info:
            return self._last_match_info
        # Fallback: run a match to populate info.
        _ = self.get_answer(ai_question, step_id=step_id)
        return self._last_match_info or {"matched": False, "similarity": 0.0}


class WorkflowTester(WorkflowTesterBase):
    DEFAULT_PROFILE_KEY = "medium"
    PROFILE_LABEL_FIELD_NAME = "学生档位"
    PROFILE_SELECT_TITLE = "学生档位"

    STUDENT_PROFILES = {
        "good": {
            "label": "优秀学生",
            "description": "理解透彻、表达清晰，回答结构化、条理分明，并主动总结要点。",
            "style": "语气自信、语言规范，必要时引用题目或材料中的关键信息。",
            "fallback_hint": "若模拟对话中没有合适示例，可自己组织最佳答案，保持高水平。"
        },
        "medium": {
            "label": "需要引导的学生",
            "description": "基本理解问题但不够全面，回答中会暴露疑惑或请求提示。",
            "style": "语气略显犹豫，能覆盖核心内容，但会提出 1-2 个不确定点或寻求老师建议。",
            "fallback_hint": "示例缺失时，先回答主要内容再说明不确定之处。"
        },
        "bad": {
            "label": "答非所问的学生",
            "description": "理解偏差，常常跑题或只复述与问题弱相关的信息。",
            "style": "语气随意，容易偏离重点或答非所问。",
            "fallback_hint": "即使需要自己生成，也要保持轻微跑题或误解的特征。"
        }
    }

    def __init__(self, base_url="https://cloudapi.polymas.com"):
        super().__init__(base_url)

        # Provide profile data for base prompt/selection helpers.
        self.student_profiles = self.STUDENT_PROFILES

        # 重试配置
        self.max_retries = 3  # 最大重试次数
        self.base_timeout = 60  # 基础超时时间（秒）
        self.retry_backoff = 2  # 重试退避因子

        # 初始化 Doubao 客户端
        self.doubao_client = None
        self.doubao_model = os.getenv("DOUBAO_MODEL", "doubao-seed-1-6-251015")
        self.model_type = "doubao_sdk"

        # 回放模式相关属性
        self.replay_engine = None
        self.use_replay_mode = False
        self.similarity_threshold = 0.7
        self.replay_log_path = None

        self._initialize_doubao_client()

    def _initialize_doubao_client(self):
        """初始化 Doubao 客户端"""
        api_key = os.getenv("ARK_API_KEY")
        base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

        if api_key:
            try:
                self.doubao_client = OpenAI(api_key=api_key, base_url=base_url)
            except Exception as e:
                print(f"⚠️  警告: 初始化 Doubao 客户端失败: {str(e)}")

    def _retry_request(self, request_func, *args, **kwargs):
        """
        通用重试机制

        Args:
            request_func: 要执行的请求函数
            *args, **kwargs: 传递给请求函数的参数

        Returns:
            请求结果
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # 动态调整超时时间
                timeout = self.base_timeout * (attempt + 1)
                if 'timeout' in kwargs:
                    kwargs['timeout'] = timeout

                print(f"🔄 尝试第 {attempt + 1}/{self.max_retries} 次请求 (超时: {timeout}秒)...")

                result = request_func(*args, **kwargs)

                # 如果成功，返回结果
                if attempt > 0:
                    print(f"✅ 重试成功！")
                return result

            except requests.exceptions.ReadTimeout as e:
                last_exception = e
                print(f"⚠️  请求超时 (尝试 {attempt + 1}/{self.max_retries})")

                if attempt < self.max_retries - 1:
                    # 计算退避等待时间
                    wait_time = self.retry_backoff ** attempt
                    print(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 已达到最大重试次数")

            except requests.exceptions.RequestException as e:
                # 其他网络错误，不重试
                print(f"❌ 网络请求失败: {str(e)}")
                raise Exception(f"网络请求失败: {str(e)}")

        # 所有重试都失败
        raise Exception(f"请求超时，已重试 {self.max_retries} 次")

    def _post_json(self, url: str, payload: Dict, timeout: int):
        """Override base POST to add retries."""
        def make_request():
            return self.session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=timeout,
            )
        return self._retry_request(make_request)

    def _log_run_card(self, step_id, payload, response_data):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_lines = [
            f"[{timestamp}] Step {step_id}",
            f"请求载荷: {json.dumps(payload, ensure_ascii=False)}",
            f"响应内容: {json.dumps(response_data, ensure_ascii=False)}",
            "-" * 80,
        ]
        self._append_log(self.run_card_log_path, "\n".join(log_lines))

    def _log_dialogue_entry(self, step_id, user_text=None, ai_text=None, source="chat"):
        if user_text is None and ai_text is None:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        round_info = f" | 第 {self.dialogue_round} 轮" if self.dialogue_round else ""
        header = f"[{timestamp}] Step {step_id}{round_info} | 来源: {source}"
        lines = [header]
        if user_text:
            lines.append(f"用户: {user_text}")
        if ai_text:
            lines.append(f"AI: {ai_text}")
        lines.append("-" * 80)
        self._append_log(self.dialogue_log_path, "\n".join(lines))

        # Collect JSON stage data when enabled (base hook).
        if user_text:
            try:
                self._collect_stage_data(step_id, self.dialogue_round, "user", user_text)
            except Exception:
                pass
        if ai_text:
            try:
                self._collect_stage_data(step_id, self.dialogue_round, "assistant", ai_text)
            except Exception:
                pass

    def enable_replay_mode(self, log_path: str, similarity_threshold: float = 0.7):
        """
        启用回放模式

        Args:
            log_path: 日志文件路径
            similarity_threshold: 相似度阈值，默认0.7
        """
        self.use_replay_mode = True
        self.replay_log_path = log_path
        self.similarity_threshold = similarity_threshold

        # 创建回放引擎：支持 txt(difflib) 与 json(embedding) 两种格式
        if str(log_path).lower().endswith(".json"):
            emb_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            emb_base_url = os.getenv(
                "EMBEDDING_BASE_URL",
                "https://llm-service.polymas.com/api/openai/v1",
            )
            self.replay_engine = JsonDialogueReplayEngine(
                log_path,
                similarity_threshold=similarity_threshold,
                embedding_model=emb_model,
                embedding_base_url=emb_base_url,
            )
        else:
            self.replay_engine = DialogueReplayEngine(log_path, similarity_threshold)

        # 加载日志
        if self.replay_engine.load_log():
            print(f"\n🎯 已启用回放模式")
            print(f"   日志文件: {log_path}")
            print(f"   相似度阈值: {similarity_threshold}")
            print(f"   加载对话对: {len(self.replay_engine.dialogue_pairs or [])} 个")
        else:
            print(f"\n❌ 回放模式启用失败，将使用普通模式")
            self.use_replay_mode = False
            self.replay_engine = None

    def generate_answer_with_replay(self, question: str) -> str:
        """
        优先使用日志回答，回退到模型生成

        Args:
            question: AI提问

        Returns:
            用户回答
        """
        if not self.use_replay_mode or not self.replay_engine:
            print("⚠️  未启用回放模式，使用模型生成回答")
            return self.generate_answer_with_doubao(question)

        # 尝试从日志中获取匹配的回答
        step_id = getattr(self, "current_step_id", None)
        matched_answer = self.replay_engine.get_answer(question, step_id=step_id)

        if matched_answer:
            print(f"🎯 使用日志回答 (相似度匹配)")
            return matched_answer
        else:
            print("🔍 未找到匹配的日志回答，使用模型生成")
            return self.generate_answer_with_doubao(question)

    def generate_answer_with_doubao(self, question):
        """使用 Doubao 模型生成回答"""
        if not self.doubao_client:
            print("❌ Doubao 客户端未初始化")
            return None

        try:
            profile_info = self._get_student_profile_info()
            system_prompt = (
                "你是一名能力训练助手，需要严格按照给定的学生档位扮演角色。"
            )

            sections = [
                "## 角色设定",
                f"学生档位: {profile_info['label']}",
                f"角色特征: {profile_info['description']}",
                f"表达风格: {profile_info['style']}",
                "",
            ]

            if self.dialogue_samples_content:
                sections.extend([
                    "## 档位示例对话 (如有匹配请优先引用或改写)",
                    self.dialogue_samples_content,
                    "",
                ])

            if self.knowledge_base_content:
                sections.extend([
                    "## 参考知识库 (可结合使用)",
                    self.knowledge_base_content,
                    "",
                ])

            # 添加对话历史
            if self.conversation_history:
                sections.extend([
                    "## 对话历史（按时间顺序）",
                ])
                for i, turn in enumerate(self.conversation_history, 1):
                    sections.append(f"第{i}轮:")
                    sections.append(f"  AI提问: {turn['ai']}")
                    sections.append(f"  学生回答: {turn['student']}")
                sections.append("")

            sections.extend([
                "## 当前问题",
                question,
                "",
                "## 输出要求",
                "1. **字数限制**: 回答必须严格控制在50字以内。",
                "2. **确认式问题**: 如'你准备好了吗？请回复是或否'、'确认的话请回复是'等，直接回答'是'、'好的'、'确认'等简短词汇。",
                "3. **选择式问题**: 如'你选择A还是B？'、'请选择1/2/3'等，直接回复选项，如'A'、'1'等。",
                "4. 回答需与所选学生档位的语气、思路保持一致。",
                "5. 如果示例对话中存在高度相关的回答，请优先引用或在其基础上微调。",
                "6. 若示例未覆盖此问题，可自行生成，但需符合档位特征。",
                "7. 仅返回学生回答内容，不要额外解释。",
                "8. 保持简洁，避免冗余表达。"
            ])

            user_message = "\n".join(sections)

            response = self.doubao_client.chat.completions.create(
                model=self.doubao_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                top_p=0.9
            )

            answer = response.choices[0].message.content
            return answer
        except Exception as e:
            print(f"❌ 调用 Doubao 模型失败: {str(e)}")
            return None

    def run_semi_interactive(self, task_id, breakpoint_round: int = 0):
        """
        半交互式运行工作流：
        - 用户输入内容不为空时，按用户输入走流程
        - 用户直接回车（输入为空）时，让 Doubao 模型自动生成回答（默认好学生）
        - 用户输入 'continue' 时，后续全部自动让模型回答
        - 用户输入 'continue N' 时，自动运行到第 N 轮后恢复半交互

        Args:
            task_id: 任务ID
            breakpoint_round: 断点轮数，0表示不设断点
        """
        if not self.doubao_client:
            print("\n❌ Doubao 客户端未初始化，请检查 ARK_API_KEY 环境变量")
            return

        # 如果未设置学生档位，默认使用"好学生"
        if not self.student_profile_key:
            print("\n📚 半交互模式默认使用'优秀学生'档位生成回答")
            self.student_profile_key = "good"

        try:
            self.start_workflow(task_id)
            round_num = 1
            auto_continue = False  # 是否进入全自动模式
            current_breakpoint = breakpoint_round  # 当前断点轮数

            while True:
                if self.current_step_id is None:
                    print("\n✅ 工作流完成！没有更多步骤了。")
                    break

                if round_num > 50:
                    print(f"\n⚠️  警告：已达到最大对话轮数（{round_num}轮），自动退出防止无限循环")
                    break

                print("\n" + "=" * 60)
                mode_label = "全自动模式" if auto_continue else "半交互模式"
                print(f"💬 第 {round_num} 轮对话（{mode_label}）")
                print("=" * 60)

                if auto_continue:
                    # 检查是否到达断点
                    if current_breakpoint > 0 and round_num >= current_breakpoint:
                        print(f"\n🔴 到达断点（第 {current_breakpoint} 轮），切回半交互模式")
                        auto_continue = False
                        current_breakpoint = 0  # 清除断点
                        # 不 continue，继续走下面的半交互逻辑
                    else:
                        # 全自动模式：直接让模型生成回答
                        bp_info = f"（断点: 第 {current_breakpoint} 轮）" if current_breakpoint > 0 else ""
                        print(f"\n🤖 正在使用 Doubao 生成回答...{bp_info}")
                        answer = self.generate_answer_with_doubao(self.question_text)
                        if not answer:
                            print("❌ 无法生成回答，退出自动模式")
                            auto_continue = False
                            continue
                        print(f"🤖 Doubao 生成的回答: {answer}")

                if not auto_continue:
                    # 半交互模式：等待用户输入
                    print("\n提示：回车=AI回答 | 输入内容=手动回答 | continue [N]=全自动(可选断点) | quit=退出")
                    user_input = input("请输入你的回答: ").strip()

                    if user_input.lower() == "quit":
                        print("👋 用户主动退出")
                        break

                    if user_input.lower().startswith("continue"):
                        # 解析是否带断点参数: "continue" 或 "continue 10"
                        parts = user_input.split()
                        if len(parts) >= 2:
                            try:
                                current_breakpoint = int(parts[1])
                                if current_breakpoint <= round_num:
                                    print(f"⚠️  断点必须大于当前轮数（{round_num}），已忽略断点设置")
                                    current_breakpoint = 0
                                else:
                                    print(f"\n🚀 进入全自动模式，将在第 {current_breakpoint} 轮后暂停...")
                            except ValueError:
                                print(f"⚠️  无效的断点数字: {parts[1]}，将持续全自动运行")
                                current_breakpoint = 0
                        else:
                            current_breakpoint = 0
                            print("\n🚀 进入全自动模式，后续将由 AI 自动回答...")

                        auto_continue = True
                        # 本轮也自动回答
                        print(f"\n🤖 正在使用 Doubao 生成回答...")
                        answer = self.generate_answer_with_doubao(self.question_text)
                        if not answer:
                            print("❌ 无法生成回答，请手动输入")
                            auto_continue = False
                            continue
                        print(f"🤖 Doubao 生成的回答: {answer}")
                    elif user_input:
                        # 用户有输入，使用用户的回答
                        print(f"\n👤 使用用户回答: {user_input}")
                        answer = user_input
                    else:
                        # 用户直接回车，使用 Doubao 生成回答
                        print(f"\n🤖 正在使用 Doubao 生成回答...")
                        answer = self.generate_answer_with_doubao(self.question_text)
                        if not answer:
                            print("❌ 无法生成回答，请手动输入")
                            continue
                        print(f"🤖 Doubao 生成的回答: {answer}")

                # 保存当前轮对话到历史
                self.conversation_history.append({
                    "ai": self.question_text,
                    "student": answer
                })

                # 发送回答
                try:
                    result = self.chat(answer)
                except Exception as e:
                    print(f"\n⚠️  发送回答失败: {str(e)}")
                    break

                # 检查返回结果
                data = (result or {}).get("data") or {}
                if data.get("text") is None and data.get("nextStepId") is None:
                    print("\n✅ 工作流完成！")
                    break

                round_num += 1
                time.sleep(0.5)

            print("\n" + "=" * 60)
            print("🎉 工作流测试结束")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                self._finalize_workflow()
            except Exception:
                pass

    def run_with_doubao(self, task_id):
        """
        使用 Doubao 模型自动生成回答并运行工作流
        """
        if not self.doubao_client:
            print("\n❌ Doubao 客户端未初始化，请检查 ARK_API_KEY 环境变量")
            return

        if not self.student_profile_key:
            print("\n⚠️  未指定学生档位，默认使用'需要引导的学生'。")
            self.student_profile_key = "medium"

        try:
            # 启动工作流
            self.start_workflow(task_id)

            round_num = 1

            # 循环对话
            while True:
                # 检查是否还有下一步
                if self.current_step_id is None:
                    print("\n✅ 工作流完成！没有更多步骤了。")
                    break

                # 安全检查：防止无限循环
                if round_num > 50:
                    print(f"\n⚠️  警告：已达到最大对话轮数（{round_num}轮），自动退出防止无限循环")
                    break

                print("\n" + "="*60)
                mode = "日志回放" if self.use_replay_mode else "Doubao 自主回答"
                print(f"🤖 第 {round_num} 轮对话（{mode}）")
                print("="*60)

                # 使用回放模式或 Doubao 生成回答
                print(f"\n🔄 正在生成回答...")
                generated_answer = self.generate_answer_with_replay(self.question_text)

                if not generated_answer:
                    print("❌ 无法生成回答，跳过此轮")
                    break

                step_id = getattr(self, "current_step_id", None)
                source = "日志" if self.use_replay_mode and self.replay_engine and self.replay_engine.get_match_info(self.question_text, step_id=step_id).get("matched") else "Doubao"
                print(f"\n🤖 {source} 生成的回答: {generated_answer}")

                # 保存当前轮对话到历史
                self.conversation_history.append({
                    "ai": self.question_text,
                    "student": generated_answer
                })

                # 发送生成的回答
                try:
                    result = self.chat(generated_answer)
                except Exception as e:
                    print(f"\n⚠️  发送回答失败: {str(e)}")
                    break

                # 检查返回结果，如果 text 为 null 且 nextStepId 为 null，代表输出结束
                data = (result or {}).get("data") or {}
                if data.get("text") is None and data.get("nextStepId") is None:
                    print("\n✅ 工作流完成！")
                    break

                round_num += 1
                time.sleep(1)  # 稍微延迟，避免请求过快

            print("\n" + "="*60)
            print("🎉 工作流测试结束")
            print("="*60)

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure JSON logs are written even if the last round errors out.
            try:
                self._finalize_workflow()
            except Exception:
                pass


# 主程序
if __name__ == "__main__":
    print("="*60)
    print("📋 对话工作流自动化测试工具 v2.0")
    print("="*60)
    
    # 创建测试器
    tester = WorkflowTester()
    
    # 测试连接
    if not tester.test_connection():
        print("\n❌ 连接测试失败，请先解决问题")
        exit(1)
    
    # 获取 task_id
    task_id = os.getenv("TASK_ID")
    if not task_id:
        task_id = input("\n请输入 task_id: ").strip()
        if not task_id:
            print("❌ task_id 不能为空")
            exit(1)
    
    print(f"\n使用 task_id: {task_id}")

    # 选择日志格式
    tester.log_format = tester._get_log_format_preference()
    
    # 选择运行模式
    print("\n请选择运行方式：")
    print("1. 半交互式运行（推荐）- 回车自动回答，输入内容则手动回答")
    print("2. 自动化运行（需要预设答案）")
    print("3. 大模型自主选择回答（Doubao 自动生成答案）")
    print("4. 回放模式（支持 TXT 日志 difflib / JSON 日志 embedding）")

    choice = input("\n请输入选项 (1/2/3/4): ").strip()

    if choice == "1":
        print("\n🎯 半交互模式")
        print("=" * 60)
        print("说明：")
        print("- 直接回车：让 Doubao 模型自动生成回答（默认优秀学生）")
        print("- 输入内容：使用你输入的内容作为回答")
        print("- 输入 continue：后续全部由 AI 自动回答")
        print("- 输入 continue N：自动运行到第 N 轮后暂停，恢复半交互")
        print("- 输入 quit：退出程序")
        print("=" * 60)

        # 可选：让用户选择学生档位
        print("\n是否选择学生档位？（直接回车使用默认'优秀学生'）")
        select_profile = input("选择档位？(y/n，默认 n): ").strip().lower()
        if select_profile == "y":
            tester.prompt_student_profile()

        # 可选：设置初始断点
        print("\n是否预设断点？（在第 N 轮自动暂停，直接回车不设断点）")
        bp_input = input("断点轮数 (直接回车跳过): ").strip()
        breakpoint_round = 0
        if bp_input:
            try:
                breakpoint_round = int(bp_input)
                if breakpoint_round > 0:
                    print(f"✅ 已设置断点：第 {breakpoint_round} 轮后暂停")
                else:
                    breakpoint_round = 0
            except ValueError:
                print("⚠️  无效数字，不设置断点")

        tester.run_semi_interactive(task_id, breakpoint_round=breakpoint_round)

    elif choice == "2":
        print("\n提示: 请先在代码中配置 user_answers 列表")
        user_answers = [
            "这是第一个答案",
            "这是第二个答案",
            "这是第三个答案"
        ]
        tester.run_auto(task_id, user_answers)

    elif choice == "3":
        print("\n🤖 使用 Doubao 模型自主回答模式")
        tester.prompt_student_profile()

        print("\n可选: 是否提供学生档位模拟对话 Markdown？")
        use_dialogue_md = input("是否加载模拟对话？(y/n，默认 n): ").strip().lower()
        if use_dialogue_md == "y":
            dialogue_path = input("\n请输入 Markdown 文件的绝对路径: ").strip()
            if dialogue_path:
                tester.load_student_dialogues(dialogue_path)
            else:
                print("⚠️  未提供路径，跳过加载模拟对话")

        print("\n可选: 是否使用外接知识库？")
        use_kb = input("是否使用知识库？(y/n，默认 n): ").strip().lower()
        if use_kb == "y":
            kb_path = input("\n请输入知识库 Markdown 文件的绝对路径: ").strip()
            if kb_path:
                if not tester.load_knowledge_base(kb_path):
                    print("⚠️  知识库加载失败，将以通用模式运行")
            else:
                print("⚠️  未提供知识库路径，跳过加载")

        print("\n开始工作流...")
        tester.run_with_doubao(task_id)

    elif choice == "4":
        print("\n🎯 日志回放模式")
        print("="*60)
        print("说明：")
        print("1. 第一次运行生成对话日志或导出对话 JSON")
        print("2. 手动修改其中的用户回答（如需要）")
        print("3. 再次运行时，程序会根据AI提问找到最匹配的历史提问")
        print("   并强制使用对应的用户回答")
        print("4. 找不到匹配时，才让模型自己生成回答")
        print("="*60)

        # 输入日志文件路径
        log_path = input("\n请输入对话日志文件路径 (*_dialogue.txt 或 *_dialogue.json): ").strip()
        if not log_path:
            print("❌ 日志文件路径不能为空")
            exit(1)

        # 检查文件是否存在
        if not os.path.exists(log_path):
            print(f"❌ 日志文件不存在: {log_path}")
            exit(1)

        # 配置相似度阈值
        default_threshold = 0.8 if log_path.lower().endswith(".json") else 0.7
        threshold_input = input(f"\n请输入相似度阈值 (0.0-1.0，默认 {default_threshold}): ").strip()
        similarity_threshold = default_threshold
        if threshold_input:
            try:
                similarity_threshold = float(threshold_input)
                if similarity_threshold < 0.0 or similarity_threshold > 1.0:
                    print(f"⚠️  阈值必须在0.0-1.0之间，使用默认值{default_threshold}")
                    similarity_threshold = default_threshold
            except ValueError:
                print(f"⚠️  无效的阈值，使用默认值{default_threshold}")

        # 选择学生档位
        tester.prompt_student_profile()

        # 启用回放模式
        tester.enable_replay_mode(log_path, similarity_threshold)

        print("\n可选: 是否提供学生档位模拟对话 Markdown？")
        use_dialogue_md = input("是否加载模拟对话？(y/n，默认 n): ").strip().lower()
        if use_dialogue_md == "y":
            dialogue_path = input("\n请输入 Markdown 文件的绝对路径: ").strip()
            if dialogue_path:
                tester.load_student_dialogues(dialogue_path)
            else:
                print("⚠️  未提供路径，跳过加载模拟对话")

        print("\n可选: 是否使用外接知识库？")
        use_kb = input("是否使用知识库？(y/n，默认 n): ").strip().lower()
        if use_kb == "y":
            kb_path = input("\n请输入知识库 Markdown 文件的绝对路径: ").strip()
            if kb_path:
                if not tester.load_knowledge_base(kb_path):
                    print("⚠️  知识库加载失败，将以通用模式运行")
            else:
                print("⚠️  未提供知识库路径，跳过加载")

        print("\n开始工作流...")
        tester.run_with_doubao(task_id)

    else:
        print("❌ 无效选项")
