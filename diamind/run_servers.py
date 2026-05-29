import subprocess
import sys
import os
import time
from pathlib import Path

ROOT = Path(__file__).parent

def main():
    print("Starting Diamind Backend and Frontend concurrently...")
    
    # 1. Start Backend (FastAPI)
    backend_cmd = [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--reload", "--port", "8000"]
    print(f"Launching Backend: {' '.join(backend_cmd)}")
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(ROOT),
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Give backend a moment to bind to the port
    time.sleep(1.5)
    
    # 2. Start Frontend (Next.js)
    frontend_cmd = ["npm", "run", "dev"]
    if os.name == "nt":
        frontend_cmd = ["npm.cmd", "run", "dev"]
        
    print(f"Launching Frontend: {' '.join(frontend_cmd)}")
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(ROOT / "frontend"),
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    print("\nBoth servers are running concurrently!")
    print("Backend API is available at: http://localhost:8000")
    print("Frontend UI is available at: http://localhost:3000\n")
    print("Press Ctrl+C to terminate both servers.\n")
    
    try:
        while True:
            if backend_proc.poll() is not None:
                print("Backend terminated unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("Frontend terminated unexpectedly.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTerminating servers...")
    finally:
        try:
            backend_proc.terminate()
        except Exception:
            pass
        try:
            frontend_proc.terminate()
        except Exception:
            pass
        print("Servers stopped.")

if __name__ == "__main__":
    main()
