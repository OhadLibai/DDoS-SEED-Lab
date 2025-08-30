# CPU-Intensive Scenario Implementations

This directory (`shared/scenarios/`) contains six realistic CPU-intensive scenarios that can replace the `simulate_proof_of_work` function in the HTTP/2 Flood Attack Lab. Each scenario represents real-world services that legitimately perform heavy computation for unauthenticated users.

These scenarios are automatically available to the victim application (`shared/victim_app.py`) through environment variable configuration.

## Available Scenarios

### 1. CAPTCHA Generation/Validation (`captcha_scenario.py`)
**Real-world use case**: Websites generate complex CAPTCHAs to prevent automated abuse.

**CPU-intensive operations**:
- Visual CAPTCHA with image distortion, noise generation, and mathematical transformations
- Mathematical puzzle solving with varying complexity levels
- Audio CAPTCHA generation (simulated text-to-speech processing)
- Complex image filtering and post-processing

**Usage**:
```python
from scenarios.captcha_scenario import captcha_challenge

# Visual CAPTCHA with image manipulation
result = captcha_challenge("visual", complexity=3)

# Mathematical puzzle 
result = captcha_challenge("math", complexity=2)

# Audio CAPTCHA simulation
result = captcha_challenge("audio", complexity=4)
```

### 2. Rate Limiting/Anti-Bot Protection (`antibot_scenario.py`)
**Real-world use case**: Services implement computational challenges to prevent bot attacks.

**CPU-intensive operations**:
- Proof-of-work challenges with configurable DIFFICULITY
- Image classification simulation ("Select all traffic lights")
- Adaptive computational puzzles that scale with request frequency
- Prime factorization, Fibonacci calculations, matrix operations

**Usage**:
```python
from scenarios.antibot_scenario import antibot_challenge

# Proof-of-work challenge
result = antibot_challenge("proof_of_work", DIFFICULITY=4)

# Image classification challenge
result = antibot_challenge("image_classification")

# Adaptive puzzle that scales with requests
result = antibot_challenge("adaptive_puzzle", DIFFICULITY=3, request_count=50)
```

### 3. Content Preview/Search (`content_preview_scenario.py`)
**Real-world use case**: Search engines and content platforms process queries and generate previews.

**CPU-intensive operations**:
- Full-text search across large document databases with relevance scoring
- Image thumbnail generation with resize algorithms and compression
- Video preview generation with frame analysis and encoding
- PDF rendering and preview generation

**Usage**:
```python
from scenarios.content_preview_scenario import content_preview_challenge

# Full-text search with relevance scoring
result = content_preview_challenge("search", "artificial intelligence", complexity=3)

# Image thumbnail generation
result = content_preview_challenge("image_thumbnail", "42", complexity=2)

# Video preview with keyframe extraction
result = content_preview_challenge("video_preview", "123", complexity=4)
```

### 4. Cryptographic Operations (`crypto_scenario.py`)
**Real-world use case**: Secure services perform key exchange and certificate validation.

**CPU-intensive operations**:
- Diffie-Hellman key exchange with large prime generation
- X.509 certificate chain validation and verification
- SSL/TLS handshake simulation with RSA operations
- Cryptographically secure session token generation

**Usage**:
```python
from scenarios.crypto_scenario import cryptographic_challenge

# Diffie-Hellman key exchange
result = cryptographic_challenge("diffie_hellman", complexity=3)

# Certificate chain validation
result = cryptographic_challenge("certificate_chain", complexity=2)

# TLS handshake simulation
result = cryptographic_challenge("tls_handshake")
```

### 5. Real-World Web Services (`webservice_scenario.py`)
**Real-world use case**: Map services, weather APIs, and translation services.

**CPU-intensive operations**:
- Map tile generation with geographic calculations and feature rendering
- Routing algorithms with Dijkstra pathfinding and network analysis
- Weather data processing with statistical analysis and forecasting
- Language translation with tokenization and semantic analysis

**Usage**:
```python
from scenarios.webservice_scenario import webservice_challenge

# Map tile generation
result = webservice_challenge("map_tiles", "zoom_level=12")

# Route calculation between coordinates
result = webservice_challenge("routing", "New York to Boston")

# Weather forecast processing
result = webservice_challenge("weather", "San Francisco", complexity=3)

# Language translation
result = webservice_challenge("translation", "Hello world how are you?")
```

### 6. Gaming/Entertainment (`gaming_scenario.py`)
**Real-world use case**: Game servers generate content and perform matchmaking.

**CPU-intensive operations**:
- Sudoku puzzle generation with uniqueness validation
- Random maze generation using recursive backtracking
- Procedural dungeon generation with room placement and pathfinding
- Multiplayer matchmaking with compatibility algorithms

**Usage**:
```python
from scenarios.gaming_scenario import gaming_challenge

# Generate Sudoku puzzle
result = gaming_challenge("sudoku", DIFFICULITY=4)

# Create random maze
result = gaming_challenge("maze", DIFFICULITY=3, size=50)

# Generate procedural content
result = gaming_challenge("procedural", DIFFICULITY=2, size=30)

# Matchmaking simulation
result = gaming_challenge("matchmaking", size=100)
```

## Integration with HTTP/2 Flood Lab

### Automatic Integration
The scenarios are automatically integrated with the victim application (`shared/victim_app.py`) and can be selected using environment variables:

```bash
# Deploy with specific scenarios
SCENARIO=captcha ./local-deploy.sh part-A
SCENARIO=crypto DIFFICULITY=4 ./gcp-deploy.sh part-B
SCENARIO=gaming ./local-deploy.sh part-B
```

### Manual Integration Examples

```python
# In shared/victim_app.py - scenarios are loaded dynamically:
if SCENARIO == "captcha":
    from scenarios.captcha_scenario import captcha_challenge
    result = captcha_challenge("visual", DIFFICULITY)
elif SCENARIO == "crypto":
    from scenarios.crypto_scenario import cryptographic_challenge  
    result = cryptographic_challenge("diffie_hellman", DIFFICULITY)
```

### Multiple Endpoints

```python
@app.route('/captcha')
def captcha_endpoint():
    challenge_type = request.args.get('type', 'visual')
    complexity = int(request.args.get('complexity', '2'))
    result = captcha_challenge(challenge_type, complexity)
    return {"status": "success", "result": result}
```

### Adaptive Complexity

```python
@app.route('/adaptive')
def adaptive_endpoint():
    # Scale DIFFICULITY based on request frequency
    complexity = min(5, 2 + (request_count // 20))
    result = antibot_challenge("adaptive_puzzle", complexity, request_count)
    return {"status": "success", "result": result}
```

## Dependencies

All scenario dependencies are included in the main requirements file:

```bash
pip install -r ../requirements.txt
```

Scenario dependency breakdown:
- **CAPTCHA & Content scenarios**: Require `Pillow` for image processing
- **Cryptographic scenarios**: Require `cryptography` for secure operations  
- **Other scenarios**: Use only Python standard library (antibot, gaming, webservice)

## Performance Characteristics

Each scenario is designed to be CPU-intensive while remaining realistic:

- **CAPTCHA**: 0.1-2 seconds per request depending on complexity
- **Anti-Bot**: 0.05-5 seconds based on proof-of-work DIFFICULITY
- **Content**: 0.2-3 seconds for search/preview generation
- **Crypto**: 0.1-10 seconds for key operations
- **Web Services**: 0.3-5 seconds for complex service simulation
- **Gaming**: 0.1-8 seconds for procedural generation

## Defensive Security Focus

All scenarios implement **defensive security measures only**:
- ✅ CAPTCHA generation for bot prevention
- ✅ Anti-abuse computational challenges
- ✅ Legitimate content processing
- ✅ Standard cryptographic operations
- ✅ Real-world service simulation
- ✅ Gaming content generation

❌ **No offensive capabilities or malicious code generation**

## Choosing a Scenario

Select based on your testing needs:

- **CAPTCHA**: Test image processing and visual challenge handling
- **Anti-Bot**: Test adaptive DIFFICULITY and proof-of-work systems
- **Content**: Test search performance and media processing
- **Crypto**: Test cryptographic operation handling
- **Web Services**: Test real-world API simulation
- **Gaming**: Test algorithmic complexity and procedural generation

Each scenario can be tuned for different CPU load levels using the complexity parameter.