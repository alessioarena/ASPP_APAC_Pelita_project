# import cython
# import pyximport
# pyximport.install(build_in_temp=True)
# import c_utils
import networkx
import numpy as np

def closest_position(bot_position, target_positions, graph):
    # iterate through targets and calculate path lenghts
    all_distances = []
    for target in target_positions:
        all_distances.append(networkx.shortest_path_length(graph, bot_position, target, weight="weight"))

    # returning the index of the closest target
    return np.argmin(all_distances)


def next_step(bot_position, target_position, graph):
#    import pdb; pdb.set_trace()
    """Given a graph representation of the maze, return the next position
    in the (shortest-)path to target_position.

    The shortest path is computed on the graph using the a-star algorithm"""
    short_path = networkx.shortest_path(graph, bot_position, target_position, weight="weight")
    # print(graph.nodes[bot_position]['weight'])
    if len(short_path)>1:
        return short_path[1]
    else:
        return short_path[0]

def update_with_enemies(enemy_positions, graph):
    ## utility to get the new position
    def find_new_position(original, move):
        return (original[0] + move[0], original[1] + move[1])
    ## utility to update the weight based on multiplier
    def update_weight(graph, previous_graph, position, weight_multiplier):
        try:
            graph.nodes[position]['weight'] = previous_graph.nodes[position]['weight'] * weight_multiplier
        except KeyError:
            ## the target node does not exist
            pass
        return graph
    # Let's make a copy
    updated_graph = graph.copy()
    # possible moves
    moves = [(1, 0), (-1, 0), (0, 1), (0,-1)]
    for enemy in enemy_positions:
        for m1 in moves:
            # here we look at round +1 moves
            pos1 = find_new_position(enemy, m1)
            for m2 in moves:
                # here we look at round +2 moves
                pos2 = find_new_position(pos1, m1)
                for m3 in moves:
                    # here we look at round +3 moves
                    pos3 = find_new_position(pos2, m1)
                    ## cascade update to not overwrite previous changes (round+1 has priority over round=2 and so on)
                    updated_graph = update_weight(updated_graph, graph, pos3, 2)
                updated_graph = update_weight(updated_graph, graph, pos2, 5)
            updated_graph = update_weight(updated_graph, graph, pos1, 10)
        updated_graph = update_weight(updated_graph, graph, enemy, 30)
    return updated_graph


# def inspect_updated(enemy_positions, graph):
#     def find_new_position(original, move):
#         return (original[0] + move[0], original[1] + move[1])
#     def update_node(graph, position, weight_multiplier):
#         try:
#             print(position, graph.nodes[position]['weight'])
#         except KeyError:
#             pass
#         return
#     updated_graph = graph.copy()
#     moves = [(1, 0), (-1, 0), (0, 1), (0,-1)]
#     for m1 in moves:
#         pos1 = find_new_position(enemy_positions, m1)
#         update_node(updated_graph, pos1, 10)
#         for m2 in moves:
#             pos2 = find_new_position(pos1, m1)
#             update_node(updated_graph, pos2, 5)
#             for m3 in moves:
#                 pos3 = find_new_position(pos2, m1)
#                 update_node(updated_graph, pos3, 2)
#     return

def find_gaps(width, heigth, walls):
    for x in range(width):
        for y in range(heigth):
            if (x, y) not in walls:
                yield (x, y)

def walls_to_nxgraph(walls, homezone=None):
    """Return a networkx Graph object given a pelita maze (walls)"""
    graph = networkx.Graph()
    width = max([coord[0] for coord in walls]) + 1
    heigth = max([coord[1] for coord in walls]) + 1
    middle_x = int(width / 2)
    middle_y = int(heigth / 2)
    # central_heigth = (y for y in range(2, heigth - 2))
    if (middle_x - 1) == max([coord[0] for coord in homezone]):
        # you are starting on the right
        exclusion = [middle_x-1, middle_x-2]
    else:
        exclusion = [middle_x, middle_x+1]
        # you are starting on the left
    for coords in find_gaps(width, heigth, walls):
        # if coords not in homezone:
        #     graph.add_node(coords, weight=100)
        # elif coords[0] in exclusion:
        #     graph.add_node(coords, weight=10)
        # else:
        #     graph.add_node(coords, weight=1)
        for delta_x, delta_y in ((1,0), (-1,0), (0,1), (0,-1)):
            neighbor = (coords[0] + delta_x, coords[1] + delta_y)
            if coords not in homezone:
                coords_weight = 100
            elif coords[0] in exclusion:
                coords_weight = 10
            else:
                coords_weight = 1

            # we don't need to check for getting neighbors out of the maze
            # because our mazes are all surrounded by walls, i.e. our
            # deltas will not put us out of the maze
            if neighbor not in walls:
                if neighbor not in homezone:
                    neighbor_weight = 100
                elif neighbor[0] in exclusion:
                    neighbor_weight = 10
                else:
                    neighbor_weight = 1
                weight = (coords_weight + neighbor_weight) / 2
                # this is a genuine neighbor, add an edge in the graph
                graph.add_edge(coords, neighbor, weight=weight)
    return graph
