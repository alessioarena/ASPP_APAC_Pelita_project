# This bot does not ever move (useful for testing)

TEAM_NAME = 'StoppingBots'

def move(bot, state):
    import pdb; pdb.set_trace()
    # do not move at all
    next_move = (0,0)
    return next_move, state
