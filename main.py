import os
import time
import keyboard
import pyperclip
from dotenv import load_dotenv
import threading

from ai_client import build_default_service

# Load variables from .env file
load_dotenv()

service = build_default_service()
_rewrite_lock = threading.Lock()

if service is None:
    print("WARNING: GEMINI_API_KEY is missing or not set in the .env file.")
    print("Please set your API key in .env and restart the application.")

def process_rewrite(mode="grammar", trigger_key="r"):
    if service is None:
        print("Cannot rewrite: Gemini API key missing.")
        return

    # Prevent overlapping hotkey runs (clipboard + placeholder are not concurrency-safe)
    if not _rewrite_lock.acquire(blocking=False):
        print("Another rewrite is already running. Ignoring this hotkey.")
        return

    try:
        total_start = time.perf_counter()

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
    
        # Wait with a short loop for the clipboard to populate (up to ~0.30s)
        selected_text = ""
        for _ in range(15):
            time.sleep(0.02)
            try:
                selected_text = pyperclip.paste()
                if selected_text:
                    break
            except Exception:
                pass

        copy_ms = (time.perf_counter() - total_start) * 1000.0
            
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
    
        try:
            if mode == "translate":
                print("Sending text to Gemini for English translation...")
            else:
                print("Sending text to Gemini for grammar rewrite...")

            corrected_text, from_cache, latency_ms = service.generate(mode, selected_text)
            if not corrected_text:
                raise RuntimeError("Gemini returned empty text")

            if from_cache:
                print("Cache hit (instant).")
            else:
                print(f"Gemini responded in {latency_ms:.0f} ms")

            print(f"Corrected Text: {corrected_text}")

            # 4. Remove the placeholder we just pasted
            for _ in range(len(placeholder)):
                keyboard.send('backspace')
                time.sleep(0.005)  # Tiny delay to ensure Windows registers each backspace

            # Place the corrected text in the clipboard
            pyperclip.copy(corrected_text)

            # Simulate Ctrl+V to paste and replace
            time.sleep(0.05)

            # Explicit release again just before pasting
            keyboard.release('alt')
            keyboard.release('ctrl')

            keyboard.send('ctrl+v')

            print("Text successfully replaced!")

            total_ms = (time.perf_counter() - total_start) * 1000.0
            print(
                f"Timing: copy {copy_ms:.0f} ms | AI {latency_ms:.0f} ms | total {total_ms:.0f} ms"
            )
        except Exception as e:
            print(f"Error during AI generation or pasting: {e}")

            # Best-effort restoration: remove placeholder and paste original text back.
            try:
                for _ in range(len(placeholder)):
                    keyboard.send('backspace')
                    time.sleep(0.002)
                pyperclip.copy(selected_text)
                time.sleep(0.02)
                keyboard.release('alt')
                keyboard.release('ctrl')
                keyboard.send('ctrl+v')
            except Exception:
                pass

    finally:
        _rewrite_lock.release()

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
