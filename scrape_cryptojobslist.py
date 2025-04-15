import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urljoin
import re # For cleaning location text

# --- Configuration ---
BASE_URL = 'https://cryptojobslist.com'
target_url = 'https://cryptojobslist.com/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}
REQUEST_TIMEOUT = 25
POLITENESS_DELAY = 2

print("--- Starting CryptoJobsList Scraper ---")
print(f"Attempting to scrape: {target_url}")

try:
    # Step 1: Fetch HTML
    response = requests.get(target_url, headers=headers, timeout=REQUEST_TIMEOUT)
    print(f"Request sent. Status Code: {response.status_code}")
    response.raise_for_status()
    print("Successfully fetched page.")
    # Step 2: Parse HTML
    soup = BeautifulSoup(response.text, 'lxml')

    scraped_jobs_list = []

    # Step 3: Find Job Elements
    table_body_selector = 'table.job-preview-inline-table tbody'
    table_body = soup.select_one(table_body_selector)

    if not table_body:
        print(f"\n>>> ERROR: Could not find table body using selector: '{table_body_selector}'")
        exit()

    job_row_selector = 'tr[role="button"]'
    job_rows = table_body.select(job_row_selector)
    print(f"\nFound {len(job_rows)} potential job rows using selector '{job_row_selector}'.")

    if not job_rows:
        print("\n>>> Warning: No job rows found.")
        exit()

    print(f"\nProcessing potential job rows...")
    parse_count = 0

    # Step 4: Loop through found job rows and extract data
    for row_index, row in enumerate(job_rows):
        if row.has_attr('class') and 'notAJobAd' in row['class']:
            continue

        # Extract items we know work
        title_element = row.select_one('a.job-title-text')
        company_element = row.select_one('a.job-company-name-text')
        link_element = title_element
        tag_elements = row.select('td.job-tags span.category')

        title = title_element.get_text(strip=True) if title_element else 'N/A'
        company = company_element.get_text(strip=True) if company_element else 'N/A'
        tags = [tag.get_text(strip=True) for tag in tag_elements] if tag_elements else []
        relative_link = link_element['href'] if link_element and link_element.has_attr('href') else None
        job_url = urljoin(BASE_URL, relative_link) if relative_link else 'N/A'

        # --- Salary Extraction (Working) ---
        salary = 'N/A'
        salary_span = row.select_one('td span.align-middle')
        if salary_span:
             parent_div = salary_span.find_parent('div')
             if parent_div and parent_div.select_one('svg[stroke="currentColor"]'):
                  salary = salary_span.get_text(strip=True)


        # --- Location Extraction (Broader Attempt) ---
        location = 'N/A'
        # Select potential location cell (often the 5th cell, index 4)
        location_tds = row.select('td')
        # Find the TD most likely to contain location (heuristically, maybe the one before tags TD)
        potential_loc_td = None
        tags_td = row.select_one('td.job-tags')
        if tags_td:
            potential_loc_td = tags_td.find_previous_sibling('td')
        elif len(location_tds) >= 5: # Fallback to index if specific tags TD not found
            potential_loc_td = location_tds[4] # Often 5th cell overall

        if potential_loc_td:
             # Look for common location text patterns inside this TD
             location_span = potential_loc_td.select_one('span.text-sm') # Check if structure exists
             if location_span:
                  raw_location_text = location_span.get_text(strip=True)
                  # If it doesn't look like salary, assume it might be location/remote status
                  if salary == 'N/A' or salary != raw_location_text:
                       location = re.sub(r'^\s*📍\s*', '', raw_location_text).strip()
                       # Handle empty string if only emoji was present
                       if not location:
                            location = "Remote (Implied)" # Or keep N/A if preferred
             elif potential_loc_td.get_text(strip=True) and (salary == 'N/A' or salary != potential_loc_td.get_text(strip=True)):
                 # Fallback: If no specific span, grab TD text if not salary
                 location = potential_loc_td.get_text(strip=True)


        # Final check if location still N/A but 'Remote' tag exists
        if location == 'N/A' and 'Remote' in tags:
             location = 'Remote'


        # Assemble job data
        if title != 'N/A' and job_url != 'N/A':
            job_data = {
                'title': title,
                'company': company,
                'location': location, # Use refined location
                'salary_range': salary,
                'tags': tags,
                'source': 'CryptoJobsList',
                'url': job_url,
                'collected_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
            scraped_jobs_list.append(job_data)
            parse_count += 1


    # Step 5: Print Summary / Example (Print first 5 now)
    print(f"\n--- Successfully parsed {parse_count} jobs from the page ---")
    if scraped_jobs_list:
        print("\n--- Example Scraped Jobs (First 5) ---")
        for i, job in enumerate(scraped_jobs_list[:5]): # Print first 5 jobs
             print(f"\n--- Job {i+1} ---")
             print(json.dumps(job, indent=2))
    else:
        print("\n>>> Warning: No jobs were successfully parsed.")


# --- Error Handling --- (Same as before)
except requests.exceptions.HTTPError as http_err:
    print(f"\n>>> HTTP error occurred: {http_err}")
    print(f"Verify the target URL is correct: {target_url}")
except requests.exceptions.ConnectionError as conn_err:
     print(f"\n>>> Connection error occurred: {conn_err}")
     print("Check internet connection or if the website is blocking requests.")
except requests.exceptions.Timeout as timeout_err:
    print(f"\n>>> Request timed out after {REQUEST_TIMEOUT} seconds: {timeout_err}")
except requests.exceptions.RequestException as req_err:
    print(f"\n>>> An error occurred during the request: {req_err}")
except Exception as e:
    print(f"\n>>> An unexpected error occurred: {e}")
    import traceback
    print("--- Traceback ---")
    traceback.print_exc()
    print("-----------------")

finally:
    print(f"\nPausing for {POLITENESS_DELAY} seconds before finishing...")
    time.sleep(POLITENESS_DELAY)
    print("\n--- CryptoJobsList Scraper Finished ---")