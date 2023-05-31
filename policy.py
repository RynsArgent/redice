import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import gym
from collections import namedtuple

SavedAction = namedtuple('SavedAction', ['log_prob', 'value'])

"""
implements both actor and critic in one model
"""
class Policy(nn.Module):
    def __init__(self, observation_space, action_space):
        super(Policy, self).__init__()

        # Determine the input size for the neural network
        self.observation_space = observation_space
        self.action_space = action_space
        self.input_size = self.get_input_size()
        self.affine1 = nn.Linear(self.input_size, 128)
        self.affine2 = nn.Linear(128, 64)
        self.affine3 = nn.Linear(64, 128)

        # actor's layer
        self.output_size = self.get_output_size()

        self.action_head = nn.Linear(128, self.output_size)

        # critic's layer
        self.value_head = nn.Linear(128, 1)

        # action & reward buffer
        self.saved_actions = []
        self.rewards = []

    def forward(self, x):
        # forward of both actor and critic
        x = self.preprocess_observation(x)
        x = F.relu(self.affine1(x))
        x = F.relu(self.affine2(x))
        x = F.relu(self.affine3(x))

        # Actor: identify ideal actions to take from state x
        # by returning probability of each action
        action_prob = F.softmax(self.action_head(x), dim=-1)
        
        # Critic: evaluates being in the state x
        state_values = self.value_head(x)

        # Return values for both actor and critic as a tuple of 2 values:
        # 1. a list with the probability of each action over the action space
        # 2. the value from state s_t
        return action_prob, state_values

    def get_input_size(self):
        input_size = 0
        for var_key in self.observation_space.spaces.keys():
            if isinstance(self.observation_space[var_key], gym.spaces.Discrete):
                input_size += self.observation_space[var_key].n
            elif isinstance(self.observation_space[var_key], gym.spaces.Box):
                input_size += self.observation_space[var_key].shape[0]
        return input_size

    def get_output_size(self):
        # Assumes all discrete
        return np.prod([self.action_space[action].n for action in self.action_space.keys()])

    def preprocess_observation(self, x):
        # Preprocess discrete variables
        one_hot_encoded_discrete = []
        for var_key in self.observation_space.spaces.keys():
            if isinstance(self.observation_space[var_key], gym.spaces.Discrete):
                num_classes = self.observation_space[var_key].n
                one_hot_encoded = np.eye(num_classes)[x[var_key]]
                one_hot_encoded_discrete.extend(one_hot_encoded)

        # Preprocess continuous variables
        scaled_continuous = []
        for var_key in self.observation_space.spaces.keys():
            if isinstance(self.observation_space[var_key], gym.spaces.Box):
                lower_bound = self.observation_space[var_key].low
                upper_bound = self.observation_space[var_key].high
                scaled_value = (x[var_key] - lower_bound) / (upper_bound - lower_bound)
                scaled_continuous.extend(scaled_value)

        # Concatenate the preprocessed variables
        preprocessed_observation = np.concatenate((one_hot_encoded_discrete, scaled_continuous))
        # Convert the preprocessed observation to a PyTorch Tensor
        preprocessed_tensor = torch.from_numpy(preprocessed_observation).float()
        return preprocessed_tensor

