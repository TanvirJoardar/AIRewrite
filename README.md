# AI Rewrite

AI Rewrite is a lightweight, background Windows utility that acts as your personal AI writing assistant. It allows you to seamlessly correct grammar or translate text directly in any application you are using, without needing to copy and paste into a separate web browser or tool.

By highlighting text and pressing a simple keyboard shortcut, the tool instantly sends the text to the Google Gemini AI, processes it, and replaces your highlighted text with the improved version right before your eyes.

## Features
- **Grammar Correction (`Alt + R`)**: Highlights text, fixes grammatical errors, and slightly rewrites it to sound more natural and clear.
- **English Translation (`Alt + E`)**: Instantly translates the highlighted text from any language into English.
- **Visual Status Indicator**: While the AI is processing your request (which usually takes ~1 second), a visual `[AI working...]` placeholder appears so you know it's thinking.
- **Background Service**: Runs silently in the background of your computer without intrusive console windows.

## Performance notes

This tool now uses a small local SQLite cache so repeating the same rewrite/translation returns instantly.

Optional environment variables you can set in `.env`:

- `GEMINI_MODEL` (default: `gemini-flash-lite-latest`)
- `GEMINI_TIMEOUT_S` (default: `60`)
- `GEMINI_TRANSPORT` (optional; set to `rest` if requests feel slow or time out)
- `AI_REWRITE_CACHE_PATH` (default: `.cache/ai_cache.sqlite`)

## Prerequisites
- Windows OS (requires the Windows clipboard and hotkey registry).
- Python 3.10+ installed.
- A free [Google Gemini API Key](https://aistudio.google.com/app/apikey).

## Setup & Installation

1. **Configure your API Key**
   - Create a file named `.env` in the root folder of this project (if it doesn't already exist).
   - Add your Gemini API key inside the `.env` file like this:
     ```env
     GEMINI_API_KEY=your_actual_api_key_here
     ```

2. **Run the Initialization Script**
   - Double-click the **`start_rewriter.cmd`** file in the project folder. 
   - This script will automatically activate the Python virtual environment and run the core `main.py` script.
   - *Note: If you haven't installed the dependencies yet, you must run `pip install -r requirements.txt` inside your virtual environment first.*

## Development Mode

If you want to run the project in development mode to see real-time logs and debug information:

1. **Open a terminal** in the project directory.
2. **Run the quick launch command**:
   ```bash
   python launch
   ```
   This command automatically activates the virtual environment and starts the program. You will see logs in the terminal showing the original text, the AI's response, and any processing information.

Alternatively, you can run it manually:
1. Activate the venv: `.\venv\Scripts\Activate.ps1`
2. Run the script: `python main.py`

## Usage

Once the tool is running, you can minimize or close the terminal window (if it launched via the `.cmd` file). 

1. Go to any app where you can type (Notepad, Word, your web browser, etc).
2. Type a sentence and **highlight/select** the text.
3. Press **`Alt + R`** to fix the grammar, or **`Alt + E`** to translate it to English.
4. Wait approximately 1-2 seconds. You will see the `[AI working...]` text appear and then automatically be replaced by your corrected text.

## Auto-Start with Windows

This tool is designed to run completely silently in the background when your computer turns on. 

If this has been configured, the script launches via `pythonw.exe` (windowless Python) triggered by a Windows Registry key in `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. You can easily disable or manage this by opening the **Task Manager**, going to the **Startup apps** tab, and managing `AIRewrite`.

When running silently, you can identify the process and kill it via the Task Manager (look for `AIRewrite.exe` or `pythonw.exe`).
