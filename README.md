# TULP: TULP Understands Language Promptly (v2.7.0)

TULP is a command-line tool inspired by POSIX utilities, designed to help you **process**, **filter**, and **create** data in the realm of Artificial Intelligence. It interfaces with various AI APIs (OpenAI, Groq, Ollama, Anthropic, Gemini) allowing you to leverage powerful language models directly from your shell.

Pipe standard input content to TULP, provide instructions in natural language, and receive the processed output on standard output, just like familiar tools (`sed`, `awk`, `grep`, `jq`).

[![Watch the TULP demo video](https://markdown-videos.deta.dev/youtube/mHAvlRXXp6I)](https://www.youtube.com/watch?v=mHAvlRXXp6I)

## Installation

To install TULP using pip:
```bash
pip install tulp
```
To upgrade to the latest version:
```bash
pip install --upgrade tulp
```

**Note:** Depending on the AI providers you intend to use, ensure their respective libraries are installed. TULP requires `openai`, `google-generativeai`, `anthropic`, `groq`, and `ollama`. If you encounter issues during installation related to dependencies (like `google-generativeai`), try upgrading pip first: `pip install --upgrade pip`.

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

**Model Selection:** By default, TULP uses `gpt-4o`. You can specify a different model using the `--model` argument. TULP supports models from various providers (see Options below). For complex tasks or better results, explicitly selecting a powerful model is recommended:
```bash
cat complex_data.json | tulp --model claude-3-opus-20240229 "Analyze this data structure and identify anomalies"
```

### Options

```text
usage: tulp [-h] [-x] [-w FILE] [--model MODEL_NAME] [--max-chars NUM] [--cont N] [--inspect-dir DIR] [-v | -q] [--groq_api_key GROQ_API_KEY]
            [--ollama_host OLLAMA_HOST] [--anthropic_api_key ANTHROPIC_API_KEY] [--openai_api_key OPENAI_API_KEY] [--openai_baseurl OPENAI_BASEURL]
            [--gemini_api_key GEMINI_API_KEY]
            ...

TULP v2.7.0 - TULP Understands Language Promptly:
A command-line tool, in the best essence of POSIX tooling, that helps you to **process**, **filter**, and **create** data using AI models.

Tulp supports different backends and models, automatically selected based on the model name.
Currently supported model patterns:
   - (gpt-|chatgpt-|openai\.).* : Any OpenAI model (https://platform.openai.com/docs/models) or compatible API (e.g., local Ollama with base URL). Requires API key (openai_api_key). Use 'openai.<MODEL_ID>' for unlisted models.
   - groq\..* : Any Groq model id using the prefix 'groq.', requires GROQ_API_KEY. Check available models at https://console.groq.com/docs/models
   - ollama\..* : Any Ollama model prefixed with 'ollama.', requires Ollama service running (check --ollama_host).
   - claude-.* : Any Anthropic Claude model (https://docs.anthropic.com/claude/docs/models-overview), requires ANTHROPIC_API_KEY
   - gemini.* : Any Google Gemini model (https://ai.google.dev/gemini-api/docs/models/gemini), requires GEMINI_API_KEY


positional arguments:
  request               User's request or processing instructions in natural language. Reads from stdin if processing piped data.

options:
  -h, --help            show this help message and exit
  -x, --execute         Allow Tulp to generate and execute Python code to fulfill the request (Code Interpreter mode).
  -w FILE, --write FILE
                        Write the main output (<|||stdout|||>) to FILE. Creates backups (.backup-N) if FILE exists.
  --model MODEL_NAME    Select the AI model to use (e.g., gpt-4o, claude-3-opus-20240229, groq.llama3-70b-8192). (Config/Env: TULP_MODEL, default: gpt-4o)
  --max-chars NUM       Max characters per LLM request chunk when processing large stdin. (Config/Env: TULP_MAX_CHARS, default: 1000000)
  --cont N              Automatically ask the model to continue N times if the response seems incomplete (missing <|||end|||>). (Config/Env: TULP_CONT, default: 0)
  --inspect-dir DIR     Save LLM request/response messages to timestamped subdirectories in DIR for debugging. (Config/Env: TULP_INSPECT_DIR)
  -v, --verbose         Enable verbose logging (DEBUG level). Overrides -q, config, and env. (Config/Env: TULP_LOG_LEVEL=DEBUG)
  -q, --quiet           Enable quiet logging (ERROR level). Overrides config and env. (Config/Env: TULP_LOG_LEVEL=ERROR)

LLM Provider Arguments:
  --groq_api_key GROQ_API_KEY
                        Groq Cloud API Key (Config/Env: TULP_GROQ_API_KEY)
  --ollama_host OLLAMA_HOST
                        Ollama host URL (e.g., http://127.0.0.1:11434) (Config/Env: TULP_OLLAMA_HOST)
  --anthropic_api_key ANTHROPIC_API_KEY
                        Anthropic API key (Config/Env: TULP_ANTHROPIC_API_KEY)
  --openai_api_key OPENAI_API_KEY
                        OpenAI (or compatible) API Key (Config/Env: TULP_OPENAI_API_KEY)
  --openai_baseurl OPENAI_BASEURL
                        Override OpenAI API base URL (e.g., for local models like Ollama: http://localhost:11434/v1) (Config/Env: TULP_OPENAI_BASEURL)
  --gemini_api_key GEMINI_API_KEY
                        Google AI (Gemini) API Key (Config/Env: TULP_GEMINI_API_KEY)

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
MODEL = gpt-4o

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

### Debugging with `--inspect-dir`

```bash
tulp --inspect-dir ./tulp_logs "Explain the concept of recursion" -v
```
This will create a timestamped subdirectory inside `./tulp_logs` containing JSON files for each request/response interaction with the LLM, useful for debugging prompts and responses.

## Origin of the Name

TULP stands for "TULP Understands Language Promptly". It's a recursive acronym, reflecting the tool's nature of using language models to process language.

## Changelog (Summary)

### v2.7.0 | YYYY-MM-DD (Current Refactor)
- **Major Refactor:** Improved modularity, readability, and adherence to clean code principles.
    - Broke down `tulp.py` into `cli.py`, `core.py`, `input_handler.py`, `response_parser.py`, `output_handler.py`, `executor.py`.
    - Moved prompt generation to `prompts/` package.
    - Centralized constants in `constants.py`.
    - Simplified configuration loading (`config.py`).
    - Renamed helper files (`arguments.py`, `logger.py`).
- **FML Tagging:** Changed internal block tagging from `(#tag)` to `<|||tag|||>`. Updated prompts and response parser accordingly. This is an internal change and should not affect user commands.
- **Dependencies & Compatibility:** Updated dependency handling and versions. Requires Python >= 3.8.
- **Minor Fixes:** Improved error messages, logging, and output handling.

### v2.6.x | 2024
- Added `--inspect-dir` for debugging.
- Added Gemini support.
- Fixed various bugs and improved error handling.

### v2.0 - v2.5.x | 2024
- Added support for Groq, Ollama, Anthropic models.
- Changed default model over time (gpt-4-turbo, gpt-4o).
- Added `--cont` option for automatic continuation.
- Improved large input handling and warnings.

### v1.x | 2023-2024
- Initial versions with OpenAI support.
- Added code interpretation (`-x`).
- Switched to newer OpenAI models and API versions.

*(For detailed history, see git log)*
