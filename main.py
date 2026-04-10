import os
import time
import keyboard
import pyperclip
import google.generativeai as genai
from dotenv import load_dotenv
import threading

# Load variables from .env file
load_dotenv()

# Configure the Gemini API client
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key or api_key == "your_api_key_here":
    print("WARNING: GEMINI_API_KEY is missing or not set in the .env file.")
    print("Please set your API key in .env and restart the application.")
else:
    genai.configure(api_key=api_key)

# Using gemini-flash-lite-latest which is significantly faster for simple text tasks
model = genai.GenerativeModel('gemini-flash-lite-latest')

def process_rewrite(mode="grammar", trigger_key="r"):
    if not api_key or api_key == "your_api_key_here":
         print("Cannot rewrite: Gemini API key missing.")
         return

    print(f"\nHotkey triggered ({mode} mode)! Waiting for you to release keys...")
    
    # 1. Wait until user releases the keys to prevent keystroke ghosting / character bleeding
    while keyboard.is_pressed('alt') or keyboard.is_pressed(trigger_key):
        time.sleep(0.01)
        
    print("Fetching text...")
    
    # 2. Explicitly clear any logical stuck keys from the OS level
    keyboard.release('alt')
    keyboard.release('ctrl')
    keyboard.release('shift')

    # Simulate Ctrl+C to copy highlighted text.
    keyboard.send('ctrl+c')
    
    # Needs a small delay to ensure clipboard is populated
    time.sleep(0.05)
    
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
    
    if mode == "translate":
        print("Sending text to Gemini for English translation... (Optimized for speed)")
        prompt = f"Translate the following text to English. Reply ONLY with the English translation, no chat:\n{selected_text}"
    else:
        print("Sending text to Gemini for grammar rewrite... (Optimized for speed)")
        prompt = f"Fix the grammar of this text. Reply ONLY with the corrected text, no chat:\n{selected_text}"

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
    # Run the actual logic in a separate thread to avoid blocking the global keyboard hook
    threading.Thread(target=process_rewrite, args=("grammar", "r")).start()

def translate_text():
    # Run translation in a separate thread
    threading.Thread(target=process_rewrite, args=("translate", "e")).start()

print("---------------------------------------------------------")
print("AI Rewrite Tool is running in the background!")
print("Highlight any text and press 'Alt+R' to rewrite and replace it.")
print("Highlight any text and press 'Alt+E' to translate it to English.")
print("Press 'Ctrl+C' in this terminal to exit.")
print("---------------------------------------------------------")

# Listen for the global shortcuts
keyboard.add_hotkey('alt+r', rewrite_text, suppress=True)
keyboard.add_hotkey('alt+e', translate_text, suppress=True)

# Keep the script running
keyboard.wait()
