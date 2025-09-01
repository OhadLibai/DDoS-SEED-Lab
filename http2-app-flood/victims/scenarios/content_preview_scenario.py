# scenarios/content_preview_scenario.py

import random
import string
import hashlib
import time
import re
import asyncio
from collections import defaultdict

# Simulate a large database of content
SAMPLE_DOCUMENTS = [
    {"id": i, "title": f"Document {i}", "content": ' '.join([
        ''.join(random.choices(string.ascii_lowercase + ' ', k=random.randint(50, 200)))
        for _ in range(random.randint(10, 25))
    ]), "category": random.choice(["technology", "science", "business", "health", "education"])}
    for i in range(5000)
]

SAMPLE_IMAGES = [
    {"id": i, "filename": f"image_{i}.jpg", "width": random.randint(100, 2000), 
     "height": random.randint(100, 2000), "size_bytes": random.randint(50000, 5000000)}
    for i in range(2500)
]

SAMPLE_VIDEOS = [
    {"id": i, "filename": f"video_{i}.mp4", "duration": random.randint(30, 1800),
     "resolution": random.choice(["720p", "1080p", "4K"]), "size_bytes": random.randint(1000000, 500000000)}
    for i in range(500)
]

async def full_text_search(query, max_results=50):
    """
    Simulate CPU-intensive full-text search across large document database.
    Includes complex relevance scoring and result ranking.
    """
    start_time = time.time()
    query_terms = query.lower().split()
    results = []
    
    # Search through all documents (CPU-intensive)
    for i, doc in enumerate(SAMPLE_DOCUMENTS):
        if i % 100 == 0:
            await asyncio.sleep(0)  # Yield control periodically
        content_lower = doc['content'].lower()
        title_lower = doc['title'].lower()
        
        # Calculate relevance score (complex computation)
        relevance_score = 0
        
        # Term frequency calculation
        for term in query_terms:
            # Count occurrences in content
            content_matches = len(re.findall(r'\b' + re.escape(term) + r'\b', content_lower))
            title_matches = len(re.findall(r'\b' + re.escape(term) + r'\b', title_lower))
            
            # Weight title matches higher
            relevance_score += content_matches + (title_matches * 3)
            
            # Proximity scoring (CPU-intensive)
            if len(query_terms) > 1:
                proximity_bonus = await calculate_proximity_score(content_lower, query_terms)
                relevance_score += proximity_bonus
        
        if relevance_score > 0:
            # Additional ranking factors (simulate complex algorithms)
            category_boost = 1.2 if doc['category'] in ['technology', 'science'] else 1.0
            length_penalty = max(0.5, 1.0 - (len(doc['content']) / 10000))
            
            final_score = relevance_score * category_boost * length_penalty
            
            results.append({
                "document_id": doc['id'],
                "title": doc['title'],
                "category": doc['category'],
                "relevance_score": final_score,
                "content_snippet": extract_snippet(doc['content'], query_terms),
                "content_length": len(doc['content'])
            })
    
    # Sort by relevance (CPU-intensive for large result sets)
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    end_time = time.time()
    
    return {
        "query": query,
        "total_results": len(results),
        "results": results[:max_results],
        "search_time": end_time - start_time,
        "documents_processed": len(SAMPLE_DOCUMENTS),
        "ranking_algorithm": "tf-idf_with_proximity_and_category_boost"
    }

async def calculate_proximity_score(content, query_terms):
    """
    Calculate proximity score for query terms in content (CPU-intensive).
    """
    proximity_score = 0
    words = content.split()
    
    # Find positions of all query terms
    term_positions = defaultdict(list)
    for i, word in enumerate(words):
        for term in query_terms:
            if term in word.lower():
                term_positions[term].append(i)
    
    # Calculate proximity bonuses (computationally expensive)
    for i, term1 in enumerate(query_terms):
        for j, term2 in enumerate(query_terms[i+1:], i+1):
            if term1 in term_positions and term2 in term_positions:
                for pos1 in term_positions[term1]:
                    for pos2 in term_positions[term2]:
                        distance = abs(pos1 - pos2)
                        if distance <= 10:  # Words within 10 positions
                            proximity_score += 10 - distance
    
    return proximity_score

async def extract_snippet(content, query_terms, snippet_length=150):
    """
    Extract relevant snippet from content around query terms.
    """
    content_lower = content.lower()
    query_lower = [term.lower() for term in query_terms]
    
    # Find best position for snippet
    best_pos = 0
    max_term_density = 0
    
    # Sliding window to find area with most query terms
    window_size = snippet_length
    for i in range(0, len(content) - window_size, 20):
        window = content_lower[i:i + window_size]
        term_count = sum(window.count(term) for term in query_lower)
        if term_count > max_term_density:
            max_term_density = term_count
            best_pos = i
    
    snippet = content[best_pos:best_pos + snippet_length]
    if best_pos > 0:
        snippet = "..." + snippet
    if best_pos + snippet_length < len(content):
        snippet = snippet + "..."
    
    return snippet

async def generate_image_thumbnail(image_id, width=150, height=150):
    """
    Simulate CPU-intensive image thumbnail generation with various processing steps.
    """
    if image_id >= len(SAMPLE_IMAGES):
        return {"error": "Image not found"}
    
    image_info = SAMPLE_IMAGES[image_id]
    start_time = time.time()
    
    # Simulate complex image processing operations
    
    # 1. Image loading simulation (I/O intensive)
    loading_time = image_info['size_bytes'] / 10000000  # Simulate loading based on size
    time.sleep(min(0.1, loading_time))
    
    # 2. Resize algorithm simulation (CPU-intensive)
    original_width = image_info['width']
    original_height = image_info['height']
    
    # Calculate aspect ratio preserving dimensions
    aspect_ratio = original_width / original_height
    if aspect_ratio > 1:
        new_width = width
        new_height = int(width / aspect_ratio)
    else:
        new_height = height
        new_width = int(height * aspect_ratio)
    
    # Simulate pixel processing (very CPU-intensive)
    pixels_processed = 0
    for y in range(new_height):
        for x in range(new_width):
            # Simulate bilinear interpolation
            src_x = x * (original_width / new_width)
            src_y = y * (original_height / new_height)
            
            # Complex color interpolation calculation
            interpolated_value = (src_x * 255 + src_y * 255) % 255
            pixels_processed += 1
    
    # 3. Image optimization (CPU-intensive)
    compression_work = 0
    for _ in range(500): # Simulate compression algorithm work
        compression_work += random.randint(1, 100)
    
    # 4. Format conversion simulation
    output_size = int(image_info['size_bytes'] * 0.1)  # Assume 90% compression
    
    end_time = time.time()
    
    return {
        "image_id": image_id,
        "original_filename": image_info['filename'],
        "original_dimensions": f"{original_width}x{original_height}",
        "thumbnail_dimensions": f"{new_width}x{new_height}",
        "original_size_bytes": image_info['size_bytes'],
        "thumbnail_size_bytes": output_size,
        "pixels_processed": pixels_processed,
        "compression_ratio": f"{((image_info['size_bytes'] - output_size) / image_info['size_bytes'] * 100):.1f}%",
        "processing_time": end_time - start_time,
        "operations_performed": ["resize", "interpolation", "compression", "format_conversion"]
    }

async def generate_video_preview(video_id, preview_duration=30):
    """
    Simulate CPU-intensive video preview generation.
    """
    if video_id >= len(SAMPLE_VIDEOS):
        return {"error": "Video not found"}
    
    video_info = SAMPLE_VIDEOS[video_id]
    start_time = time.time()
    
    # Simulate video processing operations
    total_frames = video_info['duration'] * 30  # Assume 30 FPS
    preview_frames = preview_duration * 30
    
    # 1. Video decoding simulation (CPU-intensive)
    decoded_frames = 0
    for frame_num in range(preview_frames):
        # Simulate complex video decoding
        frame_complexity = random.randint(1000, 10000)
        decoding_work = 0
        for _ in range(frame_complexity // 100):
            decoding_work += random.randint(1, 255)
        decoded_frames += 1
    
    # 2. Frame analysis for preview selection (CPU-intensive)
    selected_keyframes = []
    frame_scores = []
    
    for i in range(preview_frames):
        # Simulate content analysis for each frame
        content_score = 0
        for _ in range(250):  # Analyze 250 regions per frame
            # Simulate edge detection, color analysis, etc.
            edge_value = random.randint(0, 255)
            color_value = random.randint(0, 255)
            content_score += (edge_value + color_value) / 2
        
        frame_scores.append({
            "frame_number": i,
            "content_score": content_score,
            "timestamp": i / 30.0
        })
        
        # Select keyframes based on content score
        if content_score > 50000:  # High content score threshold
            selected_keyframes.append(i)
    
    # 3. Video encoding for preview (CPU-intensive)
    encoding_complexity = len(selected_keyframes) * 1000
    encoded_bytes = 0
    
    for _ in range(encoding_complexity):
        # Simulate H.264 encoding work
        encoded_bytes += random.randint(1, 1000)
    
    # 4. Audio processing (CPU-intensive)
    audio_samples = preview_duration * 44100  # 44.1kHz sample rate
    processed_audio_samples = 0
    
    for _ in range(audio_samples // 1000):  # Process in chunks
        # Simulate audio compression and normalization
        audio_work = random.randint(1, 1000)
        processed_audio_samples += audio_work
    
    end_time = time.time()
    
    return {
        "video_id": video_id,
        "original_filename": video_info['filename'],
        "original_duration": video_info['duration'],
        "original_resolution": video_info['resolution'],
        "original_size_bytes": video_info['size_bytes'],
        "preview_duration": preview_duration,
        "total_frames_analyzed": preview_frames,
        "keyframes_selected": len(selected_keyframes),
        "keyframe_timestamps": [f"{frame/30:.2f}s" for frame in selected_keyframes[:10]],
        "encoded_preview_size": encoded_bytes,
        "audio_samples_processed": processed_audio_samples,
        "processing_time": end_time - start_time,
        "compression_ratio": f"{(encoded_bytes / video_info['size_bytes'] * 100):.3f}%"
    }

async def generate_pdf_preview(document_text, page_count=None):
    """
    Simulate CPU-intensive PDF preview rendering.
    """
    if page_count is None:
        page_count = len(document_text) // 2000 + 1  # Estimate pages
    
    start_time = time.time()
    
    rendered_pages = []
    total_elements_rendered = 0
    
    for page_num in range(page_count):
        page_start = page_num * 2000
        page_end = min((page_num + 1) * 2000, len(document_text))
        page_content = document_text[page_start:page_end]
        
        # Simulate text rendering (CPU-intensive)
        elements_on_page = 0
        for char in page_content:
            # Simulate font rendering, kerning, positioning
            char_complexity = ord(char) % 10
            for _ in range(char_complexity):
                font_calculation = random.randint(1, 100)
            elements_on_page += 1
        
        # Simulate layout calculations
        line_breaks = page_content.count('\n') + page_content.count(' ') // 10
        layout_complexity = line_breaks * 50
        
        for _ in range(layout_complexity):
            positioning_work = random.randint(1, 50)
        
        # Simulate page rendering to image
        page_pixels = 595 * 842  # A4 page at 72 DPI
        rendered_pixels = 0
        
        for _ in range(page_pixels // 1000):  # Render in chunks
            pixel_work = random.randint(1, 255)
            rendered_pixels += pixel_work
        
        total_elements_rendered += elements_on_page
        
        rendered_pages.append({
            "page_number": page_num + 1,
            "characters": len(page_content),
            "elements_rendered": elements_on_page,
            "layout_operations": layout_complexity,
            "pixels_rendered": rendered_pixels
        })
    
    end_time = time.time()
    
    return {
        "document_type": "PDF",
        "total_pages": page_count,
        "total_characters": len(document_text),
        "total_elements_rendered": total_elements_rendered,
        "pages_processed": len(rendered_pages),
        "processing_time": end_time - start_time,
        "average_time_per_page": (end_time - start_time) / page_count,
        "rendered_pages": rendered_pages[:5],  # Show first 5 pages
        "operations_performed": ["text_rendering", "layout_calculation", "page_composition", "image_conversion"]
    }

async def content_preview_challenge(content_type="search", query_or_id="", complexity=2):
    """
    Main function to replace simulate_default_cpu_work.
    Provides CPU-intensive content processing and preview generation.
    """
    if content_type == "search":
        search_query = query_or_id or "technology artificial intelligence"
        max_results = 10 + (complexity * 20)
        return await full_text_search(search_query, max_results)
        
    elif content_type == "image_thumbnail":
        image_id = int(query_or_id) if query_or_id.isdigit() else random.randint(0, len(SAMPLE_IMAGES)-1)
        thumbnail_size = 100 + (complexity * 50)
        return await generate_image_thumbnail(image_id, thumbnail_size, thumbnail_size)
        
    elif content_type == "video_preview":
        video_id = int(query_or_id) if query_or_id.isdigit() else random.randint(0, len(SAMPLE_VIDEOS)-1)
        preview_duration = 15 + (complexity * 15)
        return await generate_video_preview(video_id, preview_duration)
        
    elif content_type == "pdf_preview":
        document_text = query_or_id if query_or_id else ' '.join([
            ''.join(random.choices(string.ascii_letters + ' .,\n', k=1000))
            for _ in range(complexity * 5)
        ])
        return await generate_pdf_preview(document_text)
        
    else:
        # Default to search
        return await full_text_search("default search query", 50)