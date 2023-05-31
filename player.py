import warnings
import gym
from battle import *
from battle_action import *
from game_data import *
from game_data_obj import *
from policy import *
from torch.distributions import Categorical

"""
Base Player Class given the environment constructs a BattleAction for its turn
"""
class Player:
    def __init__(self, logger, game_data, battle_env, team):
        self.logger = logger
        self.game_data = game_data
        self.battle_env = battle_env
        self.team = team
        self.total_steps = 0
        self.total_reward = 0

    def reset_episode(self):
        self.total_steps = 0
        self.total_reward = 0

    def get_episode_details(self):
        return self.total_steps, self.total_reward

    def select_action(self):
        self.total_steps += 1
        unit = self.battle_env.battle.get_current_turn()
        if unit.team != self.team:
            self.logger.warning('Not player {0} turn: {1} is on team {2}'.format(self.team, unit.label, unit.team))
            return None
        return self.on_select_action(unit)

    def finish_episode(self):
        self.on_finish_episode()
        return

    def on_select_action(self, unit):
        self.logger.warning('Expected to override on_select_action')
        return None

    def on_finish_episode(self):
        self.logger.warning('Expected to override on_finish_episode')
        return

"""
Player Class accepting manual console-based input
"""
class ConsolePlayer(Player):
    def __init__(self, logger, game_data, battle_env, team):
        Player.__init__(self, logger, game_data, battle_env, team)

    def validate_argument_count(self, command, expected_arg_count, args):
        num_args = len(args)
        if num_args != expected_arg_count:
            self.logger.warning('Unexpected number of arguments for command:{0} expected:{1} found:{2}'.format(command, expected_arg_count, num_args))
            return False
        return True

    def try_parse_value(self, str, desc):
        ret = 0
        try:
            ret = int(str)
        except ValueError as ex:
            self.logger.warning('{0} cannot be converted to int - parsing for {1}'.format(str, desc))
        return ret

    def on_select_action(self, unit):
        self.logger.info('Enter Option (examples: <primary 0 E1>, <move 1>, <end>): ')
        player_input = input()
        player_input = player_input.strip(' \t\n')
        args = player_input.split()

        num_args = len(args)
        if num_args <= 0:
            self.logger.warning('Unknown input {0}'.format(player_input))
            return None

        cmd = args[0]
        if cmd == 'primary':
            if not self.validate_argument_count(cmd, 3, args):
                return None
            die_index = self.try_parse_value(args[1], 'die_index')
            die = unit.get_die(die_index)
            if die == None:
                self.logger.warning('Invalid Die index - primary for unit {0} index:{1}'.format(unit.label, die_index))
                return None
            target_label = args[2]
            target = self.battle_env.battle.battlefield.get_unit_by_label(target_label)
            if target == None:
                self.logger.warning('Invalid Target - label:{0}'.format(target_label))
                return None
            return BattleActionPrimary(self.logger, self.game_data, self.battle_env.battle.battlefield, unit, die, target)
        elif cmd == 'move':
            if not self.validate_argument_count(cmd, 2, args):
                return None
            die_index = self.try_parse_value(args[1], 'die_index')
            die = unit.get_die(die_index)
            if die == None:
                self.logger.warning('Invalid Die index - primary for unit {0} index:{1}'.format(unit.label, die_index))
                return None
            return BattleActionMove(self.logger, self.game_data, self.battle_env.battle.battlefield, unit, die)
        elif cmd == 'end':
            if not self.validate_argument_count(cmd, 1, args):
                return None
            return BattleActionEnd(self.logger, self.game_data, self.battle_env.battle.battlefield, unit)

        self.logger.warning('Invalid command:{0}'.format(cmd))
        return None

    def on_finish_episode(self):
        return

"""
Player Class doing simple, dumb and predictable AI behavior. 
"""
class NonPlayer(Player):
    def __init__(self, logger, game_data, battle_env, team, rng):
        Player.__init__(self, logger, game_data, battle_env, team)
        self.rng = rng

    def on_select_action(self, unit):
        potential_actions = []
        # Go through each die and use them in-order
        for die in unit.die:
            face_to_use = die.get_rolled_face()
            if face_to_use == None:
                continue

            face_data = self.game_data.get_row(SheetId.Faces, face_to_use.face_id)
            ability_data = self.game_data.get_row(SheetId.Abilities, face_data.ability_id)

            test_act = BattleActionPrimary(self.logger, self.game_data, self.battle_env.battle.battlefield, unit, die, None)
            if not test_act.can_ability_use_resources():
                continue
            if not test_act.can_ability_be_used():
                if ability_data.usage == AbilityUsage.MELEE:
                    # If melee ability which can't be used due to location, move forward
                    action = BattleActionMove(self.logger, self.game_data, self.battle_env.battle.battlefield, unit, die)
                    if action.can_ability_use_resources() and action.can_ability_be_used() and action.can_ability_apply_to_target():
                        potential_actions.append(action)
                        break
                continue

            # Find all possible targets for the ability on the given die
            potential_targets = []
            if ability_data.target_type == TargetType.UNIT:
                for target in self.battle_env.battle.battlefield.units:
                    potential_targets.append(target)
            elif ability_data.target_type == TargetType.AREA:
                potential_targets.append(self.battle_env.battle.battlefield.blue_side.front)
                potential_targets.append(self.battle_env.battle.battlefield.blue_side.back)
                potential_targets.append(self.battle_env.battle.battlefield.red_side.front)
                potential_targets.append(self.battle_env.battle.battlefield.red_side.back)
            elif ability_data.target_type == TargetType.SIDE:
                potential_targets.append(self.battle_env.battle.battlefield.blue_side)
                potential_targets.append(self.battle_env.battle.battlefield.red_side)
            else:
                potential_targets.append(None)
            
            # See which targets are possible as a target
            for target in potential_targets:
                action = BattleActionPrimary(self.logger, self.game_data, self.battle_env.battle.battlefield, unit, die, target)
                if action.can_ability_use_resources() and action.can_ability_be_used() and action.can_ability_apply_to_target():
                    potential_actions.append(action)

            # If we have a possible action, then use this die
            if len(potential_actions) > 0:
                break

        if len(potential_actions) > 0:
            return self.rng.choice(potential_actions)
        else:
            return BattleActionEnd(self.logger, self.game_data, self.battle_env.battle.battlefield, unit)

    def on_finish_episode(self):
        return

"""
Player Class doing simple, dumb and predictable AI behavior.
"""
class LearningAgent(Player):
    def __init__(self, logger, game_data, battle_env, team, gamma, epsilon, rho):
        Player.__init__(self, logger, game_data, battle_env, team)
        self.model = Policy(battle_env.observation_space, battle_env.action_space)
        self.optimizer = optim.Adam(self.model.parameters(), lr=3e-2)
        self.eps = np.finfo(np.float32).eps.item()
        self.gamma = gamma
        self.epsilon = epsilon
        self.rho = rho
        self.should_print_probabilities = False

    def calculate_reward(self):
        # Slightly penalize every step to mitigate the bot from stalling
        reward = constants.REWARD_AMOUNT_STEP_PENALTY

        if self.battle_env.battle.state == BattleState.BATTLE_FINISHED:
            # If the battle is over, tally the results.
            reward = 0

            player_units = []
            enemy_units = []
            if self.team == Team.BLUE:
                player_units = self.battle_env.battle.battlefield.get_all_units(Team.BLUE)
                enemy_units = self.battle_env.battle.battlefield.get_all_units(Team.RED)
            elif self.team == Team.RED:
                player_units = self.battle_env.battle.battlefield.get_all_units(Team.RED)
                enemy_units = self.battle_env.battle.battlefield.get_all_units(Team.BLUE)
            else:
                self.logger.warning('Unknown team calculating reward: {0}'.format(self.team))

            # Determine reward based on how the player's units survived
            player_unit_score = 0
            num_player_units = len(player_units)
            for unit in player_units:
                if not unit.is_dead():
                    percent_health = unit.get_percent_health()
                    player_unit_score += constants.REWARD_SCORE_PLAYER_UNIT_SURVIVING + constants.REWARD_SCORE_PLAYER_UNIT_HEALTH * percent_health
            reward += player_unit_score / num_player_units if num_player_units > 0 else 0

            # Determine reward based on how the enemy's units survived
            enemy_unit_score = 0
            num_enemy_units = len(enemy_units)
            for unit in enemy_units:
                if not unit.is_dead():
                    percent_health = unit.get_percent_health()
                    enemy_unit_score += constants.REWARD_SCORE_ENEMY_UNIT_SURVIVING + constants.REWARD_SCORE_ENEMY_UNIT_HEALTH * percent_health
            reward += enemy_unit_score / num_enemy_units if num_enemy_units > 0 else 0

            # Boost reward based on which team won. No team winning is a loss to the Agent
            winning_team = self.battle_env.battle.get_winning_team()
            if winning_team == self.team:
                reward += constants.REWARD_AMOUNT_WIN
            else:
                reward += constants.REWARD_AMOUNT_LOSS
        return reward

    # Creates a Battle Action from a dictionary defined in the Learning Agent's Action Space
    def create_battle_action(self, action, unit):
        action_type = action['action_type']
        die_index = action['die_index']
        target_index = action['target_index']

        ret = None
        if action_type == BattleActionType.PRIMARY:
            die = unit.get_die(die_index)
            face_to_use = die.get_rolled_face()
            if face_to_use != None:
                face_data = self.game_data.get_row(SheetId.Faces, face_to_use.face_id)
                ability_data = self.game_data.get_row(SheetId.Abilities, face_data.ability_id)
            
                target_type = ability_data.target_type
                target = self.battle_env.battle.get_target_by_index(target_type, target_index)
                ret = BattleActionPrimary(self.logger, self.game_data, self.battle_env.battle.battlefield, unit, die, target)
        elif action_type == BattleActionType.MOVE:
            die = unit.get_die(die_index)
            face_to_use = die.get_rolled_face()
            if face_to_use != None:
                ret = BattleActionMove(self.logger, self.game_data, self.battle_env.battle.battlefield, unit, die)
        elif action_type == BattleActionType.END:
            ret = BattleActionEnd(self.logger, self.game_data, self.battle_env.battle.battlefield, unit)

        return ret

    def on_select_action(self, unit):
        # Before selecting the next action. Evaluate how much reward we earned from our prior action.
        if len(self.model.saved_actions) > len(self.model.rewards):
            reward = self.calculate_reward()
            self.total_reward += reward
            self.model.rewards.append(reward)

        state = self.battle_env.get_observed_state()
        if (self.should_print_probabilities):
            self.print_action_probabilities(state)
        probs, state_value = self.get_action_probabilities(state)

        # create a categorical distribution over the list of probabilities of actions
        m = Categorical(probs)

        should_explore = False
        should_exploit = False
        if self.epsilon > 0:
            random_num = np.random.uniform()
            should_explore = random_num < self.epsilon
        if not should_explore and self.rho > 0:
            random_num = np.random.uniform()
            should_exploit = random_num < self.rho

        if should_explore:
            # Explore
            sampled_action = torch.randint(0, self.model.input_size, (1,))[0]
        elif should_exploit:
            # Exploit
            sampled_action = torch.argmax(probs)
        else:
            # Stochastic
            sampled_action = m.sample()

        # save to action buffer
        self.model.saved_actions.append(SavedAction(m.log_prob(sampled_action), state_value))

        # the action to take
        action_index = sampled_action.item()
        action = self.get_action_dict(action_index)
        battle_action = self.create_battle_action(action, unit)

        # Ensure the battle action can be used. If we pass none, this is similar to the
        # game rejecting the player input with the state not changing.
        if battle_action is not None and battle_action.can_ability_use_resources() and battle_action.can_ability_be_used() and battle_action.can_ability_apply_to_target():
            return battle_action
        else:
            # Return no action if it's invalid. 
            return None

    def get_action_dict(self, action_index):
        action_type = action_index // (2 * 6)        # Discrete(3)
        die_index = (action_index % (2 * 6)) // 6    # Discrete(2)
        target_index = (action_index % (2 * 6)) % 6  # Discrete(6)
        action = {}
        action['action_type'] = action_type
        action['die_index'] = die_index
        action['target_index'] = target_index
        return action

    def get_action_probabilities(self, state):
        probs, state_value = self.model(state)
        return (probs, state_value)

    def print_action_probabilities(self, state):
        print('Printing probabilities for state: {0}'.format(state))
        probs, state_value = self.model(state)
        for i in range(len(probs)):
            action = self.get_action_dict(i)
            print('{0:.3} - {1}'.format(probs[i], action))

    def on_finish_episode(self):
        # Before finishing. Evaluate how much reward we earned from our last action.
        if len(self.model.saved_actions) > len(self.model.rewards):
            reward = self.calculate_reward()
            self.total_reward += reward
            self.model.rewards.append(reward)
            
        # This is pulled from https://github.com/pytorch/examples.git
        # Training code. Calculates actor and critic loss and performs backprop.
        R = 0
        saved_actions = self.model.saved_actions
        policy_losses = []  # list to save actor (policy) loss
        value_losses = []   # list to save critic (value) loss
        returns = []        # list to save the true values

        # calculate the true value using rewards returned from the environment
        for r in self.model.rewards[::-1]:
            # calculate the discounted value
            R = r + self.gamma * R
            returns.insert(0, R)

        returns = torch.tensor(returns)
        returns = (returns - returns.mean()) / (returns.std() + self.eps)

        for (log_prob, value), R in zip(saved_actions, returns):
            advantage = R - value.item()

            # calculate actor (policy) loss
            policy_losses.append(-log_prob * advantage)

            # calculate critic (value) loss using L1 smooth loss
            value_losses.append(F.smooth_l1_loss(value, torch.tensor([R])))

        # reset gradients
        self.optimizer.zero_grad()

        # sum up all the values of policy_losses and value_losses
        loss = torch.stack(policy_losses).sum() + torch.stack(value_losses).sum()

        # perform backprop
        loss.backward()
        self.optimizer.step()

        # reset rewards and action buffer
        del self.model.rewards[:]
        del self.model.saved_actions[:]
