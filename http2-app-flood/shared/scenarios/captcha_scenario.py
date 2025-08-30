# scenarios/captcha_scenario.py

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import string
import io
import base64
import math
import asyncio

async def generate_visual_captcha(length=6, width=200, height=80):
    """
    Generate a complex visual CAPTCHA with distortion and noise.
    CPU-intensive operations include image manipulation, random transformations.
    """
    # Generate random text
    characters = string.ascii_uppercase + string.digits
    captcha_text = ''.join(random.choices(characters, k=length))
    
    # Create image with background
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Add background noise
    for i in range(1000):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        # Yield control every 100 points to avoid blocking
        if i % 100 == 0:
            await asyncio.sleep(0)
    
    # Add noise lines
    for _ in range(20):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(0, 128), random.randint(0, 128), random.randint(0, 128)), width=1)
    
    # Draw text with random positioning and rotation
    try:
        font_size = 30
        font = ImageFont.load_default()  # Using default font for compatibility
    except:
        font = None
    
    x_start = 10
    for i, char in enumerate(captcha_text):
        x = x_start + i * 25 + random.randint(-5, 5)
        y = 20 + random.randint(-10, 10)
        
        # Random color for each character
        color = (random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))
        draw.text((x, y), char, font=font, fill=color)
    
    # Apply distortion using mathematical transformations
    img_array = list(img.getdata())
    distorted_array = []
    
    for y in range(height):
        for x in range(width):
            # Apply sine wave distortion
            new_x = x + int(5 * math.sin(y / 10.0))
            new_y = y + int(3 * math.cos(x / 15.0))
            
            # Ensure coordinates are within bounds
            new_x = max(0, min(width-1, new_x))
            new_y = max(0, min(height-1, new_y))
            
            original_index = y * width + x
            distorted_array.append(img_array[original_index])
        
        # Yield control every row to avoid blocking
        if y % 10 == 0:
            await asyncio.sleep(0)
    
    distorted_img = Image.new('RGB', (width, height))
    distorted_img.putdata(distorted_array)
    
    # Apply blur for additional complexity
    distorted_img = distorted_img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    return captcha_text, distorted_img

async def solve_mathematical_puzzle(complexity=3):
    """
    Generate and solve mathematical puzzles of varying complexity.
    """
    if complexity == 1:
        # Simple arithmetic
        a = random.randint(1, 100)
        b = random.randint(1, 100)
        operation = random.choice(['+', '-', '*'])
        if operation == '+':
            result = a + b
        elif operation == '-':
            result = a - b
        else:  # multiplication
            result = a * b
        puzzle = f"{a} {operation} {b}"
        
    elif complexity == 2:
        # Multiple operations
        a = random.randint(1, 50)
        b = random.randint(1, 50)
        c = random.randint(1, 10)
        result = (a + b) * c
        puzzle = f"({a} + {b}) * {c}"
        
    else:  # complexity == 3
        # Complex mathematical operations
        base = random.randint(2, 10)
        exponent = random.randint(2, 4)
        addend = random.randint(1, 100)
        
        # CPU-intensive calculation
        power_result = 1
        for i in range(exponent):
            power_result *= base
            await asyncio.sleep(0)  # Yield control during computation
        
        result = power_result + addend
        puzzle = f"{base}^{exponent} + {addend}"
    
    return puzzle, result

async def generate_audio_captcha_text(text):
    """
    Simulate audio CAPTCHA generation (text-to-speech simulation).
    In real implementation, this would involve complex audio processing.
    """
    # Simulate CPU-intensive audio processing
    audio_data = []
    for char in text:
        # Simulate frequency generation for each character
        char_freq = ord(char) * 100  # Simple frequency mapping
        
        # Generate simulated audio samples (computationally intensive)
        for i in range(8000):  # Simulate 8kHz sample rate for 1 second
            sample = int(32767 * math.sin(2 * math.pi * char_freq * i / 8000))
            audio_data.append(sample)
            
            # Yield control every 1000 samples to avoid blocking
            if i % 1000 == 0:
                await asyncio.sleep(0)
    
    # Simulate audio effects and noise reduction
    processed_audio = []
    for i, sample in enumerate(audio_data):
        # Apply noise reduction (CPU-intensive filtering)
        if i >= 2 and i < len(audio_data) - 2:
            filtered_sample = (audio_data[i-2] + audio_data[i-1] + sample + 
                             audio_data[i+1] + audio_data[i+2]) // 5
        else:
            filtered_sample = sample
        processed_audio.append(filtered_sample)
        
        # Yield control every 1000 samples to avoid blocking
        if i % 1000 == 0:
            await asyncio.sleep(0)
    
    return f"Audio CAPTCHA generated for: {text} ({len(processed_audio)} samples)"

async def captcha_challenge(challenge_type="visual", complexity=2):
    """
    Main function to replace simulate_proof_of_work.
    Generates different types of CAPTCHA challenges.
    """
    if challenge_type == "visual":
        captcha_text, captcha_img = await generate_visual_captcha()
        
        # Convert image to base64 for web display
        img_buffer = io.BytesIO()
        captcha_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return {
            "type": "visual_captcha",
            "challenge": img_base64,
            "expected_answer": captcha_text,
            "format": "base64_png"
        }
        
    elif challenge_type == "math":
        puzzle, answer = await solve_mathematical_puzzle(complexity)
        return {
            "type": "mathematical_captcha",
            "challenge": f"Solve: {puzzle}",
            "expected_answer": str(answer),
            "format": "text"
        }
        
    elif challenge_type == "audio":
        text_length = 4 + complexity
        characters = string.ascii_uppercase + string.digits
        audio_text = ''.join(random.choices(characters, k=text_length))
        audio_info = await generate_audio_captcha_text(audio_text)
        
        return {
            "type": "audio_captcha",
            "challenge": audio_info,
            "expected_answer": audio_text,
            "format": "simulated_audio"
        }
    
    else:
        # Default to visual
        return await captcha_challenge("visual", complexity)