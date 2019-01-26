import demo_group0_for_testing
from demo_group0_for_testing import move
from pelita.utils import setup_test_game

'''
(x,y)
--> x
|   y

    layout="""
    ################################
    #           #           #      #
    #  #  #         ##             #
    # ## ##### ###    ## #   #     #
    # #            #     #   #     #
    #     # #      ######## ## ##  #
    #    ## ####                  ##
    #                 #########    #
    #       ######            #    #
    ##                  ###  ##    #
    #   # ## ########        #     #
    #     #   #    #             # #
    #     #   # ##    ### ##### ## #
    #  #                     #     #
    #  #  #   #        #           #
    ################################
    """
'''

def test_kill_enemy():
    # do we kill enemy when it's close to us in the homezone?
    #layout="""
    ########
    #    1.#
    #.0E  E#
    ########"""
    layout="""
    ################################
    #           #           #      #
    #  #  #   1     ##             #
    # ## ##### ###    ## #   #     #
    # #            #     #   #   E #
    #     # #      ######## ## ##  #
    #    ## ####                  ##
    #                 #########    #
    #       ######            #    #
    ##    0E            ###  ##    #
    #   # ## ########        #     #
    #     #   #    #             # #
    #     #   # ##    ### ##### ## #
    #  #                     #     #
    #  #  #   #        #           #
    ################################
    """
    bot = setup_test_game(layout=layout, is_blue=True)
    next_move, _ = move(bot, None)
    assert next_move == (1, 0)
    # 0 kills enemy to the right

def test_stop_at_the_border():
    # do we stop when we can't move?
    #layout="""
        ########
        #  # 1.#
        #.#0#EE#
        ########"""

    layout="""
    ################################
    #           #           #      #
    #  #  #         ##        E    #
    # ## ##### ###    ## #   #     #
    # #            #     #   #     #
    #     # #      ######## ## ##  #
    # 1  ## ####                  ##
    #                 #########    #
    #       ######            #    #
    ##                  ###  ##    #
    #   # ## ########        #     #
    #     #   #0#  #             # #
    #     #   ######  ### ##### ## #
    #  #                     #     #
    #  #  #   #        #        E  #
    ################################
    """
    bot = setup_test_game(layout=layout, is_blue=True)
    next_move, _ = move(bot, None)
    assert next_move == (0, 0)
    # don't move because we are surrounded by walls

def test_face_the_enemy():
    # do we move back out of the exclusion zone when enemy is still in enemy homezone?
    #layout="""
    ########
    #  0 1.#
    #.  E E#
    ########"""
    layout="""
    ################################
    #   1       #           #      #
    #  #  #         ##             #
    # ## ##### ###    ## #   #     #
    # #            #     #   #  E  #
    #     # #      ######## ## ##  #
    #    ## ####                  ##
    #              0E #########    #
    #       ######            #    #
    ##                  ###  ##    #
    #   # ## ########        #     #
    #     #   #    #             # #
    #     #   # ##    ### ##### ## #
    #  #                     #     #
    #  #  #   #        #           #
    ################################
    """
    bot = setup_test_game(layout=layout, is_blue=True)
    next_move, _ = move(bot, None)
    assert next_move in ((-1, 0),(0,-1),(0,1),(0,0))
    # move back out of exclusion zone

def test_eat_food():
    # do we eat food when it's available?
    #layout="""
    ########
    #    0.#
    #.1  EE#
    ########"""
    layout="""
    ################################
    # 1         #     0.    #      #
    #  #  #         ##         ##  #
    # ## ##### ###  ## #   # #     #
    # #            #     #    ###  #
    #     # #      ######## ## ##  #
    #    ## ####                  ##
    #                 #########    #
    #       ######            #    #
    ##                  ###  ##    #
    #   # ## ########        #     #
    #     #    #    #            # #
    #     #   # ##    ### ##### ## #
    #  #                    #      #
    #  #  #   #        #         EE#
    ################################
    """
    bot = setup_test_game(layout=layout, is_blue=True)
    next_move, state = move(bot, None)
    assert next_move in ((1, 0),(0,0))
    # bot 0 eats food to the right

def test_no_kamikaze():
    # do we avoid enemies when they can kill us?
    #layout="""
    ########
    #    E.#
    #.1  0E#
    ########"""
    layout="""
    ################################
    # 1         #           ####   #
    #  #  #         ##         0E  #
    # ## ##### ###    ## #   # E   #
    # #            #     #   #     #
    #     # #      ######## ## ##  #
    #    ## ####                  ##
    #                 #########    #
    #      ######             #    #
    ##                  ###  ##    #
    #   # ## ########        #     #
    #     #   #    #             # #
    #     #   # ##    ### ##### ## #
    #  #                     #     #
    #  #  #   #        #           #
    ################################
    """
    bot = setup_test_game(layout=layout, is_blue=True)
    # create a "fake" track of previous moves, as our bot needs it to decide
    # where to go to avoid a bot
    next_move, state = move(bot, None)
    assert next_move == (-1, 0)
    # move to the left, only way out

def test_legalmoves():
    # check that the only two valid moves are always returned
    # we try ten times, to test 10 different random streams
    #layout="""
    ########
    #0######
    #1. .EE#
    ########"""
    layout="""
    ################################
    #           #           #      #
    #   ##          ##             #
    # ##1##### ###    ## #   #     #
    # ##0          #     #   #   E #
    #   ### #      ######## ## ##  #
    #    ## ####                  ##
    #                 #########    #
    #       ######            #    #
    ##                  ###  ##    #
    #   # ## ########        #   E #
    #     #   #    #             # #
    #     #   # ##    ### ##### ## #
    #  #                     #     #
    #  #  #   #        #           #
    ################################
    """
    bot = setup_test_game(layout=layout, is_blue=True)
    next_move,_ = move(bot, None)
    assert next_move in ((1,0), (0,0), (0,-1))
    # allowed moves: to the right, stop or step on other bot
