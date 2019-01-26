""" Team Bot Implementation 
"""

import numpy as np
import networkx as nx
import enum
from pelita.utils import Graph
from group0_utils import *
import matplotlib as mp
import matplotlib.pyplot as plt
from operator import sub
import pdb

TEAM_NAME = 'Group0'

class Mode(enum.Enum):
    # agent modes (can add more later)
    defend = 0
    attack = 1

def is_stuck(bot):
    return (len(bot.track) > 5) and (len(set(bot.track[-5:])) <= 2)


class BotState:
    '''
    We only get one state for both bots, so the bot-specific state data is stored as 
    list[2]
    '''
    def __init__(self, bot, modes, spawning_location):
        self.mode = modes
        # set up a graph of the map 
        self.nx_G = walls_to_nxgraph(bot.walls, bot.homezone)
        # self.nx_G = walls_to_nxgraph(bot.walls)
        self.target = [None, None]
        self.spawning = spawning_location
        self.home_boundary_x = 15 if self.spawning[0] <= 15 else 16
        self.home_boundaries = [boundary for boundary in (set(bot.homezone) - set(bot.walls)) if boundary[0] == self.home_boundary_x]
        self.enemy_track = [[[], []], [[], []]] # enemy_track[0][1] is the list of positions of enemy[1] as seen by bot[0]
        self.enemy_track_noise = [[[], []], [[], []]] # same but for noise flags

        # enemy cells around the homezone boundary
        self.homezone_enembound = [(15, i) for i in range(0, 16)] if bot.is_blue else [(16, i) for i in range(0, 16)]
        self.homezone_enembound = [i for i in self.homezone_enembound if not i in bot.walls]

    def enemy_track_update(self, bot):
        for i in range(0, 2):
            self.enemy_track[bot.turn][i] += [bot.enemy[i].position, ]
            self.enemy_track_noise[bot.turn][i] += [bot.enemy[i].is_noisy, ]

    def enemy_track_flush(self, bot, enemy_idx):
        for i in enemy_idx:
            for j in range(0, 2):
                self.enemy_track[j][i] = [bot.enemy[i].position, ]
                self.enemy_track_noise[j][i] = [bot.enemy[i].is_noisy, ]

    def enemy_check_kill(self, bot, new_pos): # check if an enemy has been killed in our homezone
        killed = []
        for i in range(0, 2):
            if not bot.enemy[i].is_noisy and bot.enemy[i].position == new_pos\
                and new_pos in bot.homezone:
                killed+=[i, ]
        return killed

    def get_enemy_pos_info(self, bot, enemy_idx):
        # call AFTER enemy_track_update for latest information
        if not self.enemy_track_noise[bot.turn][enemy_idx][-1]:
            # if not noisy, return own information
            return (self.enemy_track[bot.turn][enemy_idx][-1], self.enemy_track_noise[bot.turn][enemy_idx][-1])
        elif len(self.enemy_track_noise[1-bot.turn][enemy_idx]) > 0 and not self.enemy_track_noise[1-bot.turn][enemy_idx][-1]:
            # first round is a special case and we need ensure the other bot's enemy pos info is not empty
            return (self.enemy_track[1-bot.turn][enemy_idx][-1], self.enemy_track_noise[1-bot.turn][enemy_idx][-1])
        else:
            return (self.enemy_track[bot.turn][enemy_idx][-1], self.enemy_track_noise[bot.turn][enemy_idx][-1])

    def get_enemy_pos(self, bot, enemy_idx):
        return self.get_enemy_pos_info(bot, enemy_idx)[0]

    def get_enemy_noise(self, bot, enemy_idx):
        return self.get_enemy_pos_info(bot, enemy_idx)[1]

def move_defend(bot, state, was_recur = False):
    '''
    move routine for defend.
    was_recur indicates whether this was called from within another move routine. This 
    happens when we switch agent modes
    '''
    noisy_e0 = state.get_enemy_noise(bot, 0) 
    noisy_e1 = state.get_enemy_noise(bot, 1) 

    homezone_e0 = state.get_enemy_pos(bot, 0) in bot.homezone
    homezone_e1 = state.get_enemy_pos(bot, 1) in bot.homezone

    # if there are two defenders and no enemies, we can become attackers
    if state.mode[0] == state.mode[1] == Mode.defend and not was_recur:
        if not any([homezone_e0, homezone_e1]):
            state.mode[bot.turn] = Mode.attack
            return move_attack(bot, state, True)

    closest = closest_position(bot.position, (state.get_enemy_pos(bot, 0), state.get_enemy_pos(bot, 1)), state.nx_G)

    # target selection logic
    ## both in homezone
    if all([homezone_e0, homezone_e1]):
        if noisy_e0 + noisy_e1 == 1:
            ## select bot 0 if bot 1 is noisy (and therefore bot 0 is not)
            state.target[bot.turn] = state.get_enemy_pos(bot, 0) if noisy_e1 else state.get_enemy_pos(bot, 1) 
        else:
            ## go to the closest
            state.target[bot.turn] = bot.enemy[closest].position
    elif homezone_e0 + homezone_e1 == 1:
        ## select the one in the homezone
        state.target[bot.turn] = state.get_enemy_pos(bot, 0) if homezone_e0 else state.get_enemy_pos(bot, 1) 
    else:
        ## No one to be seen
        ## find out who is closer
        closer_to_enemy = closest_position(bot.enemy[closest].position, (bot.other.position, bot.position), state.nx_G)
        if closer_to_enemy:
            # you are closer, you should go
            state.target[bot.turn] = bot.enemy[closest].position
        else:
            # the other will deal with it
            state.target[bot.turn] = bot.enemy[1 - closest].position

    # movement logic
    width = max([coord[0] for coord in bot.walls]) + 1
    heigth = max([coord[1] for coord in bot.walls]) + 1
    half_way = int(width / 2)
    middle_y = int(heigth / 2)
    # exclusion_zone = [(x, y) for x in range(half_way-2, half_way+2) for y in range(heigth)]
    exclusion_zone = list(range(half_way-2, half_way+2))
    
    base = (state.spawning[0], middle_y)
    # if this is a wall, no path will lead to that
    if base in bot.walls:
        # fallback to the spawning point
        base = state.spawning
    # if noisy
    if state.get_enemy_noise(bot, 0) and state.get_enemy_noise(bot, 1):
        ## if current position in exclusion
        if bot.position[0] in exclusion_zone:
            ### find the side you are on and look behind you
            corners = [(-1,1), (-1, -1)] if base[0] < half_way else [(1,1), (1,-1)]
            maybe_walls = [(bot.position[0] + x, bot.position[1] + y) for x,y in corners]
            ### the bot is trying to get around corners
            if any([w in bot.walls for w in maybe_walls]):
                ### move towards target
                next_pos = next_step(bot.position, state.target[bot.turn], state.nx_G)
            else:
                ### next move towards base
                next_pos = next_step(bot.position, base, state.nx_G)
        else:
            ### next move towards enemy
            next_pos = next_step(bot.position, state.target[bot.turn], state.nx_G)
            ### if next move in exclusion
            # if next_pos in exclusion_zone:
            #     #### override with stay
            #     next_move = (0, 0)
    else:
        if state.target[bot.turn] not in bot.homezone:
            next_pos = next_step(bot.position, base, state.nx_G)
            bot.say('Come here if you dare!')
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
        next_move = bot.random.choice([i for i in bot.legal_moves if bot.get_position(i) in bot.homezone])
    return next_move, state

def move_attack(bot, state, was_recur = False):
    '''
    move routine for attack.
    was_recur indicates whether this was called from within another move routine. This 
    happens when we switch agent modes
    '''
# need below for natalies code
    # if bot.position in bot.homezone and not was_recur:
    #     switch_seek_target = None
    #     if not state.get_enemy_noise(bot, 0) and state.get_enemy_pos(bot, 0) in bot.homezone:
    #         switch_seek_target = state.get_enemy_pos(bot, 0) 
    #     elif not state.get_enemy_noise(bot, 1) and state.get_enemy_pos(bot, 1) in bot.homezone:
    #         switch_seek_target = state.get_enemy_pos(bot, 1)
        
    #     if switch_seek_target != None:
    #         state.mode[bot.turn] = Mode.defend
    #         return move_defend(bot, state, was_recur = True)

    # graph_with_enemies = update_with_enemies((state.get_enemy_pos(bot, 0), state.get_enemy_pos(bot, 1)), state.nx_G)
# need for steves code

    if (bot.position in bot.homezone) \
        and not was_recur:
        switch_seek_target = None
        if bot.enemy[0].position in bot.homezone:
            switch_seek_target = bot.enemy[0].position
        elif bot.enemy[1].position in bot.homezone:
            switch_seek_target = bot.enemy[1].position
        
        if switch_seek_target != None:
            state.mode[bot.turn] = Mode.defend
            print(state.mode)
            return move_defend(bot, state, was_recur = True)
    
    if (state.target[bot.turn] is None) or (state.target[bot.turn] not in bot.enemy[0].food):
        # find new food target with minimal distance to agent
        food_dist = [nx.shortest_path_length(graph_with_enemies, source = bot.position, target=i) for i in bot.enemy[0].food]
        min_dist_idx = np.argmin(food_dist)
        state.target[bot.turn] = bot.enemy[0].food[min_dist_idx]

    next_pos = next_step(bot.position, state.target[bot.turn], state.nx_G)

# Stephen's implementation
    enemy_pos = [i.position for i in bot.enemy if i.is_noisy == False] #if not bot.position in bot.homezone else [] 
    enemy_dists = [nx.shortest_path_length(state.nx_G, source = next_pos, target = j) for j in enemy_pos] #\
                # if not bot.position in bot.homezone else []

    bad_steps = []
    for i in range(0, len(enemy_pos)):
        if enemy_dists[i] < 4:
            # enemy is visible
            bad_steps += [bot.get_move(next_step(bot.position, enemy_pos[i], state.nx_G)), ]

    if len(bad_steps) > 0:
        bad_steps += [bot.get_move(bot.track[-2]), (0, 0)]
        bad_steps += [i for i in bot.legal_moves for j in range(0, len(enemy_pos)) \
                        if nx.shortest_path_length(state.nx_G, source = bot.get_position(i), target = enemy_pos[j]) <= 1]
        try:
            next_pos = bot.get_position(bot.random.choice([i for i in bot.legal_moves if not i in bad_steps]))
        except:
            # no possible moves! give up and die
            print('Give up')
            next_pos = bot.position

    # enemy_nearby = [not state.get_enemy_noise(bot, 0), not state.get_enemy_noise(bot, 1)]


    # # for enemy in bot.enemy:
    # if all(enemy_nearby) and not bot.position in bot.homezone:
    #     bot.say("Go away.")
    #     food_dist = [nx.shortest_path_length(graph_with_enemies, source = bot.position, target=i) for i in bot.enemy[0].food]
    #     enemy_0_food_dist = [nx.shortest_path_length(state.nx_G, source = state.get_enemy_pos(bot, 0), target=i) for i in bot.enemy[0].food]
    #     enemy_1_food_dist = [nx.shortest_path_length(state.nx_G, source = state.get_enemy_pos(bot, 1), target=i) for i in bot.enemy[0].food]
    #     enemy_food_dist = list(map(min, enemy_0_food_dist, enemy_1_food_dist))
    #     food_enemy_diff = list(map(sub, enemy_food_dist, food_dist))
    #     if np.max(food_enemy_diff) > 0:
    #         min_dist_idx = np.argmax(food_enemy_diff)
    #         state.target[bot.turn] = bot.enemy[0].food[min_dist_idx]
    #         next_pos = next_step(bot.position, state.target[bot.turn], state.nx_G)
    #     else:
    #         boundary_dist = [nx.shortest_path_length(graph_with_enemies, source = bot.position, target=i) for i in state.home_boundaries]
    #         enemy_0_boundary_dist = [nx.shortest_path_length(state.nx_G, source = state.get_enemy_pos(bot, 0), target=i) for i in state.home_boundaries]
    #         enemy_1_boundary_dist = [nx.shortest_path_length(state.nx_G, source = state.get_enemy_pos(bot, 1), target=i) for i in state.home_boundaries]
    #         enemy_boundary_dist = list(map(min, enemy_0_boundary_dist, enemy_1_boundary_dist))
    #         boundary_enemy_diff = list(map(sub, enemy_boundary_dist, boundary_dist))
    #         min_dist_idx = np.argmax(boundary_enemy_diff)
    #         next_pos = next_step(bot.position, state.home_boundaries[min_dist_idx], state.nx_G)
    # elif any(enemy_nearby) and not bot.position in bot.homezone:
    #     enemy = bot.enemy[np.argmax(enemy_nearby)]
    #     bot.say("Go away.")
    #     food_dist = [nx.shortest_path_length(graph_with_enemies, source = bot.position, target=i) for i in bot.enemy[0].food]
    #     enemy_dist = [nx.shortest_path_length(state.nx_G, source = enemy.position, target=i) for i in bot.enemy[0].food]
    #     food_enemy_diff = np.array(enemy_dist) - np.array(food_dist)
    #     if np.max(food_enemy_diff) > 0:
    #         min_dist_idx = np.argmax(food_enemy_diff)
    #         state.target[bot.turn] = bot.enemy[0].food[min_dist_idx]
    #         next_pos = next_step(bot.position, state.target[bot.turn], state.nx_G)
    #     else:
    #         boundary_dist = [nx.shortest_path_length(graph_with_enemies, source = bot.position, target=i) for i in state.home_boundaries]
    #         enemy_boundary_dist = [nx.shortest_path_length(state.nx_G, source = enemy.position, target=i) for i in state.home_boundaries]
    #         boundary_enemy_diff = np.array(enemy_boundary_dist) - np.array(boundary_dist)
    #         min_dist_idx = np.argmax(boundary_enemy_diff)
    #         next_pos = next_step(bot.position, state.home_boundaries[min_dist_idx], state.nx_G)    

    # if next_pos == enemy.position:
    #     state.target[bot.turn] = None
    #     next_pos = bot.track[-2]
    #     if next_pos == enemy.position:
    #         next_pos = bot.get_position(bot.random.choice(bot.legal_moves))

    if is_stuck(bot):
        print('attacker stuck')
        if bot.position not in bot.homezone:
            next_move = bot.random.choice([i for i in bot.legal_moves if not any(bot.get_position(i) == state.get_enemy_pos(state, 0), \
                                                                                bot.get_position(i) == state.get_enemy_pos(state, 1))])
        else:
            next_move = bot.random.choice([i for i in bot.legal_moves if bot.get_position(i) in bot.homezone])

    next_move = bot.get_move(next_pos)
    return next_move, state

def move(bot, state):
    try:
        if state is None:
            state = BotState(bot, [Mode.defend, Mode.attack], bot.position)

        state.enemy_track_update(bot)

        # print optimal info

        print('------')
        print('Enemy 0 best pos: ', state.get_enemy_pos(bot, 0))
        print('Enemy 1 best pos: ', state.get_enemy_pos(bot, 1))
        print('------')

        score_checking(bot, state)
        if state.mode[bot.turn] == Mode.defend:
            move, state = move_defend(bot, state)
        else:
            move, state = move_attack(bot, state)
    except:
       bot.say('Exception!')
       move = bot.random.choice(bot.legal_moves)
    else:
        pass

    # broadcast id
    bot.say('bot '+str(bot.turn))

    # check for kill
    state.enemy_track_flush(bot, state.enemy_check_kill(bot, bot.get_position(move)))

    return move, state

def score_checking(bot, state, k = 5):
    '''Check current scores and food left to modify if we need to focus on attack or defense.'''
    own_score = bot.score
    enemy_score = bot.enemy[0].score
    food_for_us = len(bot.enemy[0].food)
    food_for_them = len(bot.food)
    winning = own_score > enemy_score
    if winning:
        # If we are winning and have nearly no food left, race to finish it (prevent attack bot from turning defensive
        if food_for_us <= k:
            print("Attack mode initiated")
            # Attack!
            state.mode[0] = Mode.attack
            state.mode[1] = Mode.attack
            return state            
        # If we are winning and enemy has nearly no food left, continue as we are to maximise score
        if food_for_them <= k:
            return state
    elif not winning:
        # If we are losing and have nearly no food left, make both bots defend so we don't end the game when we're losing
        # OR
        # If we are losing and enemy has nearly no food left, make both bots defend so enemy can't easily force win
        if (food_for_us <= k) or (food_for_them <= k):
            print("Defense mode initiated")
	    # Defend
            state.mode[0] = Mode.defend
            state.mode[1] = Mode.defend
            return state
    elif own_score == enemy_score:
        # If the game is drawn, continue as we are until a condition is met.
        return state
    else:
        raise Exception("How did this case arise?")
