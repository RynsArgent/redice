from battle import *
from gym.spaces import *
import warnings
import gym
import numpy as np

"""
Wrapper around the Battle class with Open AI Gym
"""
class BattleEnv(gym.Env):
    def __init__(self, logger, battle):
        self.logger = logger
        self.battle = battle

        # Define all output features for the Actor which can create all possible Battle Actions
        # action_type - BattleActionType
        # die_index - index to Unit.die
        # target_index - index to the Targetable. This is based on TargetType
        self.action_space = Dict(
            {
                "action_type": Discrete(3),
                "die_index": Discrete(2),
                "target_index": Discrete(6),
            }
        )

        # Define all input features which is the observable Battle state.
        # turn - Number of turns which have elapsed
        # die1_face - The facing of the first die, 0 means it's inactive - this is an index of Facing in Game Data
        # die2_face - The facing of the second die, 0 means it's inactive - this is an index of Facing in Game Data
        # blue_hp1 - Health of the first blue unit, 0 means non-existant or dead
        # blue_class1 - Primary class of the first blue unit, 0 means non-existant - This is an index of Class in Game Data
        # blue_hp2 - Health of the second blue unit, 0 means non-existant or dead
        # blue_class2 - Primary class of the second blue unit, 0 means non-existant - This is an index of Class in Game Data
        # red_hp1 - Health of the first red unit, 0 means non-existant or dead
        # red_class1 - Primary class of the first red unit, 0 means non-existant - This is an index of Class in Game Data
        # red_hp2 - Health of the second red unit, 0 means non-existant or dead
        # red_class2 - Primary class of the second red unit, 0 means non-existant - This is an index of Class in Game Data
        # TODO: Create an object for { blue_hp1, blue_class1 } to add any extra information we care about the Unit
        # TODO: Add Turn Order information
        self.observation_space = Dict(
            {
                "turn": Box(low=0.0, high=100.0),
                "die1_face": Discrete(4),
                "die2_face": Discrete(4),
                "blue_hp1": Box(low=0.0, high=20.0),
                "blue_class1": Discrete(3),
                "blue_hp2": Box(low=0.0, high=20.0),
                "blue_class2": Discrete(3),
                "red_hp1": Box(low=0.0, high=20.0),
                "red_class1": Discrete(3),
                "red_hp2": Box(low=0.0, high=20.0),
                "red_class2": Discrete(3),
            }
        )

    def change_battle(self, battle):
        self.battle = battle

    def step(self, action):
        info = None
        unit_turn = self.battle.get_current_turn()
        if action != None and unit_turn != action.actor:
            self.logger.warning('Attempting to perform step using action which is wrong turn - expected:{0} seeing:{1}'.format(unit_turn.label, action.actor.label))
            return self.get_observed_state(), 0, False, False, info

        reward = 0
        is_done = False
        is_terminated = False
        if self.battle.state != BattleState.BATTLE_FINISHED:
            is_done = self.battle.step(action)
            is_terminated = self.battle.is_past_turn_limit()
        
        next_state = self.get_observed_state()
        return next_state, 0, is_done, is_terminated, info

    def get_observed_state(self):
        unit = self.battle.get_current_turn()

        die = unit.die if unit is not None else []
        num_die = len(die)
        die1_face = None
        die2_face = None
        if num_die >= 1:
            die1_face = die[0].get_rolled_face()
        if num_die >= 2:
            die2_face = die[1].get_rolled_face()

        blue1 = None
        blue2 = None
        red1 = None
        red2 = None

        blue_units = self.battle.battlefield.get_all_units(Team.BLUE)
        red_units = self.battle.battlefield.get_all_units(Team.RED)
        if (len(blue_units) > 0):
            blue1 = blue_units[0]
        if (len(blue_units) > 1):
            blue2 = blue_units[1]
        if (len(red_units) > 0):
            red1 = red_units[0]
        if (len(red_units) > 1):
            red2 = red_units[1]
        
        observation = {}
        observation['turn'] = self.battle.turn
        observation['die1_face'] = die1_face.index if die1_face is not None else 0
        observation['die2_face'] = die2_face.index if die2_face is not None else 0
        observation['blue_hp1'] = blue1.current_health if blue1 is not None else 0
        observation['blue_class1'] = blue1.get_primary_class_index() if blue1 is not None else 0
        observation['blue_hp2'] = blue2.current_health if blue2 is not None else 0
        observation['blue_class2'] = blue2.get_primary_class_index() if blue2 is not None else 0
        observation['red_hp1'] = red1.current_health if red1 is not None else 0
        observation['red_class1'] = red1.get_primary_class_index() if red1 is not None else 0
        observation['red_hp2'] = red2.current_health if red2 is not None else 0
        observation['red_class2'] = red2.get_primary_class_index() if red2 is not None else 0
        return observation

    def reset(self):
        self.battle.reset()
        return None
  
    def render(self, mode='human'):
        pass

    def close(self):
        pass
