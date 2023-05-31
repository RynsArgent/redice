from character import *
from game_data import *
from player import *
from targetable import *
from battle import *
from battle_env import *
import random
import constants
import logging
from gym.wrappers import FlattenObservation

def run_episode(battle_env, players):
    battle = battle_env.battle
    is_done = False
    while not is_done:
        action = None
        if battle.state == BattleState.MAIN_PHASE:
            turn = battle.get_current_turn()
            player = players[turn.team]
            action = player.select_action()
        next_state, reward, is_done, is_terminated, info = battle_env.step(action)

    for team in players:
        player = players[team]
        player.finish_episode()
    turns = battle_env.battle.turn
    winning_team = battle_env.battle.get_winning_team()
    return turns, winning_team

def get_battle_training_dummies(logger, game_data, random):
    player_character1 = Character(game_data, 'John Wayne', ['fighter', 'fighter'])
    player_unit1 = Unit(logger, game_data, player_character1, Team.BLUE, Location.FRONT, 'P1')
    player_character2 = Character(game_data, 'Hilbert Wayne', ['fighter', 'fighter'])
    player_unit2 = Unit(logger, game_data, player_character2, Team.BLUE, Location.FRONT, 'P2')
    enemy_character1 = Character(game_data, 'Rubick Coridano', ['training_dummy', 'training_dummy'])
    enemy_unit1 = Unit(logger, game_data, enemy_character1, Team.RED, Location.FRONT, 'E1')
    enemy_character2 = Character(game_data, 'Aaron Keller', ['training_dummy', 'training_dummy'])
    enemy_unit2 = Unit(logger, game_data, enemy_character2, Team.RED, Location.BACK, 'E2')

    units = [player_unit1, player_unit2, enemy_unit1, enemy_unit2]

    battle = Battle(logger, units, random)
    return battle

def get_battle_fighters(logger, game_data, random):
    player_character1 = Character(game_data, 'John Wayne', ['fighter', 'fighter'])
    player_unit1 = Unit(logger, game_data, player_character1, Team.BLUE, Location.FRONT, 'P1')
    player_character2 = Character(game_data, 'Hilbert Wayne', ['fighter', 'fighter'])
    player_unit2 = Unit(logger, game_data, player_character2, Team.BLUE, Location.FRONT, 'P2')
    enemy_character1 = Character(game_data, 'Rubick Coridano', ['fighter', 'fighter'])
    enemy_unit1 = Unit(logger, game_data, enemy_character1, Team.RED, Location.FRONT, 'E1')
    enemy_character2 = Character(game_data, 'Aaron Keller', ['fighter', 'fighter'])
    enemy_unit2 = Unit(logger, game_data, enemy_character2, Team.RED, Location.BACK, 'E2')

    units = [player_unit1, player_unit2, enemy_unit1, enemy_unit2]

    battle = Battle(logger, units, random)
    return battle

def train_episodes(battle_env, players, start_i, end_i):
    for i_episode in range(start_i, end_i):
        print('Training episode: {0} eps: {1:.3}'.format(i_episode, players[Team.BLUE].epsilon), end = " ")
        turns, winning_team = run_episode(battle_env, players)
        print('Turns {0} Winner {1} Player (Iterations, Reward) {2} {3}'.format(
            turns, winning_team, players[Team.BLUE].get_episode_details(), players[Team.RED].get_episode_details()))

        battle_env.reset()
        for team in players:
            player = players[team]
            player.reset_episode()

def create_logger(log_level):
    # Get the root logger
    logger = logging.getLogger()

    # Set the log level to the desired level
    logger.setLevel(log_level)

    # Configure the logging format
    formatter = logging.Formatter('%(message)s')

    # Remove the "root" log level from the format
    formatter._style._fmt = formatter._style._fmt.replace('root', '')

    # Create a handler and set the formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Run a training experiment with Actor Critic
def run_training_agent(game_data):
    game_logger = create_logger(logging.WARNING)

    battle = get_battle_training_dummies(game_logger, game_data, random)
    battle_env = BattleEnv(game_logger, battle)

    players = {}
    players[Team.BLUE] = LearningAgent(game_logger, game_data, battle_env, Team.BLUE, constants.DEFAULT_GAMMA, constants.DEFAULT_EPSILON, constants.DEFAULT_RHO)
    players[Team.RED] = NonPlayer(game_logger, game_data, battle_env, Team.RED, random)

    train_episodes(battle_env, players, 1, 1000)

    battle = get_battle_fighters(game_logger, game_data, random)
    battle_env.change_battle(battle)
    players[Team.RED] = NonPlayer(game_logger, game_data, battle_env, Team.RED, random)

    train_episodes(battle_env, players, 1001, 2000)

    print('Test episode {0}'.format(1))
    players[Team.BLUE].should_print_probabilities = True
    players[Team.BLUE].epsilon = 0
    players[Team.BLUE].rho = 0
    run_episode(battle_env, players)

# Run a crappy UI console input example of the game
def run_manual_game(game_data):
    game_logger = create_logger(logging.INFO)

    battle = get_battle_fighters(game_logger, game_data, random)
    battle_env = BattleEnv(game_logger, battle)

    players = {}
    players[Team.BLUE] = ConsolePlayer(game_logger, game_data, battle_env, Team.BLUE)
    players[Team.RED] = NonPlayer(game_logger, game_data, battle_env, Team.RED, random)

    run_episode(battle_env, players)

def main():
    game_data = GameData('data.json')
    #run_training_agent(game_data)
    run_manual_game(game_data)

main()