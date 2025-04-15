
import tweepy # Twitter API wrapper
import os     # To access environment variables (Replit Secrets)
import json   # To print output nicely
import time   # For potential delays
from datetime import datetime # To add timestamps

print("--- Starting Twitter Collection Script ---")

# Step 1: Load credentials from Replit Secrets
# Primarily need Bearer Token for read-only v2 search
print("Reading Twitter credentials (Bearer Token) from Replit Secrets...")
bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
# api_key = os.environ.get('TWITTER_API_KEY') # Needed for v1.1 or different auth
# api_secret_key = os.environ.get('TWITTER_API_SECRET_KEY') # Needed for v1.1
# access_token = os.environ.get('TWITTER_ACCESS_TOKEN') # Needed for v1.1 / user context
# access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET') # Needed for v1.1 / user context

if not bearer_token:
    print(">>> Error: TWITTER_BEARER_TOKEN secret not found.")
    print(">>> Please add the Bearer Token from Twitter Developer Portal to Replit Secrets.")
    exit()
else:
     print("Bearer Token loaded successfully.")

# Step 2: Authenticate with Twitter API v2 Client
print("\nInitializing Tweepy v2 Client...")
try:
    # Using v2 Client with Bearer Token (App-only context, standard for search)
    # wait_on_rate_limit=True automatically pauses if Twitter asks us to slow down
    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
    print("Tweepy v2 Client initialized successfully.")
    # Test authentication with a simple call (optional)
    # me = client.get_me() # This requires OAuth 2.0 PKCE or OAuth 1.0a User Context - Bearer token might not work
    # print(f"Testing authentication... (may fail with Bearer Token)") # Typically bearer doesn't allow get_me
except Exception as e:
    print(f">>> Error initializing Tweepy Client: {e}")
    print(">>> Check Bearer Token or other credentials if using different auth.")
    exit()

# --- Step 3: Configuration ---
# List of queries using Twitter Search Operators:
# Ref: https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query
# Exclude retweets, optional: filter by language (lang:en)
search_queries = [
    '(#Web3Jobs OR #CryptoHiring OR #BlockchainCareers) -is:retweet lang:en',
    '("web3 developer salary" OR "blockchain developer pay") -is:retweet lang:en',
    '(from:Coinbase OR from:binance OR from:ethereum) (hiring OR jobs OR career)', # Example company hiring keywords
    '#DeFiJobs -is:retweet lang:en'
]
# How many tweets to fetch per query (max 10 for recent search basic access)
collection_limit_per_query = 10

collected_tweets = [] # List to store results

# --- Step 4: Execute Search Queries ---
print("\nExecuting search queries for recent tweets (last 7 days)...")
try:
    for query in search_queries:
        print(f" Searching for: {query}")
        tweet_count = 0
        try:
            # Using search_recent_tweets (Standard v2 API)
            response = client.search_recent_tweets(
                query,
                max_results=collection_limit_per_query,
                # Specify fields you want besides default id/text
                tweet_fields=["created_at", "public_metrics", "author_id", "lang", "geo"]
            )

            # Process the response
            if response.data:
                for tweet in response.data:
                    collected_tweets.append({
                        'data_type': 'tweet',
                        'source_query': query,
                        'tweet_id': str(tweet.id), # Store ID as string often easier
                        'text': tweet.text,
                        'author_id': str(tweet.author_id) if tweet.author_id else None,
                        'language': tweet.lang,
                        'created_at_iso': tweet.created_at.isoformat() if tweet.created_at else None,
                        'public_metrics': tweet.public_metrics, # dict: impressions, likes, replies, retweets, etc.
                        'geo': tweet.geo, # Can contain place_id if location tagged
                        'collected_at_iso': datetime.utcnow().isoformat()
                    })
                    tweet_count += 1
                print(f"  Collected {tweet_count} tweets for this query.")
            elif response.errors:
                 print(f"  > API returned errors for this query: {response.errors}")
            else:
                print("  No tweets found matching this query in the recent period.")

        except tweepy.errors.TweepyException as e:
            print(f"  > Tweepy Error processing query '{query}': {e}")
            # Check for common errors
            if isinstance(e, tweepy.errors.TwitterServerError):
                 print("  >> Possible Twitter internal server error.")
            elif isinstance(e, tweepy.errors.Forbidden):
                 print("  >> Access forbidden. Check permissions for your API keys/Bearer token.")
            elif isinstance(e, tweepy.errors.TooManyRequests):
                 print("  >> Rate limit exceeded. The script should pause automatically due to wait_on_rate_limit=True.")
        except Exception as e_inner:
            print(f"  > Unexpected error during query '{query}': {e_inner}")

        # Optional polite pause between queries even if wait_on_rate_limit handles major pauses
        time.sleep(1)

except Exception as e_outer:
    print(f"\n>>> Major error occurred during Twitter search loop: {e_outer}")

# --- Step 5: Print Results ---
print(f"\n--- Collected total {len(collected_tweets)} Tweets ---")

# Print summary of first few items for verification
print("\n--- Example Collected Tweets (First 3) ---")
for i, item in enumerate(collected_tweets[:3]):
    print(f"\n--- Tweet {i+1} ---")
    print(f"  Tweet ID: {item.get('tweet_id')}")
    print(f"  Created At: {item.get('created_at_iso')}")
    print(f"  Author ID: {item.get('author_id')}")
    print(f"  Language: {item.get('language')}")
    print(f"  Text: {item.get('text')}")
    print(f"  Metrics: {item.get('public_metrics')}")

print("\n--- Twitter Collection Script Finished ---")