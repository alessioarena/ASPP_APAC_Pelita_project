""" Team Bot Implementation 
"""

import numpy as np
import networkx as nx
import enum
from pelita.utils import Graph
from utils import *
import pdb 
import matplotlib as mp
import matplotlib.pyplot as plt

TEAM_NAME = 'Group0'

class Mode(enum.Enum):
    # agent modes (can add more later)
    defend = 0
    attack = 1

class BotState:
    '''
    We only get one state for both bots, so the bot-specific state data is stored as 
    list[2]
    '''
    def __init__(self, bot, modes):
        self.mode = modes;
        # set up a graph of the map 
        self.G = Graph(bot.position, bot.walls)
        self.nx_G = walls_to_nxgraph(bot.walls)
        self.target = [None, None]
        self.enemy_track = [[], []] # for enemy[0] and enemy[1] positions
        self.enemy_track_noise = [[], []]
        self.stat_counter = [0, 0] # counter for number of stationaries 

def move_defend(bot, state, was_recur = False):
    '''
    move routine for defend.
    was_recur indicates whether this was called from within another move routine. This 
    happens when we switch agent modes
    '''
    # if there are two defenders and no enemies, we can become attackers
    if state.mode[0] == state.mode[1] == Mode.defend and not was_recur:
        if sum([bot.enemy[0].is_noisy, bot.enemy[1].is_noisy]) < 2:
            state.mode[bot.turn] = Mode.attack
            return move_attack(bot, state, True)

    if bot.enemy[0].is_noisy and bot.enemy[1].is_noisy:
        # both enemies noisy, basically we ignore
        state.target[bot.turn] = bot.enemy[bot.turn].position
    elif not bot.enemy[bot.turn].is_noisy:
        # pursuit
        state.target[bot.turn] = bot.enemy[bot.turn].position
    elif not bot.enemy[1-bot.turn].is_noisy:
        # pursuit
        state.target[bot.turn] = bot.enemy[1-bot.turn].position
    next_pos = next_step(bot.position, state.target[bot.turn], state.G)
    if next_pos in bot.enemy[0].homezone:
        next_move = (0, 0)
    else:
        next_move = bot.get_move(next_pos)
    return next_move, state

def move_attack(bot, state, was_recur = False):
    '''
    move routine for attack.
    was_recur indicates whether this was called from within another move routine. This 
    happens when we switch agent modes
    '''
    
    # (TODO) attackers in home territory may become defenders
    if bot.position in bot.homezone and not was_recur:
        switch_seek_target = None
        if not bot.enemy[0].is_noisy:
            switch_seek_target = bot.enemy[0].position
        elif not bot.enemy[1].is_noisy:
            switch_seek_target = bot.enemy[1].position
        
        if switch_seek_target != None:
            state.mode[bot.turn] = Mode.defend;
            return move_defend(bot, state, was_recur = True)

    # when in attacker mode, we aim for food
    if (state.target[bot.turn] is None) or (state.target[bot.turn] not in bot.enemy[0].food):
        # find new food target with minimal distance to agent
        food_dist = [nx.shortest_path_length(state.nx_G, source = bot.position, target=i) for i in bot.enemy[0].food]
        min_dist_idx = np.argmin(food_dist)
        state.target[bot.turn] = bot.enemy[0].food[min_dist_idx]

    next_pos = next_step(bot.position, state.target[bot.turn], state.G)
    
    for enemy in bot.enemy:
        if (nx.shortest_path_length(state.nx_G, source = next_pos, target =  enemy.position) < 3)\
                and (next_pos not in bot.homezone)\
                and not enemy.is_noisy:
            state.target[bot.turn] = None
            next_pos = bot.track[-2]
            if next_pos == enemy.position:
                next_pos = bot.get_position(bot.random.choice(bot.legal_moves))

        next_move = bot.get_move(next_pos)
        return next_move, state

def move(bot, state):
    if state is None:
        state = BotState(bot, [Mode.attack, Mode.defend])
    # manually update tracks
    for i in range(0, len(bot.enemy)):
        state.enemy_track[i] += [bot.enemy[i].position]
        state.enemy_track_noise[i] += [bot.enemy[i].is_noisy]
    
    if state.mode[bot.turn] == Mode.defend:
        move, state = move_defend(bot, state)
    else:
        move, state = move_attack(bot, state)

    if move == (0, 0):
        state.stat_counter[bot.turn]+=1
    return move, state
