# TULP: TULP Understands Language Promptly (v2.11.0)

TULP is a command-line tool inspired by POSIX utilities, designed to help you **process**, **filter**, and **create** data using AI. It interfaces with various AI APIs (OpenAI, Anthropic, DeepSeek, Z.ai, Google Gemini, Groq, Ollama) allowing you to leverage powerful language models directly from your shell.

Pipe standard input content to TULP, provide instructions in natural language, and receive the processed output on standard output, just like familiar tools (`sed`, `awk`, `grep`, `jq`).

[![Watch the TULP demo video](https://markdown-videos.deta.dev/youtube/mHAvlRXXp6I)](https://www.youtube.com/watch?v=mHAvlRXXp6I)

## Installation

Requires Python 3.10 or newer.

```bash
pip install tulp
```

To upgrade:
```bash
pip install --upgrade tulp
```

**Note:** TULP installs SDKs for all supported providers (`openai`, `google-genai`, `anthropic`, `groq`, `ollama`; DeepSeek and Z.ai use the `openai` SDK). If you see dependency errors, upgrade pip first: `pip install --upgrade pip`.

## Usage

TULP operates in several modes:

1.  **Direct Request Mode:** Ask a question or give a command without piping data.
    ```bash
    tulp "What is the capital of France?"
    tulp "Write a python function to calculate factorial"
    ```
    If no request is given, TULP will prompt interactively.

2.  **Stdin Processing Mode:** Pipe data into TULP and provide instructions on how to process it.
    ```bash
    cat data.csv | tulp "Extract the email addresses from the second column"
    cat report.txt | tulp "Summarize this text in three bullet points"
    cat code.py | tulp "Explain what this Python code does"
    ```

3.  **Code Interpretation Mode (`-x`):** TULP attempts to **generate, debug, and execute** a Python program to fulfill the request based on the input data or instructions.
    ```bash
    tulp -x "Generate a list of 10 random names"
    cat sales_data.csv | tulp -x "Calculate the total sales from the 'Amount' column"
    ```

**Output Handling:**
*   The primary processed output (what the AI generates in response to the request) is written to **standard output** (`stdout`).
*   Informational messages, logs, errors, and LLM explanations (from the `<|||stderr|||>` block) are written to **standard error** (`stderr`).
*   This separation allows safe piping: `cat data | tulp "process..." | another_command`.

**Large Inputs:** If standard input exceeds the `max_chars` limit (default 1,000,000, configurable), TULP automatically splits the input into chunks and processes them sequentially. Be aware that tasks requiring global context (like summarizing a whole book) may perform poorly when chunked. Line-based processing or tasks with local context generally work well. Adjust `--max-chars` or choose models with larger context windows if needed.

**Model Selection:** By default, TULP uses `gpt-6-luna`. You can switch providers with the `--model` flag; OpenAI GPT and Codex, Anthropic Claude, Google Gemini, DeepSeek, Z.ai GLM, Groq, and Ollama models all work with a single command. Choose a higher-tier model when you need more context or accuracy:
```bash
cat complex_data.json | tulp --model claude-opus-5-5 "Analyze this data structure and identify anomalies"
```

### Options

```
$ tulp -h
usage: tulp [-h] [-V] [-x] [-w FILE] [-m MODEL] [-t LEVEL] [--max-chars N]
            [--cont N] [--list-models [PROVIDER]] [--inspect-dir DIR] [-v |
            -q] [--gemini-api-key KEY] [--openai-api-key KEY]
            [--openai-baseurl KEY] [--anthropic-api-key KEY]
            [--deepseek-api-key KEY] [--deepseek-baseurl KEY]
            [--zai-api-key KEY] [--zai-baseurl KEY] [--groq-api-key KEY]
            [--ollama-host KEY]
            ...

TULP v2.11.0 - Process, filter, and create data using AI models.

positional arguments:
  REQUEST               Instructions in natural language (reads stdin if
                        piped)

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -x, --execute         Generate and execute Python code (Code Interpreter
                        mode)
  -w, --write FILE      Write output to FILE (creates backups if exists)
  -m, --model MODEL     AI model to use (default: gpt-6-luna)
  -t, --thinking-level LEVEL
                        Reasoning effort: low, medium, high (default: low)
  --max-chars N         Max chars per chunk for large inputs (default:
                        1000000)
  --cont N              Auto-continue N times if response incomplete
  --list-models [PROVIDER]
                        List the models each configured provider currently
                        offers and exit; optionally only PROVIDER (openai,
                        anthropic, gemini, deepseek, zai, groq, ollama)
  --inspect-dir DIR     Save request/response JSON to DIR for debugging
  -v, --verbose         Verbose output (DEBUG level)
  -q, --quiet           Quiet output (ERROR level only)

API Keys (also settable via env vars or ~/.tulp.conf):
  --gemini-api-key KEY  Google AI (Gemini) API Key [env: TULP_GEMINI_API_KEY]
  --openai-api-key KEY  OpenAI (or compatible) API Key [env:
                        TULP_OPENAI_API_KEY]
  --openai-baseurl KEY  Override OpenAI API base URL (e.g., for local models
                        like Ollama: http://localhost:11434/v1) [env:
                        TULP_OPENAI_BASEURL]
  --anthropic-api-key KEY
                        Anthropic API key [env: TULP_ANTHROPIC_API_KEY]
  --deepseek-api-key KEY
                        DeepSeek API key [env: TULP_DEEPSEEK_API_KEY]
  --deepseek-baseurl KEY
                        Override DeepSeek API base URL (default:
                        https://api.deepseek.com) [env: TULP_DEEPSEEK_BASEURL]
  --zai-api-key KEY     Z.ai API key [env: TULP_ZAI_API_KEY]
  --zai-baseurl KEY     Override Z.ai API base URL (default:
                        https://api.z.ai/api/paas/v4/; GLM Coding Plan:
                        https://api.z.ai/api/coding/paas/v4) [env:
                        TULP_ZAI_BASEURL]
  --groq-api-key KEY    Groq Cloud API Key [env: TULP_GROQ_API_KEY]
  --ollama-host KEY     Ollama host URL (default: http://127.0.0.1:11434)
                        [env: TULP_OLLAMA_HOST]

Supported Models:
  OpenAI      gpt-*, codex-*, o1-*, o3-*, openai.<id>    OPENAI_API_KEY
              e.g. gpt-6-luna, gpt-6.1-sol, gpt-6-astra
  Anthropic   claude-*                                   ANTHROPIC_API_KEY
              e.g. claude-opus-5-5, claude-sonnet-5-5, claude-haiku-5-5
  Google      gemini-*                                   GEMINI_API_KEY
              e.g. gemini-4-argon, gemini-3.8-flash, gemini-3.5-flash-lite
  DeepSeek    deepseek-*                                 DEEPSEEK_API_KEY
              e.g. deepseek-v4-pro, deepseek-flash
  Z.ai        glm-*, zai.<id>                            ZAI_API_KEY
              e.g. glm-5.3, glm-4.7
  Groq        groq.<id>                                  GROQ_API_KEY
              e.g. groq.openai/gpt-oss-120b, groq.llama-3.3-70b-versatile
  Ollama      ollama.<name>                              Ollama running
              e.g. ollama.gpt-oss, ollama.qwen3 (any pulled model)

Thinking (-t low|medium|high) sets each provider's reasoning effort (Z.ai only
turns thinking on). Requires Python 3.10+.
```

## Configuration

TULP can be configured via a file (`~/.tulp.conf`), environment variables, or command-line arguments. The precedence order is: **Command-line Arguments > Environment Variables > Configuration File > Defaults**.

**Configuration File (`~/.tulp.conf`):**
Uses INI format. All settings should be under the `[DEFAULT]` section.

```ini
[DEFAULT]
# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = INFO

# Default model if --model is not specified
MODEL = gpt-6-luna

# Max characters per chunk for large stdin
MAX_CHARS = 1000000

# Default number of continuation attempts if response seems incomplete
CONT = 0

# Default file to write output to (if -w is used without a value - usually not recommended)
# WRITE_FILE = output.txt

# Default mode for code execution (usually False)
# EXECUTE_CODE = False

# Default directory for saving LLM interactions
# INSPECT_DIR = /path/to/tulp_inspect_logs

# --- API Keys ---
# Set API keys here or preferably via environment variables
OPENAI_API_KEY = your_openai_key_here_or_leave_blank
GROQ_API_KEY = your_groq_key_here_or_leave_blank
ANTHROPIC_API_KEY = your_anthropic_key_here_or_leave_blank
DEEPSEEK_API_KEY = your_deepseek_key_here_or_leave_blank
ZAI_API_KEY = your_zai_key_here_or_leave_blank
GEMINI_API_KEY = your_gemini_key_here_or_leave_blank

# --- Provider Specific ---
# OLLAMA_HOST = http://127.0.0.1:11434
# OPENAI_BASEURL = https://api.openai.com/v1 # Or override for compatible APIs
# ZAI_BASEURL = https://api.z.ai/api/coding/paas/v4 # GLM Coding Plan endpoint
```

**Environment Variables:**
Prefix configuration keys with `TULP_`. For example:
```bash
export TULP_MODEL="claude-sonnet-5-5"
export TULP_OPENAI_API_KEY="sk-..."
export TULP_LOG_LEVEL="DEBUG"
tulp "My request"
```

## Examples

TULP's usage is versatile. Here are some examples:

### Simple Questions & Generation

```bash
# Ask a question
tulp "What are the main advantages of using Python?"

# Generate code
tulp "Write a bash script to find all *.log files older than 7 days in /var/log"

# Generate code and save to file
tulp "Create a simple Flask web server that returns 'Hello, World!'" -w app.py
```

### Processing Piped Data

```bash
# Basic text processing (like sed)
echo "Hello world, this is a test." | tulp "Replace 'world' with 'Tulp'"

# Data extraction (like grep/awk)
cat access.log | tulp "Extract all IP addresses that made POST requests"

# Format conversion (like jq)
cat data.json | tulp "Convert this JSON array to a CSV file with headers 'ID' and 'Name'"

# Summarization
cat article.txt | tulp "Summarize this article in one paragraph"

# Translation
cat message.txt | tulp --model gemini-1.5-pro-latest "Translate this text to French"
```

### Code Interpretation (`-x`)

```bash
# Ask a question requiring calculation
tulp -x "What is the square root of 15?"

# Analyze data from a file
cat data.csv | tulp -x "Calculate the average value of the 'Score' column"

# Perform file operations (Use with caution!)
tulp -x "Create a directory named 'output' and move all *.txt files from the current directory into it"
```
**Warning:** The `-x` mode executes generated Python code. Review the generated code (especially if using `-w`) or understand the potential risks before running it on sensitive systems or data.

### Using Different Models

```bash
# See which models your configured providers offer right now (names usable with -m)
tulp --list-models
tulp --list-models anthropic
```

```bash
# Use OpenAI's gpt-oss 120b on Groq via prefix
cat input.txt | tulp --model groq.openai/gpt-oss-120b "Rewrite this text in a more formal style"

# Use a local Ollama model (ensure Ollama service is running)
cat code.R | tulp --model ollama.gpt-oss "Explain this R code"

# Use Anthropic's Claude Opus 5.5 with more reasoning effort
tulp --model claude-opus-5-5 -t high "Compare the philosophies of Kant and Hegel"

# Use DeepSeek or Z.ai GLM
cat notes.txt | tulp --model deepseek-flash "Summarize these notes as bullet points"
cat app.py | tulp --model glm-5.3 "Add type hints to this code"
```

### Working with FMLPack

[`fmlpack`](https://github.com/fedenunez/fmlpack) packages entire folders into FML (Filesystem Markup Language), making it easy to share projects with an LLM and unpack the response.

```bash
# Send the current project snapshot to TULP for review
fmlpack -c . | tulp "Review this code and point out bugs:"

# Generate new files with TULP, then materialize them locally
tulp "Create a README and src/app.py for a TODO manager, respond in FML format." > out.fml
fmlpack -x -f out.fml -C ./todo-app
```

### Debugging with `--inspect-dir`

```bash
tulp --inspect-dir ./tulp_logs "Explain the concept of recursion" -v
```
This will create a timestamped subdirectory inside `./tulp_logs` containing JSON files for each request/response interaction with the LLM, useful for debugging prompts and responses.

## Origin of the Name

TULP stands for "TULP Understands Language Promptly". It's a recursive acronym, reflecting the tool's nature of using language models to process language.

## Changelog (Summary)

### v2.11.0 | 2026-10-22
- **New providers:** DeepSeek (`deepseek-*`, `DEEPSEEK_API_KEY`) and Z.ai GLM (`glm-*` or `zai.<model-id>`, `ZAI_API_KEY`; set `ZAI_BASEURL` for the GLM Coding Plan endpoint). Both run with thinking enabled; DeepSeek maps `--thinking-level` to `reasoning_effort`, Z.ai has no effort control.
- **Anthropic:** Current Claude models (4.6+, 5.x, Fable) use adaptive thinking with `--thinking-level` as the effort level; older models keep `budget_tokens`. Requests are streamed, all text blocks are returned, and refusals are reported as errors.
- **OpenAI:** GPT-5/GPT-6 models use the Responses API with `--thinking-level` as reasoning effort (it was previously not sent there).
- **Gemini:** Thinking is enabled for every Gemini 2.5+ model, including Gemini 4.
- **Default model:** `gpt-6-luna` (OpenAI retires the `gpt-5-mini` snapshot on 2026-12-11).
- **`--list-models [PROVIDER]`:** Lists the models each configured provider currently offers (queried live, in parallel), as names ready for `-m`.
- **Faster startup:** Provider SDKs are imported only when their model is used (`tulp -h` went from ~4.6s to ~0.2s).
- **Dependency updates:** Supports the latest SDKs: `openai>=1.66,<4`, `anthropic>=0.80,<3`, `google-genai>=1.50,<3`, `groq>=0.13,<2`, `ollama>=0.5,<1`. Requires Python 3.10+ (the code already used `X | None` annotations).

### v2.10.0 | 2025-01-20
- **Gemini SDK migration:** Switched from deprecated `google-generativeai` to new `google-genai` SDK.
- **Thinking/reasoning support:** Added `-t, --thinking-level` option (`low`, `medium`, `high`) for models with extended reasoning (OpenAI o1/o3, Anthropic Claude, Gemini 2.5+/3.x).
- **Improved CLI:** Cleaner help output, added `-V/--version`, `-m` shortcut for model, `-t` for thinking level.
- **Dependency updates:** Requires `google-genai>=1.50.0`, `ollama>=0.4.0`.

### v2.8.0 | 2025
- **OpenAI models:** Added support for GPT-o and Codex responses, so the newest assistants work with a single `tulp` command.
- **Default model:** Switched to `gpt-5-mini` for stronger reasoning out of the box.

### v2.7.0 | 2025-07-04
- **CLI refresh:** Faster startup and clearer logging after a large internal cleanup.
- **Output format:** Responses now use `<|||tag|||>` markers for easier piping and parsing.
- **Compatibility:** Updated dependencies and kept support for Python 3.8+.

### v2.6.x | 2024
- Added `--inspect-dir` for debugging.
- Added Gemini support.
- Fixed various bugs and improved error handling.

### v2.0 - v2.5.x | 2024
- Added support for Groq, Ollama, Anthropic models.
- Changed default model over time (gpt-4-turbo, gpt-4o, gpt-5-mini).
- Added `--cont` option for automatic continuation.
- Improved large input handling and warnings.

### v1.x | 2023-2024
- Initial versions with OpenAI support.
- Added code interpretation (`-x`).
- Switched to newer OpenAI models and API versions.

*(For detailed history, see git log)*
