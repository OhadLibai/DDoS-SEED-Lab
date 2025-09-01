# HTTP/2 Flood Lab - Victim Application

from quart import Quart, request
import time
import os
import asyncio
import random

# Initialize Quart app with environment override
# Set Flask environment variables before import to prevent KeyError
os.environ['FLASK_ENV'] = 'development'

# Import and create app with minimal initialization 
from quart import Quart

app = Quart(__name__)
app.config['PROVIDE_AUTOMATIC_OPTIONS'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
WORKLOAD = int(os.getenv("WORKLOAD", 5))
SCENARIO = os.getenv("SCENARIO", "default_scenario")

async def simulate_default_cpu_work(block_data="default_block_data", WORKLOAD=WORKLOAD):
    """
    Performs simple CPU-intensive calculations to consume processing power.
    Demonstrates basic arithmetic operations, string manipulations, and iterative computations.
    """
    iterations = 10000 * (WORKLOAD ** 2)  # Scale iterations with workload
    result_sum = 0
    result_string = str(block_data)
    
    for i in range(iterations):
        # Simple arithmetic operations
        result_sum += i * 2 + 1
        result_sum = result_sum % 1000000  # Keep numbers manageable
        
        # String operations
        if i % 100 == 0:
            result_string = result_string[::-1]  # Reverse string
            result_string += str(i)
            if len(result_string) > 1000:
                result_string = result_string[:500]  # Trim to keep memory usage low
        
        # Mathematical operations
        temp = (i ** 2 + i + 41) % 997  # Simple polynomial mod prime
        result_sum += temp
        
        # Periodic yield to allow other coroutines
        if i % 5000 == 0:
            await asyncio.sleep(0)
    
    print(f"Job Completed! Block: {block_data[:20]}..., Iterations: {iterations}, Final Sum: {result_sum}")
    
    return result_sum, iterations

async def get_scenario_processor():
    """Load and return the appropriate scenario processor based on SCENARIO environment variable."""
    if SCENARIO == "default_scenario":
        return simulate_default_cpu_work
    
    try:
        # Import scenario dynamically with randomized function selection
        if SCENARIO == "captcha":
            from scenarios.captcha_scenario import captcha_challenge
            challenge_types = ["visual", "math", "audio"]
            challenge_type = random.choice(challenge_types)
            return lambda data: captcha_challenge(challenge_type, WORKLOAD)
            
        elif SCENARIO == "crypto":
            from scenarios.crypto_scenario import cryptographic_challenge
            crypto_types = ["diffie_hellman", "certificate_chain", "tls_handshake"]
            crypto_type = random.choice(crypto_types)
            return lambda data: cryptographic_challenge(crypto_type, WORKLOAD)
            
        elif SCENARIO == "gaming":
            from scenarios.gaming_scenario import gaming_challenge
            game_types = ["sudoku", "maze", "procedural", "matchmaking"]
            game_type = random.choice(game_types)
            return lambda data: gaming_challenge(game_type, WORKLOAD)
            
        elif SCENARIO == "antibot":
            from scenarios.antibot_scenario import antibot_challenge
            bot_types = ["proof_of_work", "image_classification", "adaptive_puzzle"]
            bot_type = random.choice(bot_types)
            return lambda data: antibot_challenge(bot_type, WORKLOAD)
            
        elif SCENARIO == "webservice":
            from scenarios.webservice_scenario import webservice_challenge
            service_types = ["map_tiles", "routing", "weather", "translation"]
            service_type = random.choice(service_types)
            return lambda data: webservice_challenge(service_type, data, WORKLOAD)
            
        elif SCENARIO == "content_preview":
            from scenarios.content_preview_scenario import content_preview_challenge
            content_types = ["search", "image_thumbnail", "video_preview"]
            content_type = random.choice(content_types)
            return lambda data: content_preview_challenge(content_type, data, WORKLOAD)
        else:
            print(f"[WARNING] Unknown scenario '{SCENARIO}', falling back to default_scenario")
            return simulate_default_cpu_work
    except ImportError as e:
        print(f"[WARNING] Failed to load scenario '{SCENARIO}': {e}")
        print("[WARNING] Falling back to default_scenario")
        return simulate_default_cpu_work

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
    # Generic response format - whatever the scenario returns goes in "answer"
    result = await processor(block_data)
    
    return {
        "status": "success",
        "scenario": SCENARIO,
        "block_data": block_data,
        "answer": result,
        "message": f"{SCENARIO} completed successfully"
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
        "WORKLOAD": WORKLOAD
    }

if __name__ == "__main__":
    # Run with hypercorn for HTTP/2 support
    import hypercorn.asyncio
    config = hypercorn.Config()
    config.bind = ["0.0.0.0:80"]
    config.h2 = True  # Enable HTTP/2
    config.alpn_protocols = ["h2"]
    print(f"[SERVER] Starting HTTP/2 server on 0.0.0.0:80")
    print(f"[SERVER] Scenario: {SCENARIO}, WORKLOAD: {WORKLOAD}")
    print(f"[SERVER] HTTP/2 enabled: {config.h2}")
    print(f"[SERVER] ALPN protocols: {config.alpn_protocols}")
    asyncio.run(hypercorn.asyncio.serve(app, config))