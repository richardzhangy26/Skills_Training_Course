# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated training workflow testing system for AI-powered education platforms. It simulates student-AI dialogues to test "能力训练" (ability training) tasks by generating student responses using LLMs (Doubao/DeepSeek) and optionally replaying/modifying previous dialogue logs.

**Core Purpose**: Automate testing of conversational training workflows by simulating different student profiles (excellent/average/struggling students) interacting with AI tutors.

## Key Commands

### Running Workflow Tests

```bash
# Main script with 3 student profiles and dialogue replay
python auto_script_train.py

# Extended version with 5 student personalities and multi-role concurrency
python auto_script_train_5characters.py

# WebSocket-based audio training platform tester
python auto_audio_train.py
```

### Skill Training Build (Markdown → Platform)

```bash
# Interactive mode (recommended)
cd skill_training_build
python create_task_from_markdown.py

# With parameters
python create_task_from_markdown.py <markdown_file_path> <task_id>
```

Creates script nodes and flow logic from Markdown training scripts:
- Parses stage data (prompts, opening lines, model configs)
- Auto-creates nodes via API
- Auto-connects Start → Step 1 → Step 2 → ... → End
- See `skill_training_build/README.md` for Markdown format

### Homework Review

```bash
cd homework_review
python homework_reviewer.py
```

Uploads homework files and submits them for AI review.

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys and credentials
```

### Running Claude Skills

The `.claude/skills/` directory contains automated skills that generate training configurations from task documents. These are invoked automatically by Claude Code when you reference task documents with the `@` symbol.

## Architecture

### Core Scripts

**`auto_script_train.py`** - Main workflow tester with 3 student profiles
- Supports 4 modes: interactive, automated (preset answers), Doubao auto-generation, replay mode
- **Semi-interactive mode** (Mode 1): User can input answers OR press Enter for AI auto-generation OR type `continue [N]` to auto-run until round N
- **Breakpoint feature**: Set breakpoints to pause auto-mode at specific rounds
- Student profiles: `good`, `medium`, `bad`
- Uses `WorkflowTesterBase` for shared logic

**`auto_script_train_5characters.py`** - Extended version with 5 personalities
- Student profiles: S1 (silent), S2 (cooperative), S3 (perfectionist), S4 (disruptive), S5 (creative)
- Supports concurrent multi-role execution for stress testing
- Configurable LLM backends: Doubao SDK, Doubao POST API, DeepSeek SDK

**`auto_audio_train.py`** - WebSocket-based audio training tester
- Real-time audio streaming via WebSocket (`wss://cloudapi.polymas.com/ai-tools/ws/v2/trainFlow`)
- TTS integration: edge-tts converts text → MP3 → PCM audio frames
- Supports semi-interactive and manual modes
- Three student profiles: excellent, needs guidance, off-topic
- Logs conversations to `./audio_logs/`
- **Important**: Default English voice (`en-US-GuyNeural`) doesn't support Chinese text. Change to `zh-CN-XiaoxiaoNeural` (line 252) for Chinese TTS.

**`workflow_tester_base.py`** - Base class providing:
- API interface to training platform (`queryScriptStepList`, `runCard`, `chat`)
- Logging infrastructure (TXT and/or JSON formats)
- Student profile management
- Retry mechanisms for network requests
- JSON dialogue export for replay with embeddings

### Dialogue Replay System

The system supports two replay modes for reusing/modifying previous test runs:

1. **TXT Log + Difflib** (`DialogueReplayEngine`):
   - Parses `*_dialogue.txt` logs
   - Uses string similarity matching (difflib) to find matching questions
   - Threshold: 0.7 (configurable)

2. **JSON Log + Embeddings** (`JsonDialogueReplayEngine`):
   - Parses `*_dialogue.json` exports
   - Uses OpenAI-compatible embeddings for semantic matching
   - Threshold: 0.8 (configurable)
   - Generates `*_replay_index.json` cache for faster reloading
   - Requires `EMBEDDING_API_KEY` environment variable

### LLM Integration

**Model Selection** (controlled by `MODEL_TYPE` env var):
- `doubao_sdk`: Uses OpenAI SDK with Volc Engine ARK API
- `doubao_post`: Uses custom POST endpoint (company internal)
- `deepseek_sdk`: Uses OpenAI SDK with DeepSeek API

**Answer Generation** (`generate_answer_with_doubao`):
- Constructs prompts with: student profile, dialogue history, knowledge base (optional), sample dialogues (optional)
- Enforces 50-character limit and detects confirmation/choice questions for concise responses
- Falls back to model generation when replay mode fails to find matches

### Logging System

Logs are organized hierarchically:
```
log/
└── [context_path_parts]/
    └── [profile_key]/
        ├── task_[ID]_[timestamp]_runcard.txt    # API requests/responses
        ├── task_[ID]_[timestamp]_dialogue.txt   # AI-student conversations
        └── task_[ID]_[timestamp]_dialogue.json  # JSON export for replay
```

**Log Formats**:
- `txt`: Human-readable conversation logs
- `json`: Machine-readable with metadata for replay/analysis
- `both`: Generate both formats

Context path is derived from `log_context_path` (usually the task document path).

### Claude Skills (`.claude/skills/`)

Automated generators for training configuration:

1. **training-config-setup**: Extracts task name/description, generates 16:9 cover images using Doubao
2. **training-rubric-generator**: Creates detailed grading rubrics with scoring criteria, examples, and LLM evaluation guidelines
3. **training-script-generator**: Generates complete training script configurations in Markdown format with LangGPT-structured prompts
4. **training-dialogue-simulator**: Simulates complete dialogue flows for testing validation

Skills use `doubao_skill_runner.py` to interface with Doubao APIs for content generation.

## Configuration

### Required Environment Variables

```bash
# Platform Authentication (get from browser DevTools Network tab)
AUTHORIZATION=eyJ0eXAiOiJKV1Q...  # JWT token from cloudapi.polymas.com
COOKIE=hike-polymas-identity=1;...  # Full cookie string
TASK_ID=87dB0BZBXZHJ0oEjkDZ2  # Training task ID from URL

# LLM Configuration (choose one)
MODEL_TYPE=doubao_sdk  # or doubao_post, deepseek_sdk

# Doubao SDK Mode
ARK_API_KEY=ak-xxx
DOUBAO_MODEL=doubao-seed-1-6-251015

# Doubao POST Mode (company internal)
LLM_API_KEY=sk-xxx
LLM_MODEL=Doubao-1.5-pro-32k
LLM_API_URL=http://llm-service.polymas.com/api/openai/v1/chat/completions
LLM_SERVICE_CODE=SI_Ability

# DeepSeek Mode
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_MODEL=deepseek-chat

# Replay Mode (optional)
EMBEDDING_API_KEY=sk-xxx  # For JSON replay with embeddings
EMBEDDING_MODEL=text-embedding-3-small
```

### Optional Configuration

```bash
LOG_FORMAT=both  # txt, json, or both
CUSTOM_HEADERS='{"X-Custom": "value"}'  # Additional HTTP headers
```

## Student Profiles

Profiles define how the AI simulates different student behaviors:

**3-Profile System** (`auto_script_train.py`):
- `good`: Excellent student - thorough understanding, structured answers
- `medium`: Needs guidance - basic understanding but seeks confirmation
- `bad`: Off-topic - misunderstands or gives irrelevant answers

**5-Profile System** (`auto_script_train_5characters.py`):
- `S1`: Silent and passive
- `S2`: Cooperative learner
- `S3`: Perfectionist
- `S4`: Disruptive challenger
- `S5`: Creative thinker

Profiles can be customized by creating `student_profiles.custom.json` (see `student_profiles.example.json`).

## Common Workflows

### Testing a Training Task

1. Get `TASK_ID` from the platform URL
2. Configure `.env` with credentials
3. Run script and select mode:
   - Mode 1: Semi-interactive (Enter for AI, type for manual, `continue [N]` for auto with optional breakpoint)
   - Mode 3: Fully automated with Doubao
   - Mode 4: Replay from previous logs with modifications

### Generating Training Configurations

Reference a task document with `@` in Claude Code:
```
@skills_training_course/化工原理-武夷学院/实训任务文档1.md
生成基础配置、评价标准、训练剧本和对话流程
```

Skills automatically create a folder named after the task document containing:
- `基础配置.json`
- `评价标准.json` + `评价标准.md`
- `训练剧本配置.md`
- `对话流程模拟.md`

### Replay Mode Workflow

1. Run a test session (Mode 1 or 3) - generates dialogue logs
2. Manually edit `*_dialogue.txt` or `*_dialogue.json` to refine student answers
3. Re-run with Mode 4, providing the edited log file path
4. System will reuse answers from log for matching questions, falling back to LLM generation for new questions

### Multi-Role Stress Testing

Use `auto_script_train_5characters.py` Mode 3 → "同时运行多个学生角色":
- Input: `1,3,5` to run S1, S3, S5 concurrently
- Each role runs independently with separate logs
- Useful for testing system stability under load

## Important Implementation Details

### API Request Flow

1. `query_script_step_list(task_id)` → Get step list and first `stepId`
2. `run_card(task_id, step_id)` → Initialize step, get AI's opening question
3. Loop: `chat(user_answer)` → Send answer, get next question or next step
4. If `needSkipStep=true`, automatically call `run_card` for next step

### Retry Mechanism

`_retry_request()` in `auto_script_train.py` handles timeouts:
- Max 3 retries with exponential backoff (2^attempt seconds)
- Timeout increases: 60s → 120s → 180s
- Other network errors (non-timeout) fail immediately without retry

### Semi-Interactive Mode Features

- **Empty input (Enter)**: AI generates one response for current round
- **Text input**: Uses your input as the student answer
- **`continue`**: Switches to full auto-mode until workflow ends
- **`continue N`**: Auto-mode with breakpoint at round N, then pauses back to semi-interactive
- **`quit`**: Exit immediately

Breakpoints can be set at launch or dynamically during execution.

### Dialogue Matching Logic

**TXT mode**: Uses `difflib.SequenceMatcher` to compare normalized questions (strips whitespace)

**JSON mode**:
- Normalizes questions by extracting last sentence ending with `?` or `？`
- Generates embeddings using `text-embedding-3-small` (or configured model)
- Uses cosine similarity for matching
- Caches embeddings in `*_replay_index.json` to avoid recomputation

Both modes support `step_id` filtering to prioritize matches within the same workflow step.

## File Organization

```
能力训练/
├── auto_script_train.py              # Main 3-profile tester
├── auto_script_train_5characters.py  # 5-profile multi-role tester
├── workflow_tester_base.py           # Shared base class
├── .env                              # Configuration (not in git)
├── requirements.txt                  # Python dependencies
├── .claude/
│   └── skills/                       # Claude Code automated skills
│       ├── training-config-setup/
│       ├── training-rubric-generator/
│       ├── training-script-generator/
│       └── training-dialogue-simulator/
├── log/                              # Generated test logs (gitignored)
│   └── [context]/[profile]/
│       ├── *_runcard.txt
│       ├── *_dialogue.txt
│       └── *_dialogue.json
└── skills_training_course/           # Training task documents
    └── [学校-课程]/
        ├── 实训任务文档.md
        └── [任务名称]/                # Generated by skills
            ├── 基础配置.json
            ├── 评价标准.json/md
            ├── 训练剧本配置.md
            └── 对话流程模拟.md
```

## Troubleshooting

**401/403 errors**: `AUTHORIZATION` or `COOKIE` expired - re-capture from browser DevTools

**Doubao/DeepSeek failures**: Verify API keys and network access to respective endpoints

**Replay mode not matching**: Check similarity threshold (default 0.7 for TXT, 0.8 for JSON) - lower if needed

**Skills not generating files**: Ensure `ARK_API_KEY` is set (required for Doubao image generation)

**Logs missing**: Check write permissions in project directory - logs are created in `./log/`
