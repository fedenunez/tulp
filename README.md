# TULP: TULP Understands Language Promptly (v2.10.0)

TULP is a command-line tool inspired by POSIX utilities, designed to help you **process**, **filter**, and **create** data using AI. It interfaces with various AI APIs (OpenAI, Anthropic, Google Gemini, Groq, Ollama) allowing you to leverage powerful language models directly from your shell.

Pipe standard input content to TULP, provide instructions in natural language, and receive the processed output on standard output, just like familiar tools (`sed`, `awk`, `grep`, `jq`).

[![Watch the TULP demo video](https://markdown-videos.deta.dev/youtube/mHAvlRXXp6I)](https://www.youtube.com/watch?v=mHAvlRXXp6I)

## Installation

```bash
pip install tulp
```

To upgrade:
```bash
pip install --upgrade tulp
```

**Note:** TULP installs SDKs for all supported providers (`openai`, `google-genai`, `anthropic`, `groq`, `ollama`). If you see dependency errors, upgrade pip first: `pip install --upgrade pip`.

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

**Model Selection:** By default, TULP uses `gpt-5-mini`. You can switch providers with the `--model` flag; OpenAI GPT-o, Codex, Anthropic Claude, Groq LLaMA, Gemini, and Ollama models all work with a single command. Choose a higher-tier model when you need more context or accuracy:
```bash
cat complex_data.json | tulp --model claude-3-opus-20240229 "Analyze this data structure and identify anomalies"
```

### Options

```
$ tulp -h
TULP v2.10.0 - Process, filter, and create data using AI models.

usage: tulp [-h] [-V] [-x] [-w FILE] [-m MODEL] [-t LEVEL] [--max-chars N]
            [--cont N] [--inspect-dir DIR] [-v | -q] [--groq-api-key KEY]
            [--ollama-host KEY] [--anthropic-api-key KEY] [--openai-api-key KEY]
            [--openai-baseurl KEY] [--gemini-api-key KEY] [REQUEST ...]

options:
  -h, --help             show this help message and exit
  -V, --version          show program's version number and exit
  -x, --execute          Generate and execute Python code (Code Interpreter mode)
  -w, --write FILE       Write output to FILE (creates backups if exists)
  -m, --model MODEL      AI model to use (default: gpt-5-mini)
  -t, --thinking-level   Reasoning effort: low, medium, high (default: low)
  --max-chars N          Max chars per chunk for large inputs (default: 1000000)
  --cont N               Auto-continue N times if response incomplete
  --inspect-dir DIR      Save request/response JSON to DIR for debugging
  -v, --verbose          Verbose output (DEBUG level)
  -q, --quiet            Quiet output (ERROR level only)

API Keys (also settable via env vars or ~/.tulp.conf):
  --openai-api-key       OpenAI API Key [env: TULP_OPENAI_API_KEY]
  --anthropic-api-key    Anthropic API key [env: TULP_ANTHROPIC_API_KEY]
  --gemini-api-key       Google Gemini API Key [env: TULP_GEMINI_API_KEY]
  --groq-api-key         Groq Cloud API Key [env: TULP_GROQ_API_KEY]
  --ollama-host          Ollama host URL [env: TULP_OLLAMA_HOST]

Supported Models:
  OpenAI      gpt-*, chatgpt-*, o1-*, o3-*, codex-*    Requires OPENAI_API_KEY
  Anthropic   claude-*                                  Requires ANTHROPIC_API_KEY
  Google      gemini-*                                  Requires GEMINI_API_KEY
  Groq        groq.<model-id>                           Requires GROQ_API_KEY
  Ollama      ollama.<model-name>                       Requires Ollama running

Examples: gpt-4o, gpt-5-mini, o3-mini, claude-3-opus, gemini-2.5-flash
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
MODEL = gpt-5-mini

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
GEMINI_API_KEY = your_gemini_key_here_or_leave_blank

# --- Provider Specific ---
# OLLAMA_HOST = http://127.0.0.1:11434
# OPENAI_BASEURL = https://api.openai.com/v1 # Or override for compatible APIs
```

**Environment Variables:**
Prefix configuration keys with `TULP_`. For example:
```bash
export TULP_MODEL="claude-3-sonnet-20240229"
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
# Use Groq's Llama 3 70b via prefix
cat input.txt | tulp --model groq.llama3-70b-8192 "Rewrite this text in a more formal style"

# Use a local Ollama model (ensure Ollama service is running)
cat code. R | tulp --model ollama.codellama "Explain this R code"

# Use Anthropic's Claude 3 Sonnet
tulp --model claude-3-sonnet-20240229 "Compare the philosophies of Kant and Hegel"
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
