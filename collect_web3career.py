# ----- collect_web3career.py -----
import requests
import os
import json
import time
from datetime import datetime # Added for collected_at timestamp

print("--- Starting Web3.Career Collection Script ---")

# Step 1: Get API Key (Token) from Replit Secrets
print("Reading WEB3_CAREER_API_KEY from Replit Secrets...")
api_key = os.environ.get('WEB3_CAREER_API_KEY')

if not api_key:
    print(">>> Error: WEB3_CAREER_API_KEY secret not found or is empty!")
    print(">>> Please add the token provided by Web3.Career in the 'Secrets' tab.")
    exit() # Exit if no key is found
else:
    # Optional: Print partial key to confirm it's loaded (DO NOT print the whole key)
    print(f"API Key loaded successfully (starts with: {api_key[:4]}...).")

# Step 2: Configure API Request
api_endpoint = "https://web3.career/api/v1" # Base URL
params = {
    'token': api_key,             # Token is now a parameter
    'limit': 100,                 # Get up to 100 jobs
    'show_description': 'true',   # Request job descriptions
    # Add other filters here if needed, e.g.:
    # 'remote': 'true',
    # 'country': 'united-states',
    # 'tag': 'react',
}
print(f"\nRequesting data from: {api_endpoint}")
# Create a temporary dict for printing, hiding the token
printable_params = {k: v for k, v in params.items() if k != 'token'}
print(f"With parameters: {printable_params}")


# Step 3: Make the API Request
try:
    print("\nSending GET request to the API...")
    response = requests.get(api_endpoint, params=params, timeout=25) # Increased timeout
    response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
    print(f"API request successful! Status Code: {response.status_code}")

    # Step 4: Parse the JSON Response
    print("\nAttempting to parse JSON response...")
    raw_data = response.json()
    print("JSON parsing successful.")

    # *** CRITICAL DEBUGGING STEP ***
    # Let's inspect the structure hinted at by the PHP code `[2]`
    print("\n--- DEBUG: Inspecting raw_data structure ---")
    print(f"Type of raw_data: {type(raw_data)}")
    jobs_list = [] # Initialize empty list
    if isinstance(raw_data, list):
        print(f"raw_data is a list with length: {len(raw_data)}")
        if len(raw_data) > 2:
            # TRYING the [2] index based on PHP hint
            print("Attempting to access index [2] based on PHP hint...")
            potential_jobs = raw_data[2]
            if isinstance(potential_jobs, list):
                 print("Item at index [2] is a LIST - likely contains the jobs.")
                 jobs_list = potential_jobs
            else:
                 print(f"Item at index [2] is NOT a list, it's type: {type(potential_jobs)}. Cannot use as job list.")
        else:
            print("raw_data list has fewer than 3 items - cannot access index [2].")
    elif isinstance(raw_data, dict):
        print(f"raw_data is a dictionary with keys: {list(raw_data.keys())}")
        print("Looking for a key containing a list of jobs (e.g., 'jobs', 'data', 'results')...")
        # You would need to check common keys here based on output
        if 'jobs' in raw_data and isinstance(raw_data['jobs'], list):
            jobs_list = raw_data['jobs']
            print("Found jobs in raw_data['jobs']")
        # Add other potential key checks here
    else:
        print("raw_data is neither a list nor a dictionary. Cannot process.")

    print("--- END DEBUG ---")

    # Step 5: Extract Job Details
    collected_jobs_details = []
    print(f"\nProcessing the extracted jobs_list (contains {len(jobs_list)} items)...")
    skipped_count = 0
    for job_entry in jobs_list:
        # Ensure job_entry is a dictionary
        if isinstance(job_entry, dict):
            # Extract fields based on API docs / PHP example
            job_data = {
                'external_id': job_entry.get('id'),
                'title': job_entry.get('title'),
                'company': job_entry.get('company'),
                'location': job_entry.get('location'), # May combine city/country
                'country': job_entry.get('country'),
                'city': job_entry.get('city'),
                'apply_url': job_entry.get('apply_url'), # Important for linking back!
                'tags': job_entry.get('tags', []), # Expecting a list
                'description': job_entry.get('description'),
                'date_posted_epoch': job_entry.get('date_epoch'),
                'source': 'Web3.Career', # Hardcode the source
                'collected_at': datetime.utcnow().isoformat() # Add timestamp
            }
            # Optional: Clean or transform data here if needed
            if job_data['tags'] and not isinstance(job_data['tags'], list):
                 print(f"  Warning: Tags for job {job_data['external_id']} are not a list: {job_data['tags']}")

            collected_jobs_details.append(job_data)
        else:
            # This handles cases where items within the list might not be jobs
            skipped_count += 1

    if skipped_count > 0:
        print(f"Warning: Skipped {skipped_count} items in jobs_list because they were not dictionaries.")

    # Step 6: Print Summary / Example
    print(f"\n--- Successfully parsed {len(collected_jobs_details)} jobs from the API response ---")
    if collected_jobs_details:
        print("\n--- Example Parsed Job ---")
        # Print the details of the first job found
        print(json.dumps(collected_jobs_details[0], indent=2))
    else:
        print("\nNo jobs were successfully parsed from the response.")
        print("Check the 'DEBUG' section output above to understand the raw data structure.")


except requests.exceptions.HTTPError as http_err:
    print(f"\n>>> HTTP error occurred: {http_err}")
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text[:500]}") # Show beginning of response body
    if response.status_code in [401, 403]:
          print(">>> Authentication error! Check if your token in Replit Secrets is correct and active.")
except requests.exceptions.RequestException as req_err:
    print(f"\n>>> Request error occurred: {req_err}")
except json.JSONDecodeError:
    print("\n>>> Error: Failed to decode JSON response from the API.")
    print(f"Status Code was: {response.status_code if 'response' in locals() else 'N/A'}")
    print(f"Response text snippet: {response.text[:500] if 'response' in locals() else 'N/A'}")
except Exception as e:
    print(f"\n>>> An unexpected error occurred: {e}")
    # Optionally add traceback here for more detailed unexpected errors
    # import traceback
    # traceback.print_exc()

print("\n--- Web3.Career Collection Script Finished ---")