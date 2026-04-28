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
GRAMMAR_MODEL = genai.GenerativeModel("gemini-flash-lite-latest")
TRANSLATE_MODEL = genai.GenerativeModel("gemini-flash-lite-latest")

def _build_generation_config(text):
    # Estimate a tight output token budget to reduce latency.
    estimated_tokens = max(64, int(len(text) / 4) + 64)
    max_output_tokens = min(1024, estimated_tokens)
    return {
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 20,
        "max_output_tokens": max_output_tokens,
    }

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

    # Clear the clipboard first so we know when Ctrl+C actually succeeds
    pyperclip.copy('')
    
    # Simulate Ctrl+C to copy highlighted text.
    keyboard.send('ctrl+c')
    
    # Wait with a short loop for the clipboard to populate (up to 0.5s)
    selected_text = ""
    for _ in range(10):
        time.sleep(0.05)
        try:
            selected_text = pyperclip.paste()
            if selected_text:
                break
        except Exception:
            pass
            
    if not selected_text or not str(selected_text).strip():
        print("No text was selected or copied. Returning.")
        return
        
    if str(selected_text).strip() == "[AI working...]":
        print("Selected text was the placeholder. Aborting to prevent loop.")
        return
        
    # 3. Insert a visual placeholder right over the selected text so the user knows it's working!
    placeholder = "[AI working...]"
    pyperclip.copy(placeholder)
    
    # Ensure keys are clear then paste
    keyboard.release('alt')
    keyboard.release('ctrl')
    keyboard.send('ctrl+v')
    
    print(f"Original Text: {selected_text}")
    
    if mode == "translate":
        print("Sending text to Gemini for English translation... (Optimized for speed)")
        model = TRANSLATE_MODEL
        prompt = (
            "Translate to English. Reply ONLY with the English translation, no chat.\n"
            f"{selected_text}"
        )
    else:
        print("Sending text to Gemini for grammar rewrite... (Optimized for speed)")
        model = GRAMMAR_MODEL
        prompt = (
            "Fix grammar and improve clarity. Reply ONLY with the corrected text, no chat.\n"
            f"{selected_text}"
        )

    try:
        response = model.generate_content(
            prompt,
            generation_config=_build_generation_config(selected_text),
        )
        corrected_text = response.text.strip()
        print(f"Corrected Text: {corrected_text}")
        
        # 4. Remove the placeholder we just pasted
        for _ in range(len(placeholder)):
            keyboard.send('backspace')
            time.sleep(0.005) # Tiny delay to ensure Windows registers each backspace
            
        # Place the corrected text in the clipboard
        pyperclip.copy(corrected_text)
        
        # Simulate Ctrl+V to paste and replace
        time.sleep(0.1)
        
        # Explicit release again just before pasting 
        keyboard.release('alt')
        keyboard.release('ctrl')
        
        keyboard.send('ctrl+v')
        
        print("Text successfully replaced!")
    except Exception as e:
        error_text = f"[AI error: {str(e)}]"
        print(f"Error during AI generation or pasting: {e}")

        # Replace the placeholder with the error bracket so the user sees it inline.
        for _ in range(len(placeholder)):
            keyboard.send('backspace')
            time.sleep(0.005)

        pyperclip.copy(error_text)
        time.sleep(0.05)
        keyboard.release('alt')
        keyboard.release('ctrl')
        keyboard.send('ctrl+v')

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
