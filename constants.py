# Number of sides of a 6-sided die
NUM_DIE_FACES = 6
# Max number of turns in a Battle
TURN_LIMIT = 100
# Temporal Learning Rate and how much the end results affects the immediate rewards of a Learning Agent's State
DEFAULT_GAMMA = 0.5
# Percent chance the Learning Agent randomly chooses an action
DEFAULT_EPSILON = 0.2
# Percent chance the Learning Agent is exploitative, choosing the action with highest probability
DEFAULT_RHO = 0.0
# Number of accepted invalid actions from the Player before the battle terminates
# This is to prevent the Learning Agent from indefinitely exploring invalid routes
INVALID_ACTION_LIMIT = 10000
# Reward for every step the Learning Agent takes. This is primarily to prevent the agent from stalling
REWARD_AMOUNT_STEP_PENALTY = -1
# Reward for the Learning Agent winning a Battle
REWARD_AMOUNT_WIN = 10000
# Reward for the Learning Agent losing a Battle. This includes early termination by inactive moves and turn limit
REWARD_AMOUNT_LOSS = -10000
# Score for player unit's health not being 0. This is averaged across all player units
REWARD_SCORE_PLAYER_UNIT_SURVIVING = 5000
# Score for player unit being healthy multiplied by its percent health. This is averaged across all player units
REWARD_SCORE_PLAYER_UNIT_HEALTH = 5000
# Score for player unit's health not being 0. This is averaged across all player units
REWARD_SCORE_ENEMY_UNIT_SURVIVING = -5000
# Score for player unit being healthy multiplied by its percent health. This is averaged across all player units
REWARD_SCORE_ENEMY_UNIT_HEALTH = -5000