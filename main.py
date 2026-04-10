import os
import time
import keyboard
import pyperclip
import google.generativeai as genai
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Configure the Gemini API client
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key or api_key == "your_api_key_here":
    print("WARNING: GEMINI_API_KEY is missing or not set in the .env file.")
    print("Please set your API key in .env and restart the application.")
else:
    genai.configure(api_key=api_key)

# Using gemini-flash-latest which has broad compatibility across API versions.
model = genai.GenerativeModel('gemini-flash-latest')

import threading

def process_rewrite():
    if not api_key or api_key == "your_api_key_here":
         print("Cannot rewrite: Gemini API key missing.")
         return

    print("Hotkey triggered! Waiting for you to release keys...")
    
    # 1. Wait until user releases the keys to prevent keystroke ghosting / the "r" bug
    while keyboard.is_pressed('alt') or keyboard.is_pressed('r'):
        time.sleep(0.05)
        
    print("Fetching text...")
    
    # 2. Explicitly clear any logical stuck keys from the OS level
    keyboard.release('alt')
    keyboard.release('ctrl')
    keyboard.release('shift')

    # Simulate Ctrl+C to copy highlighted text.
    keyboard.send('ctrl+c')
    
    # Needs a small delay to ensure clipboard is populated
    time.sleep(0.15)
    
    # Read the copied text
    try:
        selected_text = pyperclip.paste()
    except Exception:
        print("Failed to access clipboard.")
        return
        
    if not selected_text or not str(selected_text).strip():
        print("No text was selected or copied. Returning.")
        return
        
    print(f"Original Text: {selected_text}")
    print("Sending text to Gemini for rewriting... (This usually takes 1-3 seconds)")
    
    # Prompt Gemini for grammar check and rewrite
    prompt = (
        "You are an AI grammar and writing assistant. "
        "Review the following text, correct any grammatical errors, and slightly "
        "rewrite it to sound more natural and clear, without drastically changing its original meaning or tone. "
        "Output ONLY the corrected text, with no introductory or conversational remarks.\n\n"
        f"Text to fix:\n{selected_text}"
    )

    try:
        response = model.generate_content(prompt)
        corrected_text = response.text.strip()
        print(f"Corrected Text: {corrected_text}")
        
        # Place the corrected text in the clipboard
        pyperclip.copy(corrected_text)
        
        # Simulate Ctrl+V to paste and replace
        time.sleep(0.1)
        
        # Explicit release again just before pasting to prevent stuck Alt+V
        keyboard.release('alt')
        keyboard.release('ctrl')
        
        keyboard.send('ctrl+v')
        
        print("Text successfully replaced!")
    except Exception as e:
        print(f"Error during AI generation or pasting: {e}")

def rewrite_text():
    # Run the actual logic in a separate thread to avoid blocking the global keyboard hook!
    # This prevents the whole keyboard from freezing/locking up and Alt getting stuck.
    threading.Thread(target=process_rewrite).start()

print("---------------------------------------------------------")
print("AI Rewrite Tool is running in the background!")
print("Highlight any text and press 'Alt+R' to rewrite and replace it.")
print("Press 'Ctrl+C' in this terminal to exit.")
print("---------------------------------------------------------")

# Listen for the global shortcut Alt+R
keyboard.add_hotkey('alt+r', rewrite_text, suppress=True)

# Keep the script running
keyboard.wait()
