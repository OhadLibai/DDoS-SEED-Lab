# scenarios/antibot_scenario.py

import hashlib
import random
import time
import string
import asyncio

def proof_of_work_challenge(DIFFICULITY=4):
    """
    Generate proof-of-work challenges with increasing DIFFICULITY.
    Forces clients to perform CPU-intensive computation to prove they're not bots.
    """
    challenge_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    target_prefix = '0' * DIFFICULITY
    
    # The challenge: find a nonce that makes hash(challenge_id + nonce) start with target_prefix
    return {
        "challenge_id": challenge_id,
        "target_prefix": target_prefix,
        "DIFFICULITY": DIFFICULITY,
        "instruction": f"Find nonce where SHA256({challenge_id} + nonce) starts with {target_prefix}"
    }

async def solve_proof_of_work(challenge_id, target_prefix, max_iterations=1000000):
    """
    Server-side proof-of-work solving (for validation or demonstration).
    CPU-intensive hash computation.
    """
    nonce = 0
    start_time = time.time()
    
    while nonce < max_iterations:
        test_string = f"{challenge_id}{nonce}"
        hash_result = hashlib.sha256(test_string.encode()).hexdigest()
        
        if hash_result.startswith(target_prefix):
            end_time = time.time()
            return {
                "success": True,
                "nonce": nonce,
                "hash": hash_result,
                "computation_time": end_time - start_time,
                "iterations": nonce + 1
            }
        
        nonce += 1
        
        # Yield control every 1000 iterations to avoid blocking
        if nonce % 1000 == 0:
            await asyncio.sleep(0)
    
    end_time = time.time()
    return {
        "success": False,
        "max_iterations_reached": True,
        "computation_time": end_time - start_time,
        "iterations": max_iterations
    }

async def image_classification_challenge():
    """
    Simulate complex image classification tasks like "Select all traffic lights".
    CPU-intensive image processing and pattern recognition.
    """
    # Simulate different image types and their classification complexity
    image_types = [
        {"type": "traffic_lights", "complexity": 3, "processing_time": 0.5},
        {"type": "crosswalks", "complexity": 4, "processing_time": 0.8},
        {"type": "vehicles", "complexity": 2, "processing_time": 0.3},
        {"type": "storefronts", "complexity": 5, "processing_time": 1.2},
        {"type": "bicycles", "complexity": 3, "processing_time": 0.6}
    ]
    
    selected_type = random.choice(image_types)
    grid_size = 3  # 3x3 grid of images
    
    # Simulate CPU-intensive image analysis
    analysis_results = []
    total_processing_time = 0
    
    for i in range(grid_size * grid_size):
        # Simulate complex image processing operations
        image_id = f"img_{i}_{random.randint(1000, 9999)}"
        
        # Simulate feature extraction (CPU-intensive)
        features = []
        for _ in range(100):  # Extract 100 features per image
            feature = sum([random.randint(0, 255) for _ in range(64)])  # Simulate pixel analysis
            features.append(feature)
        
        # Simulate classification algorithm
        classification_score = 0
        for j in range(selected_type["complexity"] * 1000):
            classification_score += sum(features) / len(features) * random.random()
        
        # Determine if image contains the target object
        contains_target = classification_score > (selected_type["complexity"] * 50000)
        
        analysis_results.append({
            "image_id": image_id,
            "contains_target": contains_target,
            "confidence_score": classification_score,
            "features_extracted": len(features)
        })
        
        total_processing_time += selected_type["processing_time"]
        
        # Yield control to avoid blocking
        await asyncio.sleep(0.01)  # Small delay to simulate processing
    
    correct_images = [result["image_id"] for result in analysis_results if result["contains_target"]]
    
    return {
        "challenge_type": "image_classification",
        "target_object": selected_type["type"],
        "grid_size": f"{grid_size}x{grid_size}",
        "total_images": len(analysis_results),
        "correct_images": correct_images,
        "processing_time": total_processing_time,
        "complexity_level": selected_type["complexity"],
        "analysis_results": analysis_results
    }

async def computational_puzzle_with_scaling(request_count=1):
    """
    Generate computational puzzles that increase in DIFFICULITY based on request frequency.
    Implements adaptive DIFFICULITY to counter rapid automated requests.
    """
    base_DIFFICULITY = 2
    scaled_DIFFICULITY = min(base_DIFFICULITY + (request_count // 10), 8)  # Cap at DIFFICULITY 8
    
    puzzle_types = [
        "prime_factorization",
        "fibonacci_calculation",
        "hash_collision",
        "matrix_multiplication"
    ]
    
    puzzle_type = random.choice(puzzle_types)
    
    if puzzle_type == "prime_factorization":
        # Generate a semi-prime number to factor
        prime1 = generate_prime(10**(scaled_DIFFICULITY))
        prime2 = generate_prime(10**(scaled_DIFFICULITY))
        target_number = prime1 * prime2
        
        # Solve it (CPU-intensive)
        factors = await factorize_number(target_number)
        
        return {
            "puzzle_type": puzzle_type,
            "challenge": f"Find prime factors of {target_number}",
            "target_number": target_number,
            "expected_factors": factors,
            "DIFFICULITY": scaled_DIFFICULITY,
            "request_count": request_count
        }
        
    elif puzzle_type == "fibonacci_calculation":
        n = 25 + scaled_DIFFICULITY * 5  # Fibonacci number to calculate
        fib_result = await calculate_fibonacci(n)
        
        return {
            "puzzle_type": puzzle_type,
            "challenge": f"Calculate Fibonacci({n})",
            "n": n,
            "expected_result": fib_result,
            "DIFFICULITY": scaled_DIFFICULITY,
            "request_count": request_count
        }
        
    elif puzzle_type == "matrix_multiplication":
        size = 10 + scaled_DIFFICULITY * 5
        matrix_a = generate_random_matrix(size, size)
        matrix_b = generate_random_matrix(size, size)
        result_matrix = await multiply_matrices(matrix_a, matrix_b)
        
        return {
            "puzzle_type": puzzle_type,
            "challenge": f"Multiply {size}x{size} matrices",
            "matrix_size": size,
            "expected_result_checksum": checksum_matrix(result_matrix),
            "DIFFICULITY": scaled_DIFFICULITY,
            "request_count": request_count
        }
    
    else:  # hash_collision
        target_prefix = '0' * (scaled_DIFFICULITY + 1)
        challenge_data = ''.join(random.choices(string.ascii_letters, k=20))
        collision_result = await find_hash_collision(challenge_data, target_prefix)
        
        return {
            "puzzle_type": puzzle_type,
            "challenge": f"Find hash collision for '{challenge_data}' with prefix '{target_prefix}'",
            "challenge_data": challenge_data,
            "target_prefix": target_prefix,
            "expected_result": collision_result,
            "DIFFICULITY": scaled_DIFFICULITY,
            "request_count": request_count
        }

def generate_prime(min_val):
    """Generate a prime number >= min_val"""
    candidate = max(min_val, 2)
    while not is_prime(candidate):
        candidate += 1
    return candidate

def is_prime(n):
    """Check if number is prime (simplified implementation)"""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

async def factorize_number(n):
    """Simple factorization (CPU-intensive for large numbers)"""
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
        
        # Yield control every 100 iterations to avoid blocking
        if d % 100 == 0:
            await asyncio.sleep(0)
    if n > 1:
        factors.append(n)
    return factors

async def calculate_fibonacci(n):
    """Calculate Fibonacci number (CPU-intensive for large n)"""
    if n <= 1:
        return n
    
    # Use iterative approach to avoid stack overflow
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
        
        # Yield control every 1000 iterations to avoid blocking
        if i % 1000 == 0:
            await asyncio.sleep(0)
    return b

def generate_random_matrix(rows, cols):
    """Generate random matrix"""
    return [[random.randint(1, 100) for _ in range(cols)] for _ in range(rows)]

async def multiply_matrices(a, b):
    """Matrix multiplication (CPU-intensive)"""
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    
    if cols_a != rows_b:
        raise ValueError("Matrix dimensions don't match for multiplication")
    
    result = [[0 for _ in range(cols_b)] for _ in range(rows_a)]
    
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
        
        # Yield control every row to avoid blocking
        if i % 10 == 0:
            await asyncio.sleep(0)
    
    return result

def checksum_matrix(matrix):
    """Calculate checksum of matrix"""
    total = sum(sum(row) for row in matrix)
    return hashlib.md5(str(total).encode()).hexdigest()

async def find_hash_collision(data, target_prefix):
    """Find hash collision with target prefix"""
    nonce = 0
    while True:
        test_string = f"{data}{nonce}"
        hash_result = hashlib.sha256(test_string.encode()).hexdigest()
        if hash_result.startswith(target_prefix):
            return {"nonce": nonce, "hash": hash_result}
        nonce += 1
        
        # Yield control every 1000 iterations to avoid blocking
        if nonce % 1000 == 0:
            await asyncio.sleep(0)
            
        if nonce > 100000:  # Prevent infinite loops in demo
            break
    return {"nonce": nonce, "hash": "timeout"}

async def antibot_challenge(challenge_type="proof_of_work", DIFFICULITY=3, request_count=1):
    """
    Main function to replace simulate_proof_of_work.
    Provides various anti-bot challenges with CPU-intensive operations.
    """
    if challenge_type == "proof_of_work":
        challenge = proof_of_work_challenge(DIFFICULITY)
        solution = await solve_proof_of_work(challenge["challenge_id"], challenge["target_prefix"])
        return {**challenge, "solution": solution}
        
    elif challenge_type == "image_classification":
        return await image_classification_challenge()
        
    elif challenge_type == "adaptive_puzzle":
        return await computational_puzzle_with_scaling(request_count)
        
    else:
        return proof_of_work_challenge(DIFFICULITY)