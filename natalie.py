import heapq
import numpy as np

TEAM_NAME = 'Nat'

def move(bot, state):
    if state is None:
        state = {}
        state["enemy_0_hx"] = []
        state["enemy_1_hx"] = []

    bot.say("it's me mario!")
    food = bot.enemy[0].food
    turn = bot.round + bot.turn
    if turn <= 10:
        state["enemy_0_hx"].append({
        "position": bot.enemy[0].position,
        "noisy": bot.enemy[0].is_noisy
        })
        state["enemy_1_hx"].append({
            "position": bot.enemy[1].position,
            "noisy": bot.enemy[1].is_noisy
        })
    else:
        mod = turn % 10
        state["enemy_0_hx"][mod] = {
        "position": bot.enemy[0].position,
        "noisy": bot.enemy[0].is_noisy
        }
        state["enemy_1_hx"][mod] = {
            "position": bot.enemy[1].position,
            "noisy": bot.enemy[1].is_noisy
        }


    walls = set(bot.walls)
    e1 = simple_enemy_locator(state["enemy_0_hx"])
    e2 = simple_enemy_locator(state["enemy_1_hx"])
    buff = buffer_for_enemy([e1, e2])
    walls.update(buff)
    closest_food_move = choose_move(bot.position, food, walls)
    if closest_food_move:
        move = bot.get_move(closest_food_move)
    else:
        move = bot.get_move(bot.track[-1])
    return move, state

def simple_enemy_locator(enemy_history):
    y = 0
    x = 0
    for enemy_hx in (enemy_history[-2:-1]):
        if not enemy_hx["noisy"]:
            return enemy_hx["position"]
        else:
            y += enemy_hx["position"][0] / 2
            x += enemy_hx["position"][1] / 2
    return (round(y), round(x))

def buffer_for_enemy(enemy_locations):
    return set((y + dy, x + dx)
        for y, x in enemy_locations
            for dy, dx in [(-3, 0), (3, 0), (0, 3), (0, -3), 
                            (-2, 1), (-2, 0), (-2, -1), 
                            (0, -2), (-1, -2), (1, -2),
                            (2, 1), (2, 0), (2, -1),
                            (0, 2), (-1, 2), (1, 2),
                            (1, 0), (1, -1), (1, 1),
                            (0, 1), (-1, 1), (-1, -1),
                            (0, -1), (-1, 0), (0, 0) ])

# Return the shortest path from current position to any of the food
# in the case of a tie, return all shortest paths
def shortest_paths(current_pos, food, walls):
    result = []
    best = None
    visited = set(walls)
    queue = [(0, [current_pos])]
    while queue:
        distance, path = heapq.heappop(queue)
        if best and len(path) > best:
            return result
        node = path[-1]
        if node in food:
            result.append(path)
            best = len(path)
            continue
        if node in visited:
            continue
        visited.add(node)
        for neighbor in adjacent({node}):
            if neighbor in visited:
                continue
            heapq.heappush(queue, (distance + 1, path + [neighbor]))
    return result

# adjacent returns all cells that are adjacent to all of the provided positions
def adjacent(positions):
    return set((y + dy, x + dx)
        for y, x in positions
            for dy, dx in [(-1, 0), (0, -1), (0, 1), (1, 0)])

# choose_target determines which target square a unit at `position` should
# move toward, given the specified target units
def choose_target(position, food, walls):
    if not food:
        return None
    if position in food:
        return position
    paths = shortest_paths(position, food, walls)
    ends = [x[-1] for x in paths]
    return min(ends) if ends else None

# choose_move determines the immediate up/down/left/right move to make
# given the source and target squares
def choose_move(position, target, walls):
    if position == target:
        return position
    paths = shortest_paths(position, target, walls)
    starts = [x[1] for x in paths]
    return min(starts) if starts else None
