import warnings
from enum import Enum

"""
Types of Effects alter game state in different ways
"""
class EffectType(Enum):
    DAMAGE = 0
    MOVE = 1
    HEAL = 2
    BUFF = 3

"""
Base class defining game state changes against Entities
Entities apply effects using Abilities
There can be Global Effects as well
"""
class Effect:
    def __init__(self, effect_type, m, c):
        self.effect_type = effect_type
        # Store values simply as M * X + C
        self.m = m
        self.c = c

    # Perform the game state change to the target unit
    def apply(self, logger, battlefield, source, target, x):
        logger.warning('Expected to override for action of type:{0}'.format(self.effect_type))

"""
Apply damage to a target reducing their health
"""
class EffectDamage(Effect):
    def __init__(self, m, c):
        Effect.__init__(self, EffectType.DAMAGE, m, c)

    # Apply health reduction against the target unit
    def apply(self, logger, battlefield, source, target, x):
        # Ensure damage isn't negative
        final_amount = max(0, self.m * x + self.c)
        # Ensure damage doesn't cause target to go under 0
        final_amount = min(final_amount, target.current_health)
        target.current_health -= final_amount
        logger.info('{0} deals {1} damage to {2}'.format(source.label, final_amount, target.label))

"""
Move the target swapping their positions on their side
"""
class EffectMove(Effect):
    def __init__(self, m, c):
        Effect.__init__(self, EffectType.MOVE, m, c)

    # Swap positions for the target
    def apply(self, logger, battlefield, source, target, x):
        battlefield.move_unit(target)
        logger.info('{0} moves {1} to {2}'.format(source.label, target.label, target.location))
