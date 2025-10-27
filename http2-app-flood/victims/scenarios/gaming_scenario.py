# scenarios/gaming_scenario.py

import random
import time
import hashlib
import asyncio
from collections import deque

async def generate_sudoku_puzzle(WORKLOAD=3):
    """
    Generate a Sudoku puzzle with CPU-intensive solving and validation.
    """
    start_time = time.time()
    
    # Initialize empty 9x9 grid
    grid = [[0 for _ in range(9)] for _ in range(9)]
    
    # Fill grid with valid solution (CPU-intensive)
    fill_grid_recursively(grid)
    
    # Create puzzle by removing numbers based on WORKLOAD
    puzzle = [row[:] for row in grid]  # Copy solution
    cells_to_remove = 20 + (WORKLOAD * 15)  # More removals for higher WORKLOAD
    
    removed_count = 0
    attempts = 0
    max_attempts = cells_to_remove * 10
    
    while removed_count < cells_to_remove and attempts < max_attempts:
        row = random.randint(0, 8)
        col = random.randint(0, 8)
        
        if puzzle[row][col] != 0:
            # Temporarily remove the number
            backup = puzzle[row][col]
            puzzle[row][col] = 0
            
            # Check if puzzle still has unique solution (CPU-intensive)
            if count_solutions(puzzle) == 1:
                removed_count += 1
            else:
                puzzle[row][col] = backup  # Restore if multiple solutions
        
        attempts += 1
    
    # Validate final puzzle (CPU-intensive)
    validation_start = time.time()
    is_valid = validate_sudoku_puzzle(puzzle)
    validation_time = time.time() - validation_start
    
    end_time = time.time()
    
    return {
        "game": "Sudoku Generation",
        "WORKLOAD_level": WORKLOAD,
        "puzzle": puzzle,
        "solution": grid,
        "cells_removed": removed_count,
        "puzzle_valid": is_valid,
        "generation_time": end_time - start_time,
        "validation_time": validation_time,
        "operations_performed": ["recursive_backtracking", "uniqueness_checking", "puzzle_validation"]
    }

def fill_grid_recursively(grid):
    """
    Fill Sudoku grid using backtracking algorithm (CPU-intensive).
    """
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                numbers = list(range(1, 10))
                random.shuffle(numbers)  # Randomize order
                
                for num in numbers:
                    if is_valid_placement(grid, row, col, num):
                        grid[row][col] = num
                        
                        if fill_grid_recursively(grid):
                            return True
                        
                        grid[row][col] = 0  # Backtrack
                
                return False
    return True

def is_valid_placement(grid, row, col, num):
    """
    Check if number placement is valid in Sudoku grid.
    """
    # Check row
    for c in range(9):
        if grid[row][c] == num:
            return False
    
    # Check column
    for r in range(9):
        if grid[r][col] == num:
            return False
    
    # Check 3x3 box
    box_row = (row // 3) * 3
    box_col = (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if grid[r][c] == num:
                return False
    
    return True

def count_solutions(puzzle):
    """
    Count number of solutions for Sudoku puzzle (CPU-intensive).
    """
    grid = [row[:] for row in puzzle]  # Copy puzzle
    solutions = [0]  # Use list for reference passing
    
    def solve_and_count(grid, solutions):
        if solutions[0] > 1:  # Stop if more than one solution found
            return
        
        for row in range(9):
            for col in range(9):
                if grid[row][col] == 0:
                    for num in range(1, 10):
                        if is_valid_placement(grid, row, col, num):
                            grid[row][col] = num
                            solve_and_count(grid, solutions)
                            grid[row][col] = 0
                    return
        
        solutions[0] += 1
    
    solve_and_count(grid, solutions)
    return solutions[0]

def validate_sudoku_puzzle(puzzle):
    """
    Validate Sudoku puzzle structure (CPU-intensive).
    """
    # Check all rows
    for row in puzzle:
        seen = set()
        for num in row:
            if num != 0:
                if num in seen or num < 1 or num > 9:
                    return False
                seen.add(num)
    
    # Check all columns
    for col in range(9):
        seen = set()
        for row in range(9):
            num = puzzle[row][col]
            if num != 0:
                if num in seen or num < 1 or num > 9:
                    return False
                seen.add(num)
    
    # Check all 3x3 boxes
    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            seen = set()
            for row in range(box_row, box_row + 3):
                for col in range(box_col, box_col + 3):
                    num = puzzle[row][col]
                    if num != 0:
                        if num in seen or num < 1 or num > 9:
                            return False
                        seen.add(num)
    
    return True

async def generate_random_maze(width=50, height=50):
    """
    Generate random maze using recursive backtracking (CPU-intensive).
    """
    start_time = time.time()
    
    # Initialize maze with walls
    maze = [['#' for _ in range(width)] for _ in range(height)]
    
    # Directions: up, right, down, left
    directions = [(-2, 0), (0, 2), (2, 0), (0, -2)]
    
    # Stack for backtracking
    stack = []
    start_row, start_col = 1, 1
    maze[start_row][start_col] = ' '  # Mark as path
    stack.append((start_row, start_col))
    
    cells_carved = 1
    total_cells = (width // 2) * (height // 2)
    
    # Recursive backtracking algorithm
    while stack:
        current_row, current_col = stack[-1]
        
        # Find unvisited neighbors
        neighbors = []
        for dr, dc in directions:
            new_row, new_col = current_row + dr, current_col + dc
            
            if (0 < new_row < height - 1 and 0 < new_col < width - 1 and 
                maze[new_row][new_col] == '#'):
                neighbors.append((new_row, new_col))
        
        if neighbors:
            # Choose random neighbor
            next_row, next_col = random.choice(neighbors)
            
            # Carve path to neighbor
            wall_row = current_row + (next_row - current_row) // 2
            wall_col = current_col + (next_col - current_col) // 2
            
            maze[next_row][next_col] = ' '
            maze[wall_row][wall_col] = ' '
            
            stack.append((next_row, next_col))
            cells_carved += 1
        else:
            # Backtrack
            stack.pop()
    
    # Add start and end points
    maze[1][0] = 'S'  # Start
    maze[height - 2][width - 1] = 'E'  # End
    
    # Solve maze using A* algorithm (CPU-intensive)
    solving_start = time.time()
    path = solve_maze_astar(maze, (1, 0), (height - 2, width - 1))
    solving_time = time.time() - solving_start
    
    end_time = time.time()
    
    return {
        "game": "Random Maze Generation",
        "dimensions": {"width": width, "height": height},
        "maze": maze,
        "cells_carved": cells_carved,
        "total_possible_cells": total_cells,
        "maze_density": cells_carved / total_cells,
        "path_solution": path,
        "path_length": len(path) if path else 0,
        "generation_time": solving_start - start_time,
        "solving_time": solving_time,
        "total_time": end_time - start_time,
        "algorithms_used": ["recursive_backtracking", "a_star_pathfinding"],
        "operations_performed": ["maze_generation", "pathfinding", "optimization"]
    }

def solve_maze_astar(maze, start, goal):
    """
    Solve maze using A* pathfinding algorithm (CPU-intensive).
    """
    height = len(maze)
    width = len(maze[0]) if height > 0 else 0
    
    def heuristic(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    while open_set:
        # Get node with lowest f_score
        current_f, current = min(open_set, key=lambda x: x[0])
        open_set.remove((current_f, current))
        
        if current == goal:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return list(reversed(path))
        
        for dr, dc in directions:
            neighbor = (current[0] + dr, current[1] + dc)
            
            if (0 <= neighbor[0] < height and 0 <= neighbor[1] < width and
                maze[neighbor[0]][neighbor[1]] in [' ', 'S', 'E']):
                
                tentative_g = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                    
                    if (f_score[neighbor], neighbor) not in open_set:
                        open_set.append((f_score[neighbor], neighbor))
    
    return []  # No path found

async def generate_procedural_content(content_type="dungeon", size=20, complexity=3):
    """
    Generate procedural game content using various algorithms (CPU-intensive).
    """
    start_time = time.time()
    
    if content_type == "dungeon":
        return generate_dungeon(size, complexity, start_time)
    elif content_type == "terrain":
        return generate_terrain(size, complexity, start_time)
    elif content_type == "quest":
        return generate_quest_chain(complexity, start_time)
    else:
        return generate_dungeon(size, complexity, start_time)

def generate_quest_chain(complexity, start_time):
    """
    Generate a complex quest chain with dependencies (CPU-intensive).
    """
    quests = []
    quest_types = ["fetch", "kill", "escort", "puzzle", "exploration", "crafting"]
    locations = ["forest", "dungeon", "city", "mountains", "ruins", "castle"]
    
    # Generate main quest line
    main_quest_count = complexity + 2
    
    for i in range(main_quest_count):
        quest_id = f"main_{i+1}"
        quest_type = random.choice(quest_types)
        location = random.choice(locations)
        
        # Calculate quest difficulty (CPU-intensive)
        difficulty_factors = []
        for _ in range(complexity * 10):
            factor = random.uniform(0.5, 2.0)
            # Complex calculation to simulate AI difficulty balancing
            adjusted_factor = factor * (1 + 0.1 * complexity)
            difficulty_factors.append(adjusted_factor)
        
        base_difficulty = sum(difficulty_factors) / len(difficulty_factors)
        
        # Generate quest rewards (CPU-intensive calculation)
        reward_calculation_iterations = complexity * 50
        experience_points = 0
        gold_reward = 0
        
        for _ in range(reward_calculation_iterations):
            experience_points += random.randint(1, 10) * base_difficulty
            gold_reward += random.randint(5, 50) * base_difficulty
        
        # Normalize rewards
        experience_points = int(experience_points / reward_calculation_iterations * 100)
        gold_reward = int(gold_reward / reward_calculation_iterations * 10)
        
        quest = {
            "id": quest_id,
            "type": quest_type,
            "name": f"{quest_type.title()} Quest in {location.title()}",
            "location": location,
            "difficulty": base_difficulty,
            "prerequisites": [f"main_{i}"] if i > 0 else [],
            "rewards": {
                "experience": experience_points,
                "gold": gold_reward
            },
            "estimated_completion_time": int(base_difficulty * 10)
        }
        quests.append(quest)
    
    # Generate side quests (CPU-intensive dependency analysis)
    side_quest_count = complexity * 2
    
    for i in range(side_quest_count):
        quest_id = f"side_{i+1}"
        quest_type = random.choice(quest_types)
        location = random.choice(locations)
        
        # Complex dependency calculation
        dependency_options = [q["id"] for q in quests if random.random() < 0.3]
        prerequisites = dependency_options[:random.randint(0, min(2, len(dependency_options)))]
        
        # CPU-intensive reward balancing
        reward_multiplier = 1.0
        for _ in range(complexity * 20):
            reward_multiplier *= random.uniform(0.95, 1.05)
        
        side_quest = {
            "id": quest_id,
            "type": quest_type,
            "name": f"Side Quest: {quest_type.title()} in {location.title()}",
            "location": location,
            "difficulty": random.uniform(0.5, 1.5) * complexity,
            "prerequisites": prerequisites,
            "rewards": {
                "experience": int(50 * reward_multiplier),
                "gold": int(25 * reward_multiplier)
            },
            "estimated_completion_time": random.randint(5, 20)
        }
        quests.append(side_quest)
    
    # Calculate quest chain statistics (CPU-intensive)
    total_experience = sum(q["rewards"]["experience"] for q in quests)
    total_gold = sum(q["rewards"]["gold"] for q in quests)
    total_time = sum(q["estimated_completion_time"] for q in quests)
    
    # Generate completion paths (CPU-intensive pathfinding)
    completion_paths = generate_quest_completion_paths(quests)
    
    end_time = time.time()
    
    return {
        "content_type": "Quest Chain Generation",
        "complexity_level": complexity,
        "total_quests": len(quests),
        "main_quests": main_quest_count,
        "side_quests": side_quest_count,
        "quest_details": quests,
        "total_rewards": {
            "experience": total_experience,
            "gold": total_gold
        },
        "estimated_total_time": total_time,
        "completion_paths": completion_paths,
        "generation_time": end_time - start_time,
        "algorithms_used": ["dependency_analysis", "reward_balancing", "pathfinding"],
        "operations_performed": ["quest_generation", "difficulty_calculation", "path_optimization"]
    }

def generate_quest_completion_paths(quests):
    """
    Generate optimal quest completion paths (CPU-intensive).
    """
    paths = []
    
    # Build dependency graph
    quest_map = {q["id"]: q for q in quests}
    
    # Find all possible completion orders (CPU-intensive)
    def find_completion_order(remaining_quests, completed_quests, current_path):
        if not remaining_quests:
            paths.append(current_path.copy())
            return
        
        available_quests = []
        for quest in remaining_quests:
            prerequisites_met = all(prereq in completed_quests for prereq in quest["prerequisites"])
            if prerequisites_met:
                available_quests.append(quest)
        
        for quest in available_quests:
            new_remaining = [q for q in remaining_quests if q["id"] != quest["id"]]
            new_completed = completed_quests + [quest["id"]]
            new_path = current_path + [quest["id"]]
            
            find_completion_order(new_remaining, new_completed, new_path)
    
    # Start pathfinding
    find_completion_order(quests, [], [])
    
    # Limit paths to prevent excessive computation
    return paths[:10] if len(paths) > 10 else paths

def generate_terrain(size, complexity, start_time):
    """
    Generate procedural terrain using Perlin noise simulation (CPU-intensive).
    """
    # Initialize terrain grid
    terrain = [[0.0 for _ in range(size)] for _ in range(size)]
    
    # Generate multiple octaves of noise (CPU-intensive)
    octaves = complexity + 2
    
    for octave in range(octaves):
        frequency = 2 ** octave
        amplitude = 1.0 / (2 ** octave)
        
        # Generate noise for this octave
        for y in range(size):
            for x in range(size):
                # Simple noise generation (CPU-intensive)
                noise_value = 0.0
                
                # Multiple iterations for smoother noise
                for i in range(complexity * 5):
                    sample_x = x * frequency / size + i * 0.1
                    sample_y = y * frequency / size + i * 0.1
                    
                    # Pseudo-random noise calculation
                    noise_component = (
                        random.uniform(-1, 1) * 
                        abs(sample_x - int(sample_x)) * 
                        abs(sample_y - int(sample_y))
                    )
                    noise_value += noise_component
                
                terrain[y][x] += (noise_value / (complexity * 5)) * amplitude
    
    # Normalize terrain values
    max_height = max(max(row) for row in terrain)
    min_height = min(min(row) for row in terrain)
    height_range = max_height - min_height
    
    if height_range > 0:
        for y in range(size):
            for x in range(size):
                terrain[y][x] = (terrain[y][x] - min_height) / height_range
    
    # Generate terrain features (CPU-intensive)
    features = generate_terrain_features(terrain, complexity)
    
    end_time = time.time()
    
    return {
        "content_type": "Procedural Terrain",
        "size": size,
        "complexity_level": complexity,
        "octaves_generated": octaves,
        "terrain_data": terrain,
        "terrain_features": features,
        "height_statistics": {
            "min_height": min_height,
            "max_height": max_height,
            "height_range": height_range
        },
        "generation_time": end_time - start_time,
        "algorithms_used": ["perlin_noise_simulation", "multi_octave_generation", "feature_detection"],
        "operations_performed": ["noise_generation", "terrain_analysis", "feature_placement"]
    }

def generate_terrain_features(terrain, complexity):
    """
    Analyze terrain and place features (CPU-intensive).
    """
    size = len(terrain)
    features = []
    
    # Detect peaks and valleys (CPU-intensive analysis)
    for y in range(1, size - 1):
        for x in range(1, size - 1):
            current_height = terrain[y][x]
            
            # Check neighboring heights
            neighbors = [
                terrain[y-1][x-1], terrain[y-1][x], terrain[y-1][x+1],
                terrain[y][x-1],                    terrain[y][x+1],
                terrain[y+1][x-1], terrain[y+1][x], terrain[y+1][x+1]
            ]
            
            avg_neighbor_height = sum(neighbors) / len(neighbors)
            height_diff = current_height - avg_neighbor_height
            
            # Classify terrain features
            if height_diff > 0.1:  # Peak
                features.append({
                    "type": "peak",
                    "position": (x, y),
                    "height": current_height,
                    "prominence": height_diff
                })
            elif height_diff < -0.1:  # Valley
                features.append({
                    "type": "valley",
                    "position": (x, y),
                    "height": current_height,
                    "depth": -height_diff
                })
    
    return features

def generate_dungeon(size, complexity, start_time):
    """
    Generate procedural dungeon layout (CPU-intensive).
    """
    # Initialize dungeon grid
    dungeon = [['#' for _ in range(size)] for _ in range(size)]
    
    # Generate rooms (CPU-intensive placement algorithm)
    rooms = []
    room_attempts = complexity * 20
    
    for _ in range(room_attempts):
        room_width = random.randint(3, 8)
        room_height = random.randint(3, 8)
        room_x = random.randint(1, size - room_width - 1)
        room_y = random.randint(1, size - room_height - 1)
        
        new_room = {
            "x": room_x,
            "y": room_y,
            "width": room_width,
            "height": room_height,
            "center": (room_x + room_width // 2, room_y + room_height // 2)
        }
        
        # Check for room overlaps (CPU-intensive collision detection)
        overlap = False
        for existing_room in rooms:
            if rooms_overlap(new_room, existing_room):
                overlap = True
                break
        
        if not overlap:
            # Carve out room
            for y in range(room_y, room_y + room_height):
                for x in range(room_x, room_x + room_width):
                    dungeon[y][x] = '.'
            
            rooms.append(new_room)
        
        if len(rooms) >= complexity * 5:  # Limit number of rooms
            break
    
    # Connect rooms with corridors (CPU-intensive pathfinding)
    corridor_generation_start = time.time()
    
    for i in range(len(rooms) - 1):
        current_room = rooms[i]
        next_room = rooms[i + 1]
        
        # Create L-shaped corridor between room centers
        start_x, start_y = current_room["center"]
        end_x, end_y = next_room["center"]
        
        # Horizontal corridor
        for x in range(min(start_x, end_x), max(start_x, end_x) + 1):
            if 0 <= start_y < size and 0 <= x < size:
                dungeon[start_y][x] = '.'
        
        # Vertical corridor
        for y in range(min(start_y, end_y), max(start_y, end_y) + 1):
            if 0 <= end_x < size and 0 <= y < size:
                dungeon[y][end_x] = '.'
    
    corridor_time = time.time() - corridor_generation_start
    
    # Place special features (CPU-intensive feature placement)
    features_placed = place_dungeon_features(dungeon, rooms, complexity)
    
    end_time = time.time()
    
    return {
        "content_type": "Procedural Dungeon",
        "size": size,
        "complexity_level": complexity,
        "rooms_generated": len(rooms),
        "room_details": rooms,
        "special_features": features_placed,
        "dungeon_layout": dungeon,
        "generation_time": {
            "total": end_time - start_time,
            "corridor_generation": corridor_time,
            "feature_placement": end_time - corridor_generation_start - corridor_time
        },
        "algorithms_used": ["room_placement", "collision_detection", "corridor_generation", "feature_placement"],
        "operations_performed": ["spatial_analysis", "pathfinding", "procedural_generation"]
    }

def rooms_overlap(room1, room2):
    """
    Check if two rooms overlap.
    """
    return not (room1["x"] + room1["width"] < room2["x"] or
                room2["x"] + room2["width"] < room1["x"] or
                room1["y"] + room1["height"] < room2["y"] or
                room2["y"] + room2["height"] < room1["y"])

def place_dungeon_features(dungeon, rooms, complexity):
    """
    Place special features in dungeon (CPU-intensive).
    """
    features = []
    size = len(dungeon)
    
    # Calculate feature placement probability based on complexity
    feature_types = ["treasure", "trap", "monster", "portal", "fountain"]
    
    for room in rooms:
        for _ in range(complexity):
            if random.random() < 0.7:  # 70% chance to place feature
                feature_type = random.choice(feature_types)
                
                # Find valid position in room (CPU-intensive search)
                attempts = 0
                while attempts < 50:
                    feature_x = random.randint(room["x"] + 1, room["x"] + room["width"] - 2)
                    feature_y = random.randint(room["y"] + 1, room["y"] + room["height"] - 2)
                    
                    if (0 <= feature_x < size and 0 <= feature_y < size and
                        dungeon[feature_y][feature_x] == '.'):
                        
                        # Place feature symbol
                        feature_symbols = {"treasure": "$", "trap": "^", "monster": "M", "portal": "O", "fountain": "~"}
                        dungeon[feature_y][feature_x] = feature_symbols[feature_type]
                        
                        features.append({
                            "type": feature_type,
                            "position": (feature_x, feature_y),
                            "room_id": rooms.index(room)
                        })
                        break
                    
                    attempts += 1
    
    return features

async def matchmaking_algorithm(player_count=100, skill_range=(100, 2000)):
    """
    Simulate CPU-intensive matchmaking algorithm for multiplayer games.
    """
    start_time = time.time()
    
    # Generate player profiles
    players = []
    for i in range(player_count):
        player = {
            "id": i,
            "skill_rating": random.randint(skill_range[0], skill_range[1]),
            "region": random.choice(["NA", "EU", "AS", "SA", "OC"]),
            "game_mode_preference": random.choice(["casual", "ranked", "tournament"]),
            "playtime_hours": random.randint(1, 5000),
            "win_rate": random.uniform(0.3, 0.8),
            "connection_quality": random.choice(["excellent", "good", "fair", "poor"]),
            "waiting_time": 0
        }
        players.append(player)
    
    # Complex matchmaking algorithm (CPU-intensive)
    matches = []
    unmatched_players = players.copy()
    match_id = 0
    
    while len(unmatched_players) >= 2:
        match_id += 1
        current_match = []
        
        # Select first player (highest priority)
        primary_player = min(unmatched_players, key=lambda p: p["waiting_time"])
        current_match.append(primary_player)
        unmatched_players.remove(primary_player)
        
        # Find compatible players (CPU-intensive compatibility calculation)
        compatible_players = []
        
        for candidate in unmatched_players:
            compatibility_score = calculate_player_compatibility(primary_player, candidate)
            if compatibility_score > 0.5:  # Minimum compatibility threshold
                compatible_players.append((candidate, compatibility_score))
        
        # Sort by compatibility and select best matches
        compatible_players.sort(key=lambda x: x[1], reverse=True)
        
        # Add players to match (team size based on game mode)
        team_size = 5 if primary_player["game_mode_preference"] == "tournament" else 3
        
        for candidate, score in compatible_players:
            if len(current_match) < team_size:
                current_match.append(candidate)
                unmatched_players.remove(candidate)
            else:
                break
        
        # Only create match if we have at least 2 players
        if len(current_match) >= 2:
            # Calculate match statistics (CPU-intensive)
            match_stats = calculate_match_statistics(current_match)
            
            matches.append({
                "match_id": match_id,
                "players": [p["id"] for p in current_match],
                "team_size": len(current_match),
                "average_skill": match_stats["average_skill"],
                "skill_variance": match_stats["skill_variance"],
                "region": match_stats["primary_region"],
                "estimated_duration": match_stats["estimated_duration"],
                "match_quality": match_stats["match_quality"]
            })
        
        # Update waiting times for remaining players
        for player in unmatched_players:
            player["waiting_time"] += 1
    
    end_time = time.time()
    
    return {
        "algorithm": "Advanced Matchmaking System",
        "total_players": player_count,
        "matches_created": len(matches),
        "players_matched": sum(match["team_size"] for match in matches),
        "unmatched_players": len(unmatched_players),
        "matches": matches,
        "algorithm_performance": {
            "total_time": end_time - start_time,
            "average_time_per_match": (end_time - start_time) / len(matches) if matches else 0,
            "matching_efficiency": (player_count - len(unmatched_players)) / player_count
        },
        "operations_performed": ["compatibility_calculation", "priority_sorting", "team_balancing", "quality_assessment"]
    }

def calculate_player_compatibility(player1, player2):
    """
    Calculate compatibility score between two players (CPU-intensive).
    """
    # Skill difference factor
    skill_diff = abs(player1["skill_rating"] - player2["skill_rating"])
    skill_factor = max(0, 1 - (skill_diff / 500))  # Normalize to 0-1
    
    # Region compatibility
    region_factor = 1.0 if player1["region"] == player2["region"] else 0.3
    
    # Game mode compatibility
    mode_factor = 1.0 if player1["game_mode_preference"] == player2["game_mode_preference"] else 0.5
    
    # Experience compatibility (based on playtime)
    exp_diff = abs(player1["playtime_hours"] - player2["playtime_hours"])
    exp_factor = max(0, 1 - (exp_diff / 1000))
    
    # Connection quality factor
    connection_weights = {"excellent": 1.0, "good": 0.8, "fair": 0.6, "poor": 0.3}
    min_connection = min(connection_weights[player1["connection_quality"]],
                        connection_weights[player2["connection_quality"]])
    
    # Weighted compatibility score
    weights = [0.4, 0.2, 0.2, 0.1, 0.1]  # skill, region, mode, experience, connection
    factors = [skill_factor, region_factor, mode_factor, exp_factor, min_connection]
    
    compatibility = sum(w * f for w, f in zip(weights, factors))
    return compatibility

def calculate_match_statistics(players):
    """
    Calculate detailed statistics for a match (CPU-intensive).
    """
    skills = [p["skill_rating"] for p in players]
    average_skill = sum(skills) / len(skills)
    skill_variance = sum((s - average_skill) ** 2 for s in skills) / len(skills)
    
    # Determine primary region
    regions = [p["region"] for p in players]
    primary_region = max(set(regions), key=regions.count)
    
    # Estimate match duration based on skill levels and game mode
    avg_playtime = sum(p["playtime_hours"] for p in players) / len(players)
    base_duration = 30  # minutes
    skill_modifier = (average_skill - 1000) / 100  # Adjust based on skill
    experience_modifier = min(10, avg_playtime / 100)  # Experience factor
    
    estimated_duration = base_duration + skill_modifier + experience_modifier
    
    # Calculate overall match quality
    skill_balance = max(0, 1 - (skill_variance / 10000))
    region_consistency = regions.count(primary_region) / len(regions)
    match_quality = (skill_balance + region_consistency) / 2
    
    return {
        "average_skill": average_skill,
        "skill_variance": skill_variance,
        "primary_region": primary_region,
        "estimated_duration": estimated_duration,
        "match_quality": match_quality
    }

async def gaming_challenge(game_type="sudoku", WORKLOAD=3, size=20):
    """
    Main function to replace simulate_default_cpu_work.
    Provides various CPU-intensive gaming and entertainment scenarios.
    """
    if game_type == "sudoku":
        return await generate_sudoku_puzzle(WORKLOAD)
        
    elif game_type == "maze":
        maze_size = max(20, size)
        return await generate_random_maze(maze_size, maze_size)
        
    elif game_type == "procedural":
        content_types = ["dungeon", "terrain", "quest"]
        content_type = random.choice(content_types)
        return await generate_procedural_content(content_type, size, WORKLOAD)
        
    elif game_type == "matchmaking":
        player_count = max(50, size * 5)
        return await matchmaking_algorithm(player_count)
        
    else:
        # Default to Sudoku
        return await generate_sudoku_puzzle(WORKLOAD)