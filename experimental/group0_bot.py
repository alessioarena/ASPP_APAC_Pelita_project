""" Team Bot Implementation 
"""

import numpy as np
import networkx as nx
import enum
from pelita.utils import Graph
from utils import *
import pdb 

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
        if (next_pos == enemy.position) and (next_pos not in bot.homezone):
            state.target[bot.turn] = None
            next_pos = bot.track[-2]
            if next_pos == enemy.position:
                next_pos = bot.get_position(bot.random.choice(bot.legal_moves))

        next_move = bot.get_move(next_pos)
        return next_move, state

def move(bot, state):
    if state is None:
            state = BotState(bot, [Mode.attack, Mode.defend])

    print(state.mode)
    if state.mode[bot.turn] == Mode.defend:
        return move_defend(bot, state)
    else:
        return move_attack(bot, state)

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
