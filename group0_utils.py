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
    if len(short_path)>1:
        return short_path[1]
    else:
        return short_path[0]

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
    central_heigth = (y for y in range(2, heigth - 2))
    if width - 2 == max([coord[0] for coord in homezone]):
        # you are starting on the right
        exclusion = [(x, y) for x in (middle_x+1, middle_x+2) for y in central_heigth]
    else:
        exclusion = [(x, y) for x in (middle_x, middle_x-1) for y in central_heigth]
        # you are starting on the left
    for coords in find_gaps(width, heigth, walls):
        if coords not in homezone or coords in exclusion:
            graph.add_node(coords, weight=500)
        else:
            graph.add_node(coords, weight=coords[0])
        for delta_x, delta_y in ((1,0), (-1,0), (0,1), (0,-1)):
            neighbor = (coords[0] + delta_x, coords[1] + delta_y)
            # we don't need to check for getting neighbors out of the maze
            # because our mazes are all surrounded by walls, i.e. our
            # deltas will not put us out of the maze
            if neighbor not in walls:
                # this is a genuine neighbor, add an edge in the graph
                graph.add_edge(coords, neighbor)
    return graph
