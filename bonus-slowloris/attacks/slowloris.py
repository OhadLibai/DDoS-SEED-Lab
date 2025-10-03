# slowloris.py

import socket
import time # for sleeping between sends
import random # random request values
import sys
import argparse

def slow_attack(target_ip, target_port, num_connections):
    list_of_sockets = []
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    print(f"Starting slowloris attack on {target_ip} with {num_connections} connections.")

    # Starts by opening multiple TCP sockets to the target.
    for _ in range(num_connections):
        try:
            # FILL CODE HERE
        except socket.error as e:
            print(f"Socket creation failed: {e}")
            break

    # Send partial HTTP request
    for s in list_of_sockets:
    # FILL CODE HERE

    try:
        # Keep-alive loop
        # Every 15 seconds, it sends a fake header (X-a) with random values.
        while True:
            print(f"Sending keep-alive headers... Sockets open: {len(list_of_sockets)}")
            # FILL CODE HERE
                except socket.error:
                    list_of_sockets.remove(s)
            
            time.sleep(15)
    except KeyboardInterrupt:
        print("\nAttack stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Basic slowloris attack script")
    parser.add_argument("hostname", help="Target hostname or IP address")
    parser.add_argument("connections", type=int, help="Number of connections to maintain")
    parser.add_argument("--port", type=int, default=8080, help="Target port (default: 8080)")
    
    args = parser.parse_args()
    
    slow_attack(args.hostname, args.port, args.connections)