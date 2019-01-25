""" Team Bot Implementation 
"""

import numpy as np
import networkx as nx
import enum
from pelita.utils import Graph
from group0_utils import *
import pdb 
import matplotlib as mp
import matplotlib.pyplot as plt

TEAM_NAME = 'Group0'

class Mode(enum.Enum):
    # agent modes (can add more later)
    defend = 0
    attack = 1

def is_stuck(bot):
    return (len(bot.track) > 4) and (len(set(bot.track[-3:])) <= 2)
    

class BotState:
    '''
    We only get one state for both bots, so the bot-specific state data is stored as 
    list[2]
    '''
    def __init__(self, bot, modes, spawning_location):
        self.mode = modes;
        # set up a graph of the map 
        self.nx_G = walls_to_nxgraph(bot.walls, bot.homezone)
        # self.nx_G = walls_to_nxgraph(bot.walls)
        self.target = [None, None]
        self.spawning = spawning_location

        self.enemy_track = [[], []] # for enemy[0] and enemy[1] positions
        self.enemy_track_noise = [[], []]

def move_defend(bot, state, was_recur = False):
    '''
    move routine for defend.
    was_recur indicates whether this was called from within another move routine. This 
    happens when we switch agent modes
    '''
    # if there are two defenders and no enemies, we can become attackers
    # if state.mode[0] == state.mode[1] == Mode.defend and not was_recur:
    #     if sum([bot.enemy[0].is_noisy, bot.enemy[1].is_noisy]) < 2:
    #         state.mode[bot.turn] = Mode.attack
    #         return move_attack(bot, state, True)

    # target selection logic
    if bot.enemy[0].is_noisy and bot.enemy[1].is_noisy:
        # both enemies noisy, basically we ignore
        state.target[bot.turn] = bot.enemy[bot.turn].position
    
    elif not bot.enemy[bot.turn].is_noisy:
        # pursuit
        state.target[bot.turn] = bot.enemy[bot.turn].position
    elif not bot.enemy[1-bot.turn].is_noisy:
        # pursuit
        state.target[bot.turn] = bot.enemy[1-bot.turn].position

    # movement logic
    width = max([coord[0] for coord in bot.walls]) + 1
    heigth = max([coord[1] for coord in bot.walls]) + 1
    half_way = int(width / 2)
    exclusion_zone = [(x, y) for x in range(half_way-2, half_way+2) for y in range(heigth)]
    # exclusion_zone = list(find_gaps(width, heigth, bot.walls))
    base = state.spawning
    # if noisy
    if bot.enemy[0].is_noisy and bot.enemy[1].is_noisy:
        ## if current position in exclusion
        if bot.position in exclusion_zone:
            ### next move towards base
            next_pos = next_step(bot.position, base, state.nx_G)
        else:
            ### next move towards enemy
            next_pos = next_step(bot.position, state.target[bot.turn], state.nx_G)
            ### if next move in exclusion
            if next_pos in exclusion_zone:
                #### override with stay
                next_move = (0, 0)
    else:
        ## go for the enemy
        next_pos = next_step(bot.position, state.target[bot.turn], state.nx_G)
        bot.say('ATTAAAAAACK!!!!!')

    if next_pos in bot.enemy[0].homezone:
        next_move = (0, 0)
    else:
        next_move = bot.get_move(next_pos)
        
    if is_stuck(bot):
        print('defender stuck')
        next_move = bot.random.choice([i for i in bot.legal_moves if bot.get_position(i) not in bot.enemy[0].homezone])
    return next_move, state

def move_attack(bot, state, was_recur = False):
    '''
    move routine for attack.
    was_recur indicates whether this was called from within another move routine. This 
    happens when we switch agent modes
    '''
    
    # (TODO) attackers in home territory may become defenders
    # if bot.position in bot.homezone and not was_recur:
    #     switch_seek_target = None
    #     if not bot.enemy[0].is_noisy:
    #         switch_seek_target = bot.enemy[0].position
    #     elif not bot.enemy[1].is_noisy:
    #         switch_seek_target = bot.enemy[1].position
        
    #     if switch_seek_target != None:
    #         state.mode[bot.turn] = Mode.defend;
    #         return move_defend(bot, state, was_recur = True)

    # when in attacker mode, we aim for food
    if (state.target[bot.turn] is None) or (state.target[bot.turn] not in bot.enemy[0].food):
        # find new food target with minimal distance to agent
        food_dist = [nx.shortest_path_length(state.nx_G, source = bot.position, target=i) for i in bot.enemy[0].food]
        min_dist_idx = np.argmin(food_dist)
        state.target[bot.turn] = bot.enemy[0].food[min_dist_idx]

    next_pos = next_step(bot.position, state.target[bot.turn], state.nx_G)
    
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
        state = BotState(bot, [Mode.attack, Mode.defend], bot.position)

    # manually update tracks
    for i in range(0, len(bot.enemy)):
        state.enemy_track[i] += [bot.enemy[i].position]
        state.enemy_track_noise[i] += [bot.enemy[i].is_noisy]

    score_checking(bot, state)
    print(state.mode)

    if state.mode[bot.turn] == Mode.defend:
        move, state = move_defend(bot, state)
    else:
        move, state = move_attack(bot, state)
    return move, state

def score_checking(bot, state):
    '''Check current scores and food left to modify if we need to focus on attack or defense.'''
    own_score = bot.score
    enemy_score = bot.enemy[0].score
    food_for_us = len(bot.food)
    food_for_them = len(bot.enemy[0].food)
    winning = own_score > enemy_score
    if winning:
        # If we are winning and have nearly no food left, race to finish it (prevent attack bot from turning defensive
        if food_for_us <= 3:
            # Attack!
            state.mode[0] = Mode.attack
            state.mode[1] = Mode.attack
            return state            
        # If we are winning and enemy has nearly no food left, continue as we are to maximise score
        if food_for_them <= 3:
            return state
    elif not winning:
        # If we are losing and have nearly no food left, make both bots defend so we don't end the game when we're losing
        # OR
        # If we are losing and enemy has nearly no food left, make both bots defend so enemy can't easily force win
        if (food_for_us <= 3) or (food_for_them <= 3):
            # Defend
            state.mode[0] = Mode.defend
            state.mode[1] = Mode.defend
            return state
    elif own_score == enemy_score:
        # If the game is drawn, continue as we are until a condition is met.
        return state
    else:
        raise Exception("How did this case arise?")
