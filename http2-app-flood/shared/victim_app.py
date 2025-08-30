# HTTP/2 Flood Lab - Victim Application

from quart import Quart, request
import hashlib
import time
import os
import asyncio

app = Quart(__name__)
DIFFICULITY = int(os.getenv("DIFFICULITY", 5))
SCENARIO = os.getenv("SCENARIO", "proof_of_work")

async def simulate_proof_of_work(block_data="default_block_data", DIFFICULITY=DIFFICULITY):
    """
    Simulates a proof-of-work task, common in cryptocurrency and anti-spam systems.
    The server must find a 'nonce' (a number) that, when combined with data and hashed,
    produces a hash with a specific number of leading zeros. This can be CPU-intensive.
    """
    nonce = 0
    prefix = '0' * DIFFICULITY
    while True:
        # Combine the unique block_data with the current nonce
        input_str = f"{block_data}{nonce}".encode()
        
        # Calculate the SHA-256 hash
        result_hash = hashlib.sha256(input_str).hexdigest()
        
        # Check if the hash meets the DIFFICULITY criteria
        if result_hash.startswith(prefix):
            print(f"Solved! Block: {block_data[:20]}..., Nonce: {nonce}, Hash: {result_hash}")
            return result_hash, nonce
        
        nonce += 1
        
        # Allow other coroutines to run periodically
        if nonce % 1000 == 0:
            await asyncio.sleep(0)

async def get_scenario_processor():
    """Load and return the appropriate scenario processor based on SCENARIO environment variable."""
    if SCENARIO == "proof_of_work":
        return simulate_proof_of_work
    
    try:
        # Import scenario dynamically
        if SCENARIO == "captcha":
            from scenarios.captcha_scenario import captcha_challenge
            return lambda data: captcha_challenge("visual", DIFFICULITY)
        elif SCENARIO == "crypto":
            from scenarios.crypto_scenario import cryptographic_challenge
            return lambda data: cryptographic_challenge("diffie_hellman", DIFFICULITY)
        elif SCENARIO == "gaming":
            from scenarios.gaming_scenario import gaming_challenge
            return lambda data: gaming_challenge("sudoku", DIFFICULITY)
        elif SCENARIO == "antibot":
            from scenarios.antibot_scenario import antibot_challenge
            return lambda data: antibot_challenge("proof_of_work", DIFFICULITY)
        elif SCENARIO == "webservice":
            from scenarios.webservice_scenario import webservice_challenge
            return lambda data: webservice_challenge("map_tiles", data, DIFFICULITY)
        elif SCENARIO == "content":
            from scenarios.content_preview_scenario import content_preview_challenge
            return lambda data: content_preview_challenge("search", data, DIFFICULITY)
        else:
            print(f"[WARNING] Unknown scenario '{SCENARIO}', falling back to proof_of_work")
            return simulate_proof_of_work
    except ImportError as e:
        print(f"[WARNING] Failed to load scenario '{SCENARIO}': {e}")
        print("[WARNING] Falling back to proof_of_work")
        return simulate_proof_of_work

@app.route('/')
async def handle_request():
    # Log HTTP version information
    http_version = getattr(request, 'http_version', 'Unknown')
    print(f"[REQUEST] HTTP Version: {http_version} | Path: {request.path} | Scenario: {SCENARIO}")
    
    # Get block_data from request parameters or use default
    block_data = request.args.get('block_data', 'default_block_data')
    
    # Get the appropriate scenario processor
    processor = await get_scenario_processor()
    
    # Process the request using the selected scenario
    if SCENARIO == "proof_of_work":
        result_hash, nonce = await processor(block_data)
        return {
            "status": "success",
            "scenario": SCENARIO,
            "block_data": block_data,
            "computed_hash": result_hash,
            "nonce": nonce,
            "message": f"{SCENARIO} completed successfully"
        }
    else:
        # For other scenarios, the processor returns a different format
        result = await processor(block_data)
        return {
            "status": "success",
            "scenario": SCENARIO,
            "block_data": block_data,
            "result": result,
            "message": f"{SCENARIO} challenge completed successfully"
        }

@app.route('/health')
async def health_check():
    # Log HTTP version information
    http_version = getattr(request, 'http_version', 'Unknown')
    print(f"[HEALTH] HTTP Version: {http_version} | Path: {request.path} | Scenario: {SCENARIO}")
    
    # Simple health check endpoint that doesn't require heavy computation
    return {
        "status": "healthy", 
        "message": "Server is running", 
        "protocol": "HTTP/2",
        "scenario": SCENARIO,
        "DIFFICULITY": DIFFICULITY
    }

if __name__ == "__main__":
    # Run with hypercorn for HTTP/2 support
    import hypercorn.asyncio
    config = hypercorn.Config()
    config.bind = ["0.0.0.0:80"]
    config.h2 = True  # Enable HTTP/2
    print(f"[SERVER] Starting HTTP/2 server on 0.0.0.0:80")
    print(f"[SERVER] Scenario: {SCENARIO}, DIFFICULITY: {DIFFICULITY}")
    print(f"[SERVER] HTTP/2 enabled: {config.h2}")
    asyncio.run(hypercorn.asyncio.serve(app, config))