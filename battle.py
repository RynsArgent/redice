import warnings
import copy
import constants
from enum import Enum
from operator import attrgetter
from targetable import *
from battle_action import *

class BattleState(Enum):
    BATTLE_NOT_STARTED = 0
    START_PHASE = 1
    MAIN_PHASE = 2
    END_PHASE = 3
    BATTLE_FINISHED = 4

# Copy how the battle is constructed for us to reset to that state
class BattleSignature:
    def __init__(self, units):
        self.units = units

class Battle:
    def __init__(self, logger, units, random):
        self.logger = logger
        self.battlefield = Battlefield(logger, units, 'battlefield')
        self.rng = random
        self.signature = BattleSignature(units)
        self.reset()

    def reset(self):
        self.battlefield = Battlefield(self.logger, copy.deepcopy(self.signature.units), 'battlefield')
        self.round = 0
        # Number of turns which have passed
        self.turn = 0
        # Contains the list of units primarily ordered by their initiative
        self.turn_order = []
        # Current turn in the turn order
        self.turn_index = 0
        self.state = BattleState.BATTLE_NOT_STARTED
        # At a certain point, end the battle if this exceeds a threshold
        self.invalid_actions = 0

    # Return true if battle is over
    def step(self, action):
        self.step_update(action)
        self.step_transition(action)
        self.print_details()
        return self.state == BattleState.BATTLE_FINISHED

    # Core implementation of a Battle State we're in
    def step_update(self, action):
        if self.state == BattleState.BATTLE_NOT_STARTED:
            self.start_battle()
        elif self.state == BattleState.START_PHASE:
            self.start_turn()
            self.check_and_clear_invalid_units()
        elif self.state == BattleState.MAIN_PHASE:
            if action != None:
                if not action.can_ability_use_resources():
                    self.logger.warning('Cannot spend to use Primary Ability: {0}'.format(action.actor.label))
                elif not action.can_ability_be_used():
                    self.logger.warning('Primary Ability can not be used: {0}'.format(action.actor.label))
                elif not action.can_ability_apply_to_target():
                    self.logger.warning('Primary Ability can not apply to target: {0}'.format(action.actor.label))
                else:
                    action.act()
            else:
                self.invalid_actions += 1
            self.check_and_clear_invalid_units()
        elif self.state == BattleState.END_PHASE:
            self.end_turn()
            self.check_and_clear_invalid_units()
        else:
            self.logger.warning('Unknown Update for Battle State: {0}'.format(self.state))

    # Check for any potential transitions to another Battle State based on specific conditions
    def step_transition(self, action):
        if self.state == BattleState.BATTLE_NOT_STARTED:
            self.state = BattleState.START_PHASE
        elif self.state == BattleState.START_PHASE:
            if self.check_if_battle_over():
                self.state = BattleState.BATTLE_FINISHED
            else:
                self.state = BattleState.MAIN_PHASE
        elif self.state == BattleState.MAIN_PHASE:
            if self.check_if_battle_over():
                self.state = BattleState.BATTLE_FINISHED
            elif action != None and action.action_type == BattleActionType.END:
                self.state = BattleState.END_PHASE
        elif self.state == BattleState.END_PHASE:
            if self.check_if_battle_over():
                self.state = BattleState.BATTLE_FINISHED
            else:
                self.state = BattleState.START_PHASE
        else:
            self.logger.warning('Unknown Transition for Battle State: {0}'.format(self.state))

    def start_battle(self):
        self.logger.info(get_log_header('Battle Begins'))
        self.round = 0
        self.turn = 0
        self.turn_index = 0

    def start_round(self):
        self.logger.info(get_log_header('Round {0} Begins'.format(self.round)))
        units_ordered = self.battlefield.units.copy()
        sorted(units_ordered, key=attrgetter('total_init', 'prec_init'))
        self.turn_order = units_ordered

    def start_turn(self):
        if self.turn_index == 0:
            self.start_round()

        self.logger.info(get_log_header('Turn {0} Begins'.format(self.turn)))
        current_turn_unit = self.get_current_turn()
        current_turn_unit.roll_all_available_die(self.rng)

    def end_turn(self):
        self.logger.info(get_log_header('Turn {0} Ends'.format(self.turn)))
        self.turn += 1
        self.turn_index += 1
        if self.turn_index >= len(self.turn_order):
            self.end_round()

    def end_round(self):
        self.logger.info(get_log_header('Round {0} Ends'.format(self.round)))
        self.turn_index = 0
        self.round += 1

    # Delete units from tracked lists if they are dead
    def check_and_clear_invalid_units(self):
        units_cpy = self.battlefield.units.copy()
        for unit in units_cpy:
            if unit.current_health <= 0:
                self.clear_unit(unit)

    def clear_unit(self, unit):
        # Clear from battlefield list
        self.battlefield.remove_unit(unit)

        # Add to dead list
        self.battlefield.add_to_dead_list(unit)

        # Clear from turn order list
        unit_index = self.turn_order.index(unit)
        self.turn_order.pop(unit_index)
        # Update turn index if units past current turn
        if self.turn_index > unit_index:
            self.turn_index -= 1

    def get_target_by_index(self, target_type, target_index):
        if target_type == TargetType.UNIT:
            if target_index >= 0 and target_index < len(self.battlefield.units):
                return self.battlefield.units[target_index]
        elif target_type == TargetType.SIDE:
            if target_index == 0:
                return self.battlefield.blue_side
            elif target_index == 1:
                return self.battlefield.red_side
        elif target_type == TargetType.AREA:
            if target_index == 0:
                return self.battlefield.blue_side.front
            elif target_index == 1:
                return self.battlefield.blue_side.back
            elif target_index == 2:
                return self.battlefield.red_side.front
            elif target_index == 3:
                return self.battlefield.red_side.back
        return None

    def check_if_battle_over(self):
        # Arbitrary turn limit to avoid infinite loop
        if self.is_past_turn_limit():
            return True
        if self.invalid_actions > constants.INVALID_ACTION_LIMIT:
            return True
        # If at least one enemy and ally are alive, the battle is still going
        blue_count = len(self.battlefield.blue_side.units)
        red_count = len(self.battlefield.red_side.units)
        return blue_count == 0 or red_count == 0

    def is_past_turn_limit(self):
        return self.turn >= constants.TURN_LIMIT

    def get_winning_team(self):
        blue_count = len(self.battlefield.blue_side.units)
        red_count = len(self.battlefield.red_side.units)
        if blue_count > 0 and red_count == 0:
            return Team.BLUE
        elif blue_count == 0 and red_count > 0:
            return Team.RED
        return Team.NONE

    def get_current_turn(self):
        if self.turn_index < 0 or self.turn_index >= len(self.turn_order):
            return None
        return self.turn_order[self.turn_index]

    def print_details(self):
        # Print the battle layout
        self.battlefield.print_map()

        # Print most important unit details
        self.battlefield.print_units()

        if (len(self.turn_order) <= 0):
            return

        current_turn_unit = self.get_current_turn()
        if (current_turn_unit == None):
            self.logger.warning('Invalid turn index:{0} len:{1}'.format(self.turn_index, len(self.turn_order)))

        # Print turn order
        unit_labels = []
        for i in range(len(self.turn_order)):
            unit = self.turn_order[i]
            # Show current turn
            if i == self.turn_index:
                unit_labels.append('*{0}*'.format(unit.label))
            else:
                unit_labels.append(unit.label)

        self.logger.info('Turn Order: {0}'.format(' '.join(unit_labels)))

        if current_turn_unit != None:
            msg = get_info_header(current_turn_unit.label + ' TURN')
            msg += current_turn_unit.get_formatted_die()
            self.logger.info(msg)

        self.logger.info(self.state)
