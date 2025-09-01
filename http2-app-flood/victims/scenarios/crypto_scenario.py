# scenarios/crypto_scenario.py

import hashlib
import hmac
import math
import random
import time
import os
import asyncio
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import secrets

async def diffie_hellman_key_exchange(key_size=2048):
    """
    Simulate CPU-intensive Diffie-Hellman key exchange preparation.
    Generate large prime numbers and perform modular exponentiation.
    """
    start_time = time.time()
    
    # Generate large prime numbers (CPU-intensive)
    p = generate_large_prime(key_size // 8)  # Large prime modulus
    g = find_primitive_root(p)  # Generator (primitive root)
    
    # Generate private keys for both parties
    private_key_a = random.randint(2, p - 2)
    private_key_b = random.randint(2, p - 2)
    
    # Calculate public keys (CPU-intensive modular exponentiation)
    public_key_a = pow(g, private_key_a, p)
    public_key_b = pow(g, private_key_b, p)
    
    # Calculate shared secret (CPU-intensive)
    shared_secret_a = pow(public_key_b, private_key_a, p)
    shared_secret_b = pow(public_key_a, private_key_b, p)
    
    # Verify shared secrets match
    assert shared_secret_a == shared_secret_b
    
    end_time = time.time()
    
    return {
        "algorithm": "Diffie-Hellman",
        "key_size_bits": key_size,
        "prime_modulus_p": str(p),
        "generator_g": g,
        "public_key_a": str(public_key_a),
        "public_key_b": str(public_key_b),
        "shared_secret": str(shared_secret_a),
        "computation_time": end_time - start_time,
        "operations_performed": ["prime_generation", "primitive_root_finding", "modular_exponentiation"]
    }

def generate_large_prime(byte_length):
    """
    Generate a large prime number (CPU-intensive).
    """
    while True:
        # Generate random odd number
        candidate = random.getrandbits(byte_length * 8)
        if candidate % 2 == 0:
            candidate += 1
        
        # Test for primality - scale rounds based on key size for better performance
        rounds = min(20, max(3, byte_length // 8))  # 3-20 rounds based on key size
        if miller_rabin_test(candidate, rounds):
            return candidate

def miller_rabin_test(n, k):
    """
    Miller-Rabin primality test (CPU-intensive).
    """
    if n == 2 or n == 3:
        return True
    if n < 2 or n % 2 == 0:
        return False
    
    # Write n-1 as d * 2^r
    r = 0
    d = n - 1
    while d % 2 == 0:
        d //= 2
        r += 1
    
    # Perform k rounds of testing
    for _ in range(k):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        
        if x == 1 or x == n - 1:
            continue
        
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    
    return True

def find_primitive_root(p):
    """
    Find a primitive root modulo p (optimized for performance).
    """
    if p == 2:
        return 1
    
    # For performance, use a simplified approach with small candidates
    # This is sufficient for educational purposes
    candidates = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
    phi = p - 1
    
    for g in candidates:
        if g >= p:
            continue
        # Quick primality test: if g^((p-1)/2) != 1 (mod p), likely primitive
        if pow(g, phi // 2, p) != 1:
            return g
    
    # If no small candidate works, return 2 as safe fallback
    return 2

async def certificate_validation_chain(chain_length=5, complexity=1):
    """
    Simulate CPU-intensive certificate chain validation.
    """
    start_time = time.time()
    
    certificates = []
    total_verification_time = 0
    
    # Generate certificate chain
    for i in range(chain_length):
        # Generate RSA key pair (CPU-intensive)
        key_generation_start = time.time()
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=1024
        )
        public_key = private_key.public_key()
        key_generation_time = time.time() - key_generation_start
        
        # Simulate certificate data
        cert_data = {
            "level": i,
            "subject": f"CN=Certificate-{i}",
            "issuer": f"CN=Certificate-{i-1}" if i > 0 else "CN=Root-CA",
            "serial_number": random.randint(1000000, 9999999),
            "key_size": 1024,
            "public_key": public_key,
            "private_key": private_key if i == chain_length - 1 else None  # Only leaf cert
        }
        
        # Simulate signature verification (CPU-intensive)
        verification_start = time.time()
        test_data = f"Certificate data for level {i}".encode()
        
        if i == 0:  # Root certificate (self-signed)
            signature = private_key.sign(
                test_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Verify self-signature
            try:
                public_key.verify(
                    signature,
                    test_data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                cert_data["signature_valid"] = True
            except:
                cert_data["signature_valid"] = False
        else:
            # Sign with parent's private key
            parent_key = certificates[i-1]["private_key"]
            if parent_key:
                signature = parent_key.sign(
                    test_data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                cert_data["signature"] = signature
                cert_data["signature_valid"] = True
            else:
                cert_data["signature_valid"] = False
        
        verification_time = time.time() - verification_start
        total_verification_time += verification_time
        
        cert_data["key_generation_time"] = key_generation_time
        cert_data["verification_time"] = verification_time
        
        certificates.append(cert_data)
    
    # Perform full chain validation (CPU-intensive)
    chain_validation_start = time.time()
    chain_valid = True
    
    for i in range(1, len(certificates)):
        current_cert = certificates[i]
        parent_cert = certificates[i-1]
        
        # Simulate complex validation checks
        validation_checks = [
            "signature_verification",
            "validity_period_check",
            "key_usage_validation",
            "certificate_policies_check",
            "crl_checking",
            "ocsp_validation"
        ]
        
        for check in validation_checks:
            # Simulate CPU work for each validation step
            for _ in range(100 * complexity):
                validation_work = random.randint(1, 100)
        
        if not current_cert.get("signature_valid", False):
            chain_valid = False
            break
    
    chain_validation_time = time.time() - chain_validation_start
    end_time = time.time()
    
    return {
        "algorithm": "X.509 Certificate Chain Validation",
        "chain_length": chain_length,
        "certificates": [{
            "level": cert["level"],
            "subject": cert["subject"],
            "issuer": cert["issuer"],
            "serial_number": cert["serial_number"],
            "key_size": cert["key_size"],
            "signature_valid": cert["signature_valid"],
            "key_generation_time": cert["key_generation_time"],
            "verification_time": cert["verification_time"]
        } for cert in certificates],
        "chain_valid": chain_valid,
        "total_computation_time": end_time - start_time,
        "key_generation_time": sum(cert["key_generation_time"] for cert in certificates),
        "signature_verification_time": total_verification_time,
        "chain_validation_time": chain_validation_time,
        "operations_performed": ["key_generation", "digital_signatures", "chain_validation"]
    }

async def ssl_tls_handshake_simulation(complexity=1):
    """
    Simulate CPU-intensive SSL/TLS handshake computations.
    """
    start_time = time.time()
    
    # 1. Certificate generation (CPU-intensive)
    cert_start = time.time()
    # Scale RSA key size with complexity for better performance
    rsa_key_size = 1024 + (complexity * 512)  # 1024-3072 bits based on complexity
    server_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=rsa_key_size
    )
    server_public_key = server_private_key.public_key()
    cert_generation_time = time.time() - cert_start
    
    # 2. Client random and server random generation
    client_random = os.urandom(32)
    server_random = os.urandom(32)
    
    # 3. Pre-master secret generation
    pre_master_secret = os.urandom(48)
    
    # 4. RSA encryption of pre-master secret (CPU-intensive)
    encryption_start = time.time()
    encrypted_pre_master = server_public_key.encrypt(
        pre_master_secret,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    encryption_time = time.time() - encryption_start
    
    # 5. RSA decryption (CPU-intensive)
    decryption_start = time.time()
    decrypted_pre_master = server_private_key.decrypt(
        encrypted_pre_master,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    decryption_time = time.time() - decryption_start
    
    assert pre_master_secret == decrypted_pre_master
    
    # 6. Master secret derivation (CPU-intensive)
    master_secret_start = time.time()
    
    # Simulate TLS PRF (Pseudo-Random Function)
    seed = b"master secret" + client_random + server_random
    master_secret = pbkdf2_hmac_custom(pre_master_secret, seed, 1000, 48)
    
    master_secret_time = time.time() - master_secret_start
    
    # 7. Key derivation (CPU-intensive)
    key_derivation_start = time.time()
    
    key_material_seed = b"key expansion" + server_random + client_random
    key_material = pbkdf2_hmac_custom(master_secret, key_material_seed, 5000, 136)
    
    # Split key material into individual keys
    client_mac_key = key_material[:20]
    server_mac_key = key_material[20:40]
    client_encryption_key = key_material[40:56]
    server_encryption_key = key_material[56:72]
    client_iv = key_material[72:88]
    server_iv = key_material[88:104]
    
    key_derivation_time = time.time() - key_derivation_start
    
    # 8. Finished message MAC computation (CPU-intensive)
    mac_start = time.time()
    
    handshake_messages = b"ClientHello" + b"ServerHello" + b"Certificate" + b"ServerKeyExchange"
    finished_mac = hmac.new(
        client_mac_key,
        handshake_messages,
        hashlib.sha256
    ).digest()
    
    mac_time = time.time() - mac_start
    
    end_time = time.time()
    
    return {
        "protocol": "TLS 1.2 Handshake Simulation",
        "key_exchange": "RSA",
        "cipher_suite": "TLS_RSA_WITH_AES_128_CBC_SHA256",
        "server_key_size": rsa_key_size,
        "client_random": client_random.hex(),
        "server_random": server_random.hex(),
        "master_secret": master_secret.hex(),
        "encryption_keys": {
            "client_encryption_key": client_encryption_key.hex(),
            "server_encryption_key": server_encryption_key.hex(),
            "client_mac_key": client_mac_key.hex(),
            "server_mac_key": server_mac_key.hex()
        },
        "timing_breakdown": {
            "certificate_generation": cert_generation_time,
            "rsa_encryption": encryption_time,
            "rsa_decryption": decryption_time,
            "master_secret_derivation": master_secret_time,
            "key_derivation": key_derivation_time,
            "mac_computation": mac_time
        },
        "total_computation_time": end_time - start_time,
        "operations_performed": ["key_generation", "rsa_encrypt_decrypt", "key_derivation", "hmac_computation"]
    }

def pbkdf2_hmac_custom(password, salt, iterations, key_length):
    """
    Custom PBKDF2-HMAC implementation for demonstration (CPU-intensive).
    """
    result = b""
    i = 1
    
    while len(result) < key_length:
        u = salt + i.to_bytes(4, 'big')
        
        for _ in range(iterations):
            u = hmac.new(password, u, hashlib.sha256).digest()
        
        result += u
        i += 1
    
    return result[:key_length]

async def session_token_generation(entropy_bits=256, token_count=10, complexity=1):
    """
    Generate cryptographically secure session tokens with high entropy.
    CPU-intensive random number generation and entropy collection.
    """
    start_time = time.time()
    
    tokens = []
    total_entropy_collected = 0
    
    for i in range(token_count):
        token_start = time.time()
        
        # Collect entropy from multiple sources (CPU-intensive)
        entropy_sources = []
        
        # System entropy
        system_entropy = os.urandom(entropy_bits // 8)
        entropy_sources.append(system_entropy)
        
        # Time-based entropy
        time_entropy = hashlib.sha256(str(time.time()).encode()).digest()
        entropy_sources.append(time_entropy)
        
        # Process-based entropy (CPU-intensive)
        process_entropy = b""
        for _ in range(100 * complexity):
            process_value = random.randint(0, 2**32 - 1)
            process_entropy += hashlib.sha256(str(process_value).encode()).digest()
        entropy_sources.append(process_entropy[:32])
        
        # Combine entropy sources
        combined_entropy = b"".join(entropy_sources)
        
        # Apply key stretching (CPU-intensive) - scale with complexity
        iterations = 1000 + (complexity * 2000)  # 1000-11000 iterations based on complexity
        stretched_key = pbkdf2_hmac_custom(
            combined_entropy,
            b"session_token_salt",
            iterations,
            64
        )
        
        # Generate final token
        token_hash = hashlib.sha256(stretched_key).hexdigest()
        
        token_end = time.time()
        
        tokens.append({
            "token_id": i + 1,
            "token": token_hash,
            "entropy_bits": entropy_bits,
            "generation_time": token_end - token_start,
            "entropy_sources_used": ["system", "time", "process"]
        })
        
        total_entropy_collected += entropy_bits
    
    end_time = time.time()
    
    return {
        "algorithm": "Cryptographically Secure Token Generation",
        "entropy_per_token": entropy_bits,
        "tokens_generated": token_count,
        "total_entropy_bits": total_entropy_collected,
        "tokens": tokens,
        "average_generation_time": (end_time - start_time) / token_count,
        "total_computation_time": end_time - start_time,
        "operations_performed": ["entropy_collection", "key_stretching", "secure_hashing"]
    }

async def cryptographic_challenge(operation="diffie_hellman", complexity=2, count=1):
    """
    Main function to replace simulate_default_cpu_work.
    Provides various CPU-intensive cryptographic operations.
    """
    if operation == "diffie_hellman":
        # Scale key size more reasonably for low workloads
        key_size = 256 + (complexity * 256)
        return await diffie_hellman_key_exchange(key_size)
        
    elif operation == "certificate_chain":
        chain_length = max(3, complexity * 2)
        return await certificate_validation_chain(chain_length, complexity)
        
    elif operation == "tls_handshake":
        return await ssl_tls_handshake_simulation(complexity)
        
    elif operation == "session_tokens":
        entropy_bits = 128 + (complexity * 64)
        token_count = max(1, count)
        return await session_token_generation(entropy_bits, token_count, complexity)
        
    else:
        # Default to Diffie-Hellman
        return await diffie_hellman_key_exchange(2048)