# SecLab Runtime Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide complete, non-secret runtime configuration templates and a fail-fast validator for the SecLab frontend and AI Agent service.

**Architecture:** Keep real credentials in ignored `.env` files. Add a focused Python validator that accepts a mapping for unit tests and a file path for command-line use, then make the deployment templates and documentation match every environment variable used by production code.

**Tech Stack:** Python 3, python-dotenv, unittest, Vue/Vite environment files, Markdown.

## Global Constraints

- Git stores variable names, safe defaults, and placeholders only.
- The validator never prints secret values.
- Existing API paths, database schema, and runtime ports remain unchanged.
- Missing required variables, placeholders, malformed ports, malformed booleans, and malformed JSON return a non-zero exit code.

---

### Task 1: AI Agent Runtime Configuration Validator

**Files:**
- Create: `seclab-backend/ai-agent-service/runtime_config_validator.py`
- Create: `seclab-backend/ai-agent-service/test_runtime_config_validator.py`

**Interfaces:**
- Produces: `validate_runtime_config(values: Mapping[str, str]) -> list[str]`
- Produces: `load_and_validate(path: Path) -> list[str]`
- Produces: `main(argv: Sequence[str] | None = None) -> int`

- [ ] **Step 1: Write failing validator tests**

Cover these exact behaviors:

```python
def test_complete_configuration_has_no_issues():
    assert validate_runtime_config(complete_values()) == []

def test_missing_or_placeholder_secrets_are_reported_by_name_only():
    issues = validate_runtime_config({"DIFY_API_KEY": "your_dify_api_key_here"})
    assert any("DIFY_API_KEY" in issue for issue in issues)
    assert all("your_dify_api_key_here" not in issue for issue in issues)

def test_invalid_port_boolean_and_flag_json_are_reported():
    values = complete_values()
    values.update({
        "SERVICE_PORT": "99999",
        "ENABLE_DIFY_KNOWLEDGE_RAG": "sometimes",
        "FLAG_ANSWERS_JSON": "[]",
    })
    issues = validate_runtime_config(values)
    assert any("SERVICE_PORT" in issue for issue in issues)
    assert any("ENABLE_DIFY_KNOWLEDGE_RAG" in issue for issue in issues)
    assert any("FLAG_ANSWERS_JSON" in issue for issue in issues)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m unittest test_runtime_config_validator.py
```

Expected: import failure because `runtime_config_validator.py` does not exist.

- [ ] **Step 3: Implement minimal validator**

Implement:

```python
REQUIRED_KEYS = (
    "DIFY_API_URL",
    "DIFY_API_KEY",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_DATABASE",
)

BOOLEAN_KEYS = (
    "ENABLE_FAKE_LLM_FOR_TEST",
    "ENABLE_DIFY_KNOWLEDGE_RAG",
    "STRICT_SOURCE_EXAMPLE_VALIDATION",
)

def validate_runtime_config(values: Mapping[str, str]) -> list[str]:
    issues: list[str] = []
    # Report missing/placeholder keys, numeric port bounds, boolean syntax,
    # and FLAG_ANSWERS_JSON object syntax without including any values.
    return issues
```

The CLI uses `dotenv_values(path)`, prints only `[OK]` or `[ERROR] <variable>: <reason>`, and exits `2` when issues exist.

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```powershell
python -m unittest test_runtime_config_validator.py
```

Expected: all validator tests pass.

### Task 2: Complete Templates and Deployment Instructions

**Files:**
- Modify: `seclab-backend/ai-agent-service/.env.example`
- Modify: `SecLab-FrontEnd-2/.env.example`
- Modify: `SecLab网络安全漏洞综合实验平台部署说明文档.md`
- Create: `seclab-backend/ai-agent-service/test_runtime_config_templates.py`

**Interfaces:**
- Consumes: environment keys read by `config.py`, `main.py`, `lab_repository.py`, and `single_question_generation_service.py`
- Produces: complete `.env.example` files and documented validation command

- [ ] **Step 1: Write failing template coverage tests**

```python
def test_ai_template_contains_all_runtime_keys():
    assert REQUIRED_AI_KEYS <= parse_env_keys(AI_TEMPLATE)

def test_frontend_template_contains_all_service_urls():
    assert {
        "VITE_API_BASE_URL",
        "VITE_EXPERIMENT_MODULE_BASE_URL",
        "VITE_IMAGE_SERVICE_BASE_URL",
        "VITE_DOCKER_API_URL",
        "VITE_AGENT_BASE_URL",
    } <= parse_env_keys(FRONTEND_TEMPLATE)

def test_deployment_document_runs_validator_before_start():
    assert "python runtime_config_validator.py .env" in DEPLOYMENT_DOC
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m unittest test_runtime_config_templates.py
```

Expected: failures for the missing frontend experiment-module URL, missing AI optional-mode keys, and missing validation command.

- [ ] **Step 3: Complete templates and documentation**

Add these AI Agent keys with safe defaults:

```dotenv
DIFY_RAG_MODE=local
ENABLE_DIFY_KNOWLEDGE_RAG=false
STRICT_SOURCE_EXAMPLE_VALIDATION=false
FLAG_ANSWERS_JSON={}
```

Add this frontend key:

```dotenv
VITE_EXPERIMENT_MODULE_BASE_URL=http://localhost:8084
```

Document:

```powershell
Copy-Item .env.example .env
python runtime_config_validator.py .env
python -m uvicorn main:app --host 0.0.0.0 --port 8010
```

- [ ] **Step 4: Run focused and full verification**

Run:

```powershell
python -m unittest test_runtime_config_validator.py test_runtime_config_templates.py
python -m unittest discover -p "test_*.py"
cd ../../../SecLab-FrontEnd-2
npm test
npm run build
```

Expected: all tests and the production build pass.

- [ ] **Step 5: Verify and publish**

Run:

```powershell
git diff --check
git status --short
git add seclab-backend/ai-agent-service/.env.example `
        seclab-backend/ai-agent-service/runtime_config_validator.py `
        seclab-backend/ai-agent-service/test_runtime_config_validator.py `
        seclab-backend/ai-agent-service/test_runtime_config_templates.py `
        SecLab-FrontEnd-2/.env.example `
        SecLab网络安全漏洞综合实验平台部署说明文档.md `
        docs/superpowers/plans/2026-07-25-runtime-configuration.md
git commit -m "chore: complete runtime configuration"
git push
```

Expected: `origin/fix/real-learning-loop-20260722` points to the new commit and the working tree is clean.
