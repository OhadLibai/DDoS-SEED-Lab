# scenarios/webservice_scenario.py

import random
import math
import time
import hashlib
import asyncio
from PIL import Image, ImageDraw, ImageOps
import io
import base64

async def map_tile_generation(zoom_level=10, tile_x=512, tile_y=512):
    """
    Simulate CPU-intensive map tile generation and routing calculations.
    """
    start_time = time.time()
    
    # Map tile parameters
    tile_size = 256
    earth_circumference = 40075016.686  # meters
    
    # Calculate geographic bounds for this tile (CPU-intensive)
    resolution = earth_circumference / (2 ** zoom_level)
    left_longitude = (tile_x * tile_size * resolution) - (earth_circumference / 2)
    right_longitude = ((tile_x + 1) * tile_size * resolution) - (earth_circumference / 2)
    
    # Convert to degrees
    left_lon_deg = (left_longitude / earth_circumference) * 360
    right_lon_deg = (right_longitude / earth_circumference) * 360
    
    # Generate tile image with geographic features (CPU-intensive)
    img = Image.new('RGB', (tile_size, tile_size), color=(135, 206, 235))  # Sky blue
    draw = ImageDraw.Draw(img)
    
    # Generate terrain features based on tile coordinates
    feature_count = 0
    
    # Generate roads (CPU-intensive path calculation)
    road_count = random.randint(2, 8)
    for i in range(road_count):
        # Calculate road path using complex algorithms
        start_x = random.randint(0, tile_size)
        start_y = random.randint(0, tile_size)
        
        # Generate curved road using mathematical functions
        road_points = []
        for t in range(0, 100):
            curve_param = t / 100.0
            # Complex curve calculation (CPU-intensive)
            x = start_x + int(50 * math.sin(curve_param * math.pi * 2) * math.cos(curve_param * 3))
            y = start_y + int(50 * math.cos(curve_param * math.pi) * math.sin(curve_param * 2))
            
            # Ensure within bounds
            x = max(0, min(tile_size - 1, x))
            y = max(0, min(tile_size - 1, y))
            
            road_points.append((x, y))
        
        # Draw road
        if len(road_points) > 1:
            for j in range(len(road_points) - 1):
                draw.line([road_points[j], road_points[j + 1]], fill=(64, 64, 64), width=3)
        
        feature_count += 1
    
    # Generate buildings (CPU-intensive)
    building_count = random.randint(5, 20)
    for i in range(building_count):
        # Calculate building placement and size
        building_x = random.randint(0, tile_size - 20)
        building_y = random.randint(0, tile_size - 20)
        building_width = random.randint(10, 30)
        building_height = random.randint(10, 40)
        
        # Complex building shape generation
        building_color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        
        # Draw building with shadow (CPU work)
        shadow_offset = 2
        draw.rectangle(
            [(building_x + shadow_offset, building_y + shadow_offset), 
             (building_x + building_width + shadow_offset, building_y + building_height + shadow_offset)],
            fill=(50, 50, 50)
        )
        draw.rectangle(
            [(building_x, building_y), (building_x + building_width, building_y + building_height)],
            fill=building_color
        )
        
        feature_count += 1
    
    # Generate water features (CPU-intensive)
    water_features = random.randint(0, 3)
    for i in range(water_features):
        # Generate water body using complex mathematical curves
        center_x = random.randint(50, tile_size - 50)
        center_y = random.randint(50, tile_size - 50)
        
        water_points = []
        for angle in range(0, 360, 10):
            # Complex water boundary calculation
            radius = 20 + 10 * math.sin(angle * math.pi / 180 * 3)
            x = center_x + int(radius * math.cos(angle * math.pi / 180))
            y = center_y + int(radius * math.sin(angle * math.pi / 180))
            water_points.append((x, y))
        
        draw.polygon(water_points, fill=(100, 150, 255))
        feature_count += 1
    
    # Apply post-processing filters (CPU-intensive)
    processing_start = time.time()
    
    # Convert image for processing
    img_array = list(img.getdata())
    processed_array = []
    
    # Apply noise reduction filter
    for y in range(tile_size):
        for x in range(tile_size):
            current_pixel = img_array[y * tile_size + x]
            
            # Average with neighboring pixels (blur effect)
            neighbors = []
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < tile_size and 0 <= ny < tile_size:
                        neighbors.append(img_array[ny * tile_size + nx])
            
            if neighbors:
                avg_r = sum(p[0] for p in neighbors) // len(neighbors)
                avg_g = sum(p[1] for p in neighbors) // len(neighbors)
                avg_b = sum(p[2] for p in neighbors) // len(neighbors)
                processed_array.append((avg_r, avg_g, avg_b))
            else:
                processed_array.append(current_pixel)
    
    processed_img = Image.new('RGB', (tile_size, tile_size))
    processed_img.putdata(processed_array)
    
    processing_time = time.time() - processing_start
    
    # Convert to base64 for transmission
    img_buffer = io.BytesIO()
    processed_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    end_time = time.time()
    
    return {
        "service": "Map Tile Generation",
        "tile_coordinates": {"x": tile_x, "y": tile_y, "zoom": zoom_level},
        "geographic_bounds": {
            "left_longitude": left_lon_deg,
            "right_longitude": right_lon_deg
        },
        "tile_size": tile_size,
        "features_generated": feature_count,
        "feature_types": ["roads", "buildings", "water_bodies"],
        "processing_time": processing_time,
        "total_generation_time": end_time - start_time,
        "tile_image": img_base64,
        "operations_performed": ["coordinate_calculation", "feature_generation", "image_processing"]
    }

async def routing_calculation(start_lat=40.7128, start_lon=-74.0060, end_lat=40.7589, end_lon=-73.9851):
    """
    Simulate CPU-intensive routing calculations between two geographic points.
    """
    start_time = time.time()
    
    # Generate a network of nodes and edges for pathfinding (CPU-intensive)
    network_size = 1000
    nodes = []
    
    # Generate network nodes
    for i in range(network_size):
        # Interpolate between start and end points with some randomness
        t = i / network_size
        lat = start_lat + t * (end_lat - start_lat) + random.uniform(-0.01, 0.01)
        lon = start_lon + t * (end_lon - start_lon) + random.uniform(-0.01, 0.01)
        
        nodes.append({
            "id": i,
            "lat": lat,
            "lon": lon,
            "type": random.choice(["intersection", "waypoint", "landmark"])
        })
    
    # Generate edges between nodes (CPU-intensive)
    edges = []
    for i in range(network_size - 1):
        # Connect each node to several nearby nodes
        for j in range(i + 1, min(i + 5, network_size)):
            distance = calculate_haversine_distance(
                nodes[i]["lat"], nodes[i]["lon"],
                nodes[j]["lat"], nodes[j]["lon"]
            )
            
            # Calculate edge weight based on distance and road type
            road_type = random.choice(["highway", "arterial", "local", "residential"])
            speed_limits = {"highway": 65, "arterial": 45, "local": 35, "residential": 25}
            
            travel_time = distance / speed_limits[road_type] * 3600  # seconds
            
            edges.append({
                "from": i,
                "to": j,
                "distance": distance,
                "road_type": road_type,
                "travel_time": travel_time,
                "traffic_factor": random.uniform(0.8, 1.5)
            })
    
    # Implement Dijkstra's algorithm for shortest path (CPU-intensive)
    pathfinding_start = time.time()
    
    # Initialize distances
    distances = {i: float('inf') for i in range(network_size)}
    distances[0] = 0  # Start node
    previous = {i: None for i in range(network_size)}
    unvisited = set(range(network_size))
    
    # Dijkstra's main loop
    while unvisited:
        # Find unvisited node with minimum distance
        current = min(unvisited, key=lambda x: distances[x])
        
        if distances[current] == float('inf'):
            break
        
        unvisited.remove(current)
        
        # Check all neighbors
        for edge in edges:
            if edge["from"] == current and edge["to"] in unvisited:
                neighbor = edge["to"]
                # Calculate weight including traffic
                weight = edge["travel_time"] * edge["traffic_factor"]
                alt_distance = distances[current] + weight
                
                if alt_distance < distances[neighbor]:
                    distances[neighbor] = alt_distance
                    previous[neighbor] = current
    
    # Reconstruct path
    path = []
    current = network_size - 1  # End node
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    
    pathfinding_time = time.time() - pathfinding_start
    
    # Calculate route statistics
    total_distance = sum(
        edges[i]["distance"] for i in range(len(path) - 1)
        for edge in edges
        if edge["from"] == path[i] and edge["to"] == path[i + 1]
    )
    
    total_travel_time = distances[network_size - 1] if network_size - 1 in distances else 0
    
    # Generate turn-by-turn directions (CPU-intensive)
    directions = []
    for i in range(len(path) - 1):
        from_node = nodes[path[i]]
        to_node = nodes[path[i + 1]]
        
        # Calculate bearing for direction
        bearing = calculate_bearing(
            from_node["lat"], from_node["lon"],
            to_node["lat"], to_node["lon"]
        )
        
        direction = bearing_to_direction(bearing)
        distance = calculate_haversine_distance(
            from_node["lat"], from_node["lon"],
            to_node["lat"], to_node["lon"]
        )
        
        directions.append({
            "step": i + 1,
            "instruction": f"Head {direction} for {distance:.2f} km",
            "distance": distance,
            "bearing": bearing,
            "from_node": path[i],
            "to_node": path[i + 1]
        })
    
    end_time = time.time()
    
    return {
        "service": "Routing Calculation",
        "route_request": {
            "start": {"lat": start_lat, "lon": start_lon},
            "end": {"lat": end_lat, "lon": end_lon}
        },
        "network_stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "pathfinding_algorithm": "Dijkstra"
        },
        "route_result": {
            "path_nodes": path,
            "total_distance_km": total_distance,
            "estimated_travel_time_seconds": total_travel_time,
            "directions": directions[:10]  # First 10 directions
        },
        "computation_time": {
            "network_generation": pathfinding_start - start_time,
            "pathfinding": pathfinding_time,
            "total": end_time - start_time
        },
        "operations_performed": ["network_generation", "dijkstra_algorithm", "route_optimization"]
    }

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two geographic points using Haversine formula.
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate bearing between two geographic points.
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
    
    bearing = math.atan2(y, x)
    return (math.degrees(bearing) + 360) % 360

def bearing_to_direction(bearing):
    """
    Convert bearing to compass direction.
    """
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(bearing / 45) % 8
    return directions[index]

async def weather_data_processing(location="New York", forecast_days=7):
    """
    Simulate CPU-intensive weather data processing and forecasting.
    """
    start_time = time.time()
    
    # Generate historical weather data (CPU-intensive)
    historical_days = 365
    historical_data = []
    
    for day in range(historical_days):
        # Complex weather simulation based on seasonal patterns
        day_of_year = day % 365
        seasonal_temp = 20 + 15 * math.sin((day_of_year - 80) * 2 * math.pi / 365)
        
        # Add random variations and weather patterns
        temp_variation = random.gauss(0, 5)
        pressure_base = 1013.25
        pressure_variation = random.gauss(0, 20)
        
        # Simulate complex meteorological calculations
        humidity_factor = 0.5 + 0.3 * math.sin(day_of_year * 2 * math.pi / 365)
        wind_pattern = 10 + 5 * math.cos(day_of_year * 4 * math.pi / 365)
        
        historical_data.append({
            "day": day,
            "temperature": seasonal_temp + temp_variation,
            "pressure": pressure_base + pressure_variation,
            "humidity": min(100, max(0, humidity_factor * 100 + random.gauss(0, 15))),
            "wind_speed": max(0, wind_pattern + random.gauss(0, 3)),
            "precipitation": max(0, random.expovariate(0.5) - 1)
        })
    
    # Perform statistical analysis on historical data (CPU-intensive)
    analysis_start = time.time()
    
    # Calculate moving averages
    window_size = 30
    moving_averages = []
    
    for i in range(window_size, len(historical_data)):
        window_data = historical_data[i-window_size:i]
        avg_temp = sum(d["temperature"] for d in window_data) / window_size
        avg_pressure = sum(d["pressure"] for d in window_data) / window_size
        avg_humidity = sum(d["humidity"] for d in window_data) / window_size
        
        moving_averages.append({
            "day": i,
            "avg_temperature": avg_temp,
            "avg_pressure": avg_pressure,
            "avg_humidity": avg_humidity
        })
    
    # Generate forecast using complex meteorological models (CPU-intensive)
    forecast_data = []
    last_data = historical_data[-1]
    
    for day in range(forecast_days):
        # Simulate numerical weather prediction models
        
        # Temperature forecasting using multiple factors
        seasonal_trend = 0.1 * math.sin((day + 365) * 2 * math.pi / 365)
        pressure_influence = (last_data["pressure"] - 1013.25) * 0.02
        humidity_influence = (last_data["humidity"] - 50) * 0.01
        
        forecasted_temp = (last_data["temperature"] + seasonal_trend + 
                          pressure_influence + humidity_influence +
                          random.gauss(0, 2))
        
        # Pressure forecasting
        pressure_change = random.gauss(0, 5)
        forecasted_pressure = last_data["pressure"] + pressure_change
        
        # Complex precipitation probability calculation
        temp_factor = 1.0 if forecasted_temp > 0 else 0.5
        pressure_factor = max(0.1, (1020 - forecasted_pressure) / 20)
        humidity_factor = last_data["humidity"] / 100
        
        precip_probability = min(1.0, temp_factor * pressure_factor * humidity_factor * random.uniform(0.5, 1.5))
        
        # Wind speed forecasting
        pressure_gradient = abs(forecasted_pressure - last_data["pressure"])
        forecasted_wind = last_data["wind_speed"] + pressure_gradient * 0.5 + random.gauss(0, 2)
        
        forecast_entry = {
            "day": day + 1,
            "temperature": forecasted_temp,
            "pressure": forecasted_pressure,
            "humidity": min(100, max(0, last_data["humidity"] + random.gauss(0, 5))),
            "wind_speed": max(0, forecasted_wind),
            "precipitation_probability": precip_probability,
            "weather_condition": determine_weather_condition(forecasted_temp, precip_probability, forecasted_wind)
        }
        
        forecast_data.append(forecast_entry)
        last_data = forecast_entry
    
    analysis_time = time.time() - analysis_start
    
    # Generate weather alerts (CPU-intensive pattern matching)
    alerts = []
    for forecast in forecast_data:
        if forecast["temperature"] > 35:
            alerts.append({"type": "heat_warning", "day": forecast["day"]})
        elif forecast["temperature"] < -10:
            alerts.append({"type": "cold_warning", "day": forecast["day"]})
        elif forecast["wind_speed"] > 20:
            alerts.append({"type": "wind_warning", "day": forecast["day"]})
        elif forecast["precipitation_probability"] > 0.8:
            alerts.append({"type": "precipitation_warning", "day": forecast["day"]})
    
    end_time = time.time()
    
    return {
        "service": "Weather Data Processing and Forecasting",
        "location": location,
        "historical_data_days": len(historical_data),
        "forecast_days": forecast_days,
        "statistical_analysis": {
            "moving_averages_calculated": len(moving_averages),
            "analysis_window": window_size
        },
        "forecast": forecast_data,
        "weather_alerts": alerts,
        "computation_time": {
            "historical_processing": analysis_start - start_time,
            "forecasting_analysis": analysis_time,
            "total": end_time - start_time
        },
        "models_used": ["seasonal_patterns", "pressure_systems", "statistical_analysis", "numerical_prediction"],
        "operations_performed": ["data_generation", "statistical_analysis", "forecasting", "alert_generation"]
    }

def determine_weather_condition(temp, precip_prob, wind_speed):
    """
    Determine weather condition based on meteorological parameters.
    """
    if precip_prob > 0.7:
        if temp < 0:
            return "snow"
        elif wind_speed > 15:
            return "storm"
        else:
            return "rain"
    elif wind_speed > 20:
        return "windy"
    elif temp > 30:
        return "hot"
    elif temp < 5:
        return "cold"
    else:
        return "clear"

async def language_translation_service(text, source_lang="en", target_lang="es"):
    """
    Simulate CPU-intensive language translation processing.
    """
    start_time = time.time()
    
    # Tokenization (CPU-intensive)
    words = text.split()
    tokens = []
    
    for word in words:
        # Complex tokenization with morphological analysis
        token_analysis = {
            "original": word,
            "lowercase": word.lower(),
            "length": len(word),
            "char_frequency": {},
            "morphology": analyze_morphology(word),
            "pos_tag": determine_pos_tag(word)
        }
        
        # Character frequency analysis
        for char in word.lower():
            token_analysis["char_frequency"][char] = token_analysis["char_frequency"].get(char, 0) + 1
        
        tokens.append(token_analysis)
    
    # Dictionary lookup and semantic analysis (CPU-intensive)
    dictionary_start = time.time()
    translations = []
    
    # Simulate large dictionary operations
    for token in tokens:
        # Complex dictionary lookup simulation
        word_hash = hashlib.md5(token["original"].encode()).hexdigest()
        
        # Simulate multiple translation candidates
        candidates = []
        for i in range(5):  # Generate 5 translation candidates
            candidate_score = 0
            
            # Complex scoring algorithm
            for char in token["original"]:
                candidate_score += ord(char) * (i + 1)
            
            # Simulate semantic similarity calculation
            semantic_score = candidate_score % 100 / 100.0
            
            candidates.append({
                "translation": f"translated_{token['original']}_{i}",
                "confidence": semantic_score,
                "semantic_score": semantic_score
            })
        
        # Select best translation
        best_candidate = max(candidates, key=lambda x: x["confidence"])
        translations.append(best_candidate)
    
    dictionary_time = time.time() - dictionary_start
    
    # Grammar and syntax processing (CPU-intensive)
    grammar_start = time.time()
    
    # Simulate complex grammar analysis
    sentence_structures = []
    current_sentence = []
    
    for i, token in enumerate(tokens):
        current_sentence.append(token)
        
        # End of sentence detection
        if token["original"].endswith('.') or i == len(tokens) - 1:
            # Analyze sentence structure
            structure_analysis = {
                "length": len(current_sentence),
                "complexity": calculate_sentence_complexity(current_sentence),
                "grammar_rules_applied": apply_grammar_rules(current_sentence, target_lang)
            }
            sentence_structures.append(structure_analysis)
            current_sentence = []
    
    grammar_time = time.time() - grammar_start
    
    # Final translation assembly
    final_translation = " ".join([t["translation"] for t in translations])
    
    end_time = time.time()
    
    return {
        "service": "Language Translation",
        "source_language": source_lang,
        "target_language": target_lang,
        "original_text": text,
        "translated_text": final_translation,
        "processing_stats": {
            "words_processed": len(words),
            "tokens_analyzed": len(tokens),
            "sentences_parsed": len(sentence_structures),
            "translation_candidates_evaluated": len(tokens) * 5
        },
        "timing_breakdown": {
            "tokenization": dictionary_start - start_time,
            "dictionary_lookup": dictionary_time,
            "grammar_processing": grammar_time,
            "total": end_time - start_time
        },
        "linguistic_analysis": {
            "average_word_length": sum(len(w) for w in words) / len(words) if words else 0,
            "sentence_complexity": sum(s["complexity"] for s in sentence_structures) / len(sentence_structures) if sentence_structures else 0
        },
        "operations_performed": ["tokenization", "morphological_analysis", "dictionary_lookup", "grammar_parsing", "translation_assembly"]
    }

def analyze_morphology(word):
    """
    Simulate morphological analysis of a word.
    """
    # Simplified morphology analysis
    analysis = {
        "root": word[:max(1, len(word)//2)],
        "suffix": word[max(1, len(word)//2):],
        "syllable_count": max(1, len([c for c in word.lower() if c in 'aeiou']))
    }
    return analysis

def determine_pos_tag(word):
    """
    Determine part-of-speech tag (simplified).
    """
    if word.lower().endswith('ing'):
        return 'VERB'
    elif word.lower().endswith('ed'):
        return 'VERB'
    elif word.lower().endswith('ly'):
        return 'ADVERB'
    elif word.lower().endswith('s') and len(word) > 3:
        return 'NOUN'
    else:
        return 'NOUN'

def calculate_sentence_complexity(sentence_tokens):
    """
    Calculate complexity score for a sentence.
    """
    length_factor = len(sentence_tokens) / 10.0
    pos_variety = len(set(token["pos_tag"] for token in sentence_tokens))
    avg_word_length = sum(token["length"] for token in sentence_tokens) / len(sentence_tokens)
    
    return length_factor + pos_variety + avg_word_length / 10.0

def apply_grammar_rules(sentence_tokens, target_lang):
    """
    Simulate application of grammar rules for target language.
    """
    rules_applied = []
    
    # Simulate various grammar rule applications
    if target_lang == "es":  # Spanish
        rules_applied.extend(["noun_gender_agreement", "verb_conjugation", "adjective_placement"])
    elif target_lang == "de":  # German
        rules_applied.extend(["case_declension", "word_order", "compound_nouns"])
    elif target_lang == "ja":  # Japanese
        rules_applied.extend(["particle_usage", "politeness_levels", "word_order"])
    else:
        rules_applied.extend(["basic_syntax", "word_order"])
    
    return rules_applied

async def webservice_challenge(service="weather", location_or_query="New York", complexity=2):
    """
    Main function to replace simulate_default_cpu_work.
    Provides various real-world CPU-intensive web services.
    """
    if service == "map_tiles":
        zoom = max(8, min(15, 10 + complexity))
        tile_x = random.randint(0, 2**zoom - 1)
        tile_y = random.randint(0, 2**zoom - 1)
        return await map_tile_generation(zoom, tile_x, tile_y)
        
    elif service == "routing":
        # Random coordinates around major cities based on location
        if "new york" in location_or_query.lower():
            start_lat, start_lon = 40.7128, -74.0060
            end_lat, end_lon = 40.7589, -73.9851
        elif "london" in location_or_query.lower():
            start_lat, start_lon = 51.5074, -0.1278
            end_lat, end_lon = 51.5155, -0.0922
        else:
            start_lat, start_lon = 40.7128, -74.0060
            end_lat, end_lon = 40.7589, -73.9851
        
        return await routing_calculation(start_lat, start_lon, end_lat, end_lon)
        
    elif service == "weather":
        forecast_days = max(3, min(14, 7 + complexity))
        return await weather_data_processing(location_or_query, forecast_days)
        
    elif service == "translation":
        text = location_or_query if location_or_query else "Hello, this is a sample text for translation."
        target_languages = ["es", "fr", "de", "ja", "zh"]
        target_lang = random.choice(target_languages)
        return await language_translation_service(text, "en", target_lang)
        
    else:
        # Default to weather service
        return await weather_data_processing("Default Location", 7)