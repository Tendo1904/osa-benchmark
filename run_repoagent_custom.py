from __future__ import annotations
import argparse
import subprocess
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from utils.docstring_processor import DocstringProcessor

def run_repo_agent(repo_path, model, base_url, ignore_list=None, print_hierarchy=False):
    repo_path = Path(repo_path).resolve()
    repo_name = repo_path.name
    
    print(f"Processing repository: {repo_name}")
    print(f"Path: {repo_path}")
    print(f"Model: {model}")
    
    start_dt = datetime.now()
    t0 = time.time()
    
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)
        
    cmd = [
        sys.executable, "-m", "repo_agent.main", "run",
        "-tp", str(repo_path),
        "-m", model,
        "-b", base_url,
        "-l", "English",
    ]
    
    if ignore_list:
        cmd.extend(["-i", ignore_list])
        
    if print_hierarchy:
        cmd.append("--print-hierarchy")

    print(f"Running command: {' '.join(cmd)}")
    
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{repo_name}_repoagent.log"
    
    env = os.environ.copy()
    if "OPENAI_API_KEY" not in env:
        print("WARNING: OPENAI_API_KEY not found in environment variables!")

    try:
        with log_file.open("w", encoding="utf-8") as lf:
            lf.write("CMD: " + " ".join(cmd) + "\n\n")
            
            # Using Popen to stream stdout to both console and file if needed, 
            # or just subprocess.run as before.
            proc = subprocess.run(
                cmd,
                check=False,
                text=True,
                stdout=lf,
                stderr=lf,
                env=env,
                timeout=10000 * 60, # Large timeout
            )
            
            if proc.returncode == 0:
                print("SUCCESS: Documentation generated.")
            else:
                print(f"FAILURE: Process exited with code {proc.returncode}. See logs at {log_file}")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    duration_min = (time.time() - t0) / 60.0
    print(f"Elapsed time: {duration_min:.2f} minutes")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RepoAgent with custom arguments")
    parser.add_argument("--repo", "-r", required=True, help="Path to local repository")
    parser.add_argument("--model", "-m", default="openai/gpt-5-mini", help="Model name (default: gpt-5-mini)")
    parser.add_argument("--base-url", "-b", default="https://openrouter.ai/api/v1", help="API Base URL")
    parser.add_argument("--ignore", "-i", default='tests', help="Comma-separated list of files/dirs to ignore (default: tests)")
    parser.add_argument("--print-hierarchy", "-pr", action="store_true", help="Print project hierarchy")
    
    args = parser.parse_args()
    
    # Load .env if present
    load_dotenv()
    
    run_repo_agent(
        args.repo,
        args.model,
        args.base_url,
        args.ignore,
        args.print_hierarchy
    )

    DocstringProcessor(repo_path=args.repo).run()

