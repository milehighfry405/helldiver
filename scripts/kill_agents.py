"""
Kill all running helldiver agent processes
"""
import subprocess
import sys

def kill_all_python():
    """Kill all python.exe processes"""
    try:
        result = subprocess.run(
            ['taskkill', '/F', '/IM', 'python.exe'],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode == 0:
            print("✓ All Python processes killed")
        else:
            print("No Python processes found or already killed")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Killing all Python processes...")
    kill_all_python()
