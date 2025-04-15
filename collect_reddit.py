import praw          
import os           
import json          
import time          
from datetime import datetime 
print("--- Starting Reddit Collection Script ---")

# Step 1: Load credentials from Replit Secrets
print("Reading Reddit credentials from Replit Secrets...")
client_id = os.environ.get('REDDIT_CLIENT_ID')
client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
user_agent = os.environ.get('REDDIT_USER_AGENT')

# Check if all credentials were loaded
if not all([client_id, client_secret, user_agent]):
    print(">>> Error: Missing one or more Reddit credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT) in Replit Secrets.")
    print(">>> Please ensure they are set correctly in the 'Secrets' tab.")
    exit()
else:
    print("Reddit credentials loaded successfully.")
    print(f"User Agent: {user_agent}") # Confirm User Agent

# Step 2: Authenticate with Reddit API using PRAW
print("\nAttempting to authenticate with Reddit (read-only)...")
try:
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        read_only=True # Accessing public data doesn't require user login
    )
    # Verify authentication by accessing a basic attribute
    print(f"Authenticated successfully via PRAW. Read Only Mode: {reddit.read_only}")
except Exception as e:
    print(f">>> Error initializing PRAW or authenticating: {e}")
    print(">>> Check your Client ID, Secret, and User Agent format in Secrets.")
    exit()

# --- Step 3: Configuration ---
# List of subreddits to check for new posts
target_subreddits = ['ethereum', 'soliditydevs', 'CryptoCurrency', 'cryptojobs', 'web3']
# List of keywords to search for across targeted subreddits or 'all'
search_keywords = ['web3 developer salary', 'Coinbase hiring', 'blockchain skill demand', 'remote web3 role']
# How many posts/results to fetch from each source
collection_limit_per_source = 10 # Keep low for testing

collected_data = [] # List to store all collected post/comment dictionaries

# --- Step 4: Collect from Subreddits (New Posts) ---
print(f"\nFetching {collection_limit_per_source} new posts from subreddits: {target_subreddits}...")
try:
    for sub_name in target_subreddits:
        print(f" Accessing r/{sub_name}...")
        subreddit = reddit.subreddit(sub_name)
        post_count = 0
        try:
            # Iterate through the newest submissions in the subreddit
            for submission in subreddit.new(limit=collection_limit_per_source):
                collected_data.append({
                    'data_type': 'submission', # Indicate it's a post
                    'source_method': 'subreddit_new', # How we found it
                    'source_query': sub_name, # Which subreddit
                    'reddit_id': submission.id,
                    'title': submission.title,
                    'text': submission.selftext, # Post body text
                    'author': submission.author.name if submission.author else '[deleted]',
                    'subreddit': sub_name,
                    'score': submission.score,
                    'upvote_ratio': submission.upvote_ratio,
                    'num_comments': submission.num_comments,
                    'url': f"https://www.reddit.com{submission.permalink}", # Full URL
                    'created_utc_iso': datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                    'collected_at_iso': datetime.utcnow().isoformat()
                })
                post_count += 1
        except Exception as sub_err:
            print(f"  > Error processing subreddit r/{sub_name}: {sub_err}")

        print(f"  Collected {post_count} posts from r/{sub_name}.")
        time.sleep(1) # Brief pause between subreddits

except Exception as e:
    print(f">>> Error during subreddit collection phase: {e}")


# --- Step 5: Collect using Search Keywords ---
# NOTE: Reddit search can be less reliable/more restricted via API than browsing
print(f"\nSearching top {collection_limit_per_source} posts (sorted by 'new') using keywords...")
# Construct search scope (combine relevant subreddits or use 'all')
search_scope = '+'.join(target_subreddits) # Search within our target subs
# search_scope = 'all' # Uncomment to search all of Reddit (more rate limit intensive)
print(f"Search Scope: r/{search_scope}")
try:
    for keyword in search_keywords:
        print(f" Searching for '{keyword}'...")
        search_count = 0
        try:
            search_results = reddit.subreddit(search_scope).search(
                keyword,
                limit=collection_limit_per_source,
                sort='new', # Other sorts: 'relevance', 'hot', 'top', 'comments'
                time_filter='all' # Other times: 'hour', 'day', 'week', 'month', 'year'
            )
            for submission in search_results:
                 # Avoid adding duplicates if already fetched via subreddit.new
                 if not any(d['reddit_id'] == submission.id for d in collected_data):
                    collected_data.append({
                        'data_type': 'submission',
                        'source_method': 'search',
                        'source_query': keyword,
                        'reddit_id': submission.id,
                        'title': submission.title,
                        'text': submission.selftext,
                        'author': submission.author.name if submission.author else '[deleted]',
                        'subreddit': submission.subreddit.display_name, # Get subreddit from result
                        'score': submission.score,
                        'upvote_ratio': submission.upvote_ratio,
                        'num_comments': submission.num_comments,
                        'url': f"https://www.reddit.com{submission.permalink}",
                        'created_utc_iso': datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                        'collected_at_iso': datetime.utcnow().isoformat()
                    })
                    search_count += 1

        except Exception as search_err:
            print(f"  > Error processing search for '{keyword}': {search_err}")

        print(f"  Collected {search_count} NEW posts for keyword '{keyword}'.")
        time.sleep(2) # Pause slightly longer between different search queries

except Exception as e:
    print(f">>> Error during search collection phase: {e}")


# --- Step 6: Print Results ---
print(f"\n--- Collected total {len(collected_data)} Reddit items ---")
# Optional: Print the full data collected
# print("\n--- Full Collected Data (JSON) ---")
# print(json.dumps(collected_data, indent=2))

# Print summary of first few items for verification
print("\n--- Example Collected Items (First 3) ---")
for i, item in enumerate(collected_data[:3]):
    print(f"\n--- Item {i+1} ---")
    print(f"  ID: {item.get('reddit_id')}")
    print(f"  Title: {item.get('title')}")
    print(f"  Subreddit: r/{item.get('subreddit') or item.get('source_query')}") # Show subreddit name
    print(f"  Found Via: {item.get('source_method')}")
    # print(f" Text Snippet: {item.get('text', '')[:100]}...") # Uncomment to show text snippet

print("\n--- Reddit Collection Script Finished ---")