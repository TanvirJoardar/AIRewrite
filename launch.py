import os
import subprocess
import sys

def main():
    # Path to the venv python interpreter on Windows
    venv_python = os.path.join("venv", "Scripts", "python.exe")
    
    if not os.path.exists(venv_python):
        # Try Unix path just in case
        venv_python = os.path.join("venv", "bin", "python")

    if not os.path.exists(venv_python):
        print("Error: Virtual environment 'venv' not found.")
        print("Please make sure you have created the virtual environment in the 'venv' folder.")
        return

    # Path to the main script
    main_script = "main.py"
    
    if not os.path.exists(main_script):
        print(f"Error: '{main_script}' not found in the current directory.")
        return

    # Run the main script using the venv's python
    # This ensures all dependencies in the venv are available
    try:
        subprocess.run([venv_python, main_script])
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()
