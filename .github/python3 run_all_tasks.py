# ----- scrape_cryptojobslist.py (Final Version with PostgreSQL) -----
import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urljoin
import re
import psycopg2 # Import PostgreSQL driver
import os
import sys      # To cleanly exit on major errors
from datetime import datetime # For timestamp

print("--- Starting CryptoJobsList Scraper ---")

# --- Database Connection Setup ---
db_conn = None
db_cursor = None
try:
    print("Reading POSTGRES_URI from Replit Secrets...")
    db_uri = os.environ.get('POSTGRES_URI')
    if not db_uri:
        print(">>> Error: POSTGRES_URI secret not found or is empty!")
        sys.exit(1)

    print("Connecting to external PostgreSQL database (Neon)...")
    db_conn = psycopg2.connect(db_uri)
    db_cursor = db_conn.cursor()
    print("Database connection successful!")

    # Verify table exists
    db_cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'job_postings');")
    table_exists = db_cursor.fetchone()[0]
    if not table_exists:
         print(">>> Error: 'job_postings' table does not exist! Run CREATE TABLE script first.")
         sys.exit(1)
    else:
        print("'job_postings' table found.")

except Exception as db_err:
    print(f">>> Database connection error: {db_err}")
     **complete code** for the **master runner script** (`run_all_tasks.py`) which is designed to be executed by the GitHub Actions workflow.

This script will run each of your individual data collection and processing scripts sequentially.

**Action:**

1.  **Go to Replit Files:** Find or create the file named `run_all_tasks.py`.
2.  **Replace Code:** Delete any existing code inside `run_all_tasks.py`.
3.  **Paste Code:** Copy the entire code block below and paste it into the empty file.

```python
# ----- run_all_tasks.py -----
# This script orchestrates the running of individual data collection
# and processing scripts in sequence. It's intended to be run by
# a scheduler like GitHub Actions.

import subprocess   # To run external scripts
import time         # For pausing between scripts
import sys          # To get the path to the python executable
from datetime import datetime # For timestamps

# --- Configuration ---
# List of scripts to run in the desired order
# Ensure these filenames exactly match the files in your repository root
scripts_to_run = [
    'collect_web3career.py',      # Fetch from Web3.Career API -> PostgreSQL
    'scrape_cryptojobslist.py',   # Scrape CryptoJobsList HTML -> PostgreSQL
    'collect_reddit.py',          # Fetch from Reddit API -> MongoDB
    'collect_twitter.py',         # Fetch from Twitter API -> MongoDB
    'process_sentiment.py'        # Process sentiment for MongoDB posts
]

# Timeout in seconds for each individual script to prevent hangs
# Adjust based on expected runtime (Twitter might need more due to rate limits)
SCRIPT_TIMEOUT_SECONDS = 1800 # 30 minutes per script

# Short pause between running scripts (in seconds)
PAUSE_BETWEEN_SCRIPTS = 5


# --- Main Execution Logic ---
if __name__ == "__main__":
    start_iso_time = datetime.utcnow().isoformat()
    print(f"--- Master Task Runner Started at {start_iso_time} UTC ---")

    overall_success = True # Flag to track if all scripts completed ok

    for script_name in scripts_to_run:
        print(f"\n{'='*15} Running script: {script_name} {'='*15}")
        script_start_time = time.time()

        try:
            # Run the script using the same Python interpreter that's running this script
            # Stderr is redirected to stdout for easier capture in Actions logs unless explicitly separated
            process = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,  # Capture stdout and stderr
                text=True,            # Decode output as text (UTF-8)
                check=True,           # Raise CalledProcessError on non-zero exit code
                timeout=SCRIPT_TIMEOUT_SECONDS # Prevent script from hanging indefinitely
            )

            # Print the output from the executed script
            print(f"\n--- Standard Output from {script_name} ---")
            print(process.stdout if process.stdout else "[No standard output]")
            # Print standard error only if it exists
            if process.stderr:
                print(f"\n--- Standard Error from {script_name} ---")
                print(process.stderr)
            print(f"--- Finished {script_name} Successfully ---")

        # --- Error Handling ---
        except FileNotFoundError:
            print(f">>> FATAL ERROR: Script file '{script_name}' not found!")
            overall_success = False
            break # Stop the whole process if a script file is missing

        except subprocess.CalledProcessError as e:
            # Script exited with an error code (e.g., due to an unhandled exception within the script)
            print(f">>> ERROR running {script_name}: Script exited with code {e.returncode}")
            print(f"--- FAILED SCRIPT STDOUT ---:\n{e.stdout}")
            print(f"--- FAILED SCRIPT STDERR ---:\n{e.stderr}")
            overall_success = False
            # Consider whether to 'break' (stop all) or 'continue' (run next script)
            break # Let's stop if one script fails unexpectedly

        except subprocess.TimeoutExpired as e:
             # Script took too long to run
             print(f">>> TIMEOUT running {script_name} after {e.timeout} seconds.")
             # Output captured before timeout might be in stdout/stderr
             print(f"--- TIMED OUT SCRIPT STDOUT ---:\n{e.stdout if e.stdout else '[No standard output]'}")
             print(f"--- TIMED OUT SCRIPT STDERR ---:\n{e.stderr if e.stderr else '[No standard error]'}")
             overall_success = False
             break # Stop if one script times out

        except Exception as e:
             # Catch any other unexpected errors during the subprocess call itself
             print(f">>> UNEXPECTED ERROR trying to run {script_name}: {e}")
             import traceback
             traceback.print_exc()
             overall_success = False
             break # Stop on unexpected errors

        finally:
             script_end_time = time.time()
             print(f"Script {script_name} execution time: {script_end_time - script_start_time:.2f} seconds.")
             print(f"Pausing for {PAUSE_BETWEEN_SCRIPTS} seconds...")
             time.sleep(PAUSE_BETWEEN_SCRIPTS)


    # --- Final Report ---
    end_iso_time = datetime.utcnow().isoformat()
    print(f"\n{'='*15} Master Task Runner Finished at {end_iso_time} UTC {'='*15}")
    if overall_success:
        print(">>> All scripts completed successfully (or handled errors internally).")
    else:
        print(">>> One or more scripts failed or were skipped due to previous failure.")
        # Exit with a non-zero code to make GitHub Actions show a failure
        sys.exit(1)
