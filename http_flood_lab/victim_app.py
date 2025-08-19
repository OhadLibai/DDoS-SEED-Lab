# http_flood_lab/victim_app.py

from flask import Flask, request
import hashlib # Import the library for cryptographic hashing
import time
import os

app = Flask(__name__)
DIFFICULITY = int(os.getenv("DIFFICULITY", 5))

def simulate_proof_of_work(block_data="default_block_data", difficulty=DIFFICULITY):
    """
    Simulates a proof-of-work task, common in cryptocurrency and anti-spam systems.
    The server must find a 'nonce' (a number) that, when combined with data and hashed,
    produces a hash with a specific number of leading zeros. This can be CPU-intensive.
    """
    nonce = 0
    prefix = '0' * difficulty
    while True:
        # Combine the unique block_data with the current nonce
        input_str = f"{block_data}{nonce}".encode()
        
        # Calculate the SHA-256 hash
        result_hash = hashlib.sha256(input_str).hexdigest()
        
        # Check if the hash meets the difficulty criteria
        if result_hash.startswith(prefix):
            print(f"Solved! Block: {block_data[:20]}..., Nonce: {nonce}, Hash: {result_hash}")
            return result_hash, nonce
        
        nonce += 1

@app.route('/')
def handle_request():
    # Get block_data from request parameters or use default
    block_data = request.args.get('block_data', 'default_block_data')
    
    # For every request, the server processes the unique block_data
    result_hash, nonce = simulate_proof_of_work(block_data)
    
    # Return a response with the computed hash and nonce
    return {
        "status": "success",
        "block_data": block_data,
        "computed_hash": result_hash,
        "nonce": nonce,
        "message": "Proof-of-work completed successfully"
    }

@app.route('/health')
def health_check():
    # Simple health check endpoint that doesn't require heavy computation
    return {"status": "healthy", "message": "Server is running"}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)