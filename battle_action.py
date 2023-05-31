import warnings
from enum import IntEnum
from effect import *
from game_data import *

"""
Types of Battle Actions a Unit can do
"""
class BattleActionType(IntEnum):
    # Use the Die with the ability on the side the Die rolled on
    PRIMARY = 0
    # Use the Die to switch Locations
    MOVE = 1
    # End the Unit's turn
    END = 2

"""
Base class defining a unit performing an action. An action generally applies effects if successful
"""
class BattleAction:
    def __init__(self, logger, game_data, battlefield, actor, action_type):
        self.logger = logger
        self.game_data = game_data
        self.battlefield = battlefield
        self.actor = actor
        self.action_type = action_type
    
    def can_ability_use_resources(self):
        return True

    def can_ability_be_used(self):
        return True

    def can_ability_apply_to_target(self):
        return True

    def act(self):
        self.logger.warning('Expected to override for action of type:{0}'.format(self.action_type))

"""
Core mechanic of Actions where the ability on the Die applies an effect
"""
class BattleActionPrimary:
    def __init__(self, logger, game_data, battlefield, actor, primary_die, target):
        BattleAction.__init__(self, logger, game_data, battlefield, actor, BattleActionType.PRIMARY)
        self.primary_die = primary_die
        self.target = target 
    
    # Check if ability has enough mana, die, etc.
    def can_ability_use_resources(self):
        face_to_use = self.primary_die.get_rolled_face()
        return face_to_use != None

    # Check if ability can be used based on actor's position.
    # i.e. Melee must be used in the front
    def can_ability_be_used(self):
        face_to_use = self.primary_die.get_rolled_face()
        if face_to_use == None:
            return False
        face_data = self.game_data.get_row(SheetId.Faces, face_to_use.face_id)
        ability_data = self.game_data.get_row(SheetId.Abilities, face_data.ability_id)

        if ability_data.usage == AbilityUsage.MELEE:
            line = self.battlefield.get_frontmost_line(self.actor.team)
            return self.actor.location == line.location
        return True

    def can_ability_apply_to_target(self):
        face_to_use = self.primary_die.get_rolled_face()
        if face_to_use == None:
            return False
        face_data = self.game_data.get_row(SheetId.Faces, face_to_use.face_id)
        ability_data = self.game_data.get_row(SheetId.Abilities, face_data.ability_id)

        # Ensure target is correct object type
        if ability_data.target_type == TargetType.NONE:
            return self.target == None
        elif self.target == None or ability_data.target_type != self.target.target_type:
            return False
        
        # Ensure valid target is ally or enemy
        if ability_data.target_team == TargetTeam.ALLY:
            if self.actor.team != self.target.team:
                return False
        elif ability_data.target_team == TargetTeam.ENEMY:
            if self.actor.team == self.target.team:
                return False

        # If restrictions in where target is located
        elif ability_data.target_location == TargetLocation.FRONTMOST:
            if self.target is None:
                return False
            line = self.battlefield.get_frontmost_line(target.Team)
            if line is None or self.target.Location != line.Location:
                return False
        elif ability_data.target_location == TargetType.BACKMOST:
            if self.target is None:
                return False
            line = self.battlefield.get_backmost_line(target.Team)
            if line is None or self.target.Location != line.Location:
                return False
        return True

    def act(self):
        face_to_use = self.primary_die.get_rolled_face()
        if face_to_use == None:
            self.logger.warning('Unable to act - die is not rolled')
            return
        face_data = self.game_data.get_row(SheetId.Faces, face_to_use.face_id)
        ability_data = self.game_data.get_row(SheetId.Abilities, face_data.ability_id)

        # Iterate through the effects and apply
        if self.target is not None:
            x = face_to_use.x
            self.target.apply_effects(self.battlefield, self.actor, ability_data.effects, x)

        # Use the die
        self.primary_die.reset()

        return


"""
Expend a die to switch locations
"""
class BattleActionMove:
    def __init__(self, logger, game_data, battlefield, actor, die):
        BattleAction.__init__(self, logger, game_data, battlefield, actor, BattleActionType.MOVE)
        self.die = die
    
    def can_ability_use_resources(self):
        face_to_use = self.die.get_rolled_face()
        return face_to_use != None

    def can_ability_be_used(self):
        return True

    def can_ability_apply_to_target(self):
        return True

    def act(self):
        effect = EffectMove(0, 0)
        effect.apply(self.logger, self.battlefield, self.actor, self.actor, 0)

        # Use the die
        self.die.reset()

        return

"""
End the turn for the Unit
"""
class BattleActionEnd:
    def __init__(self, logger, game_data, battlefield, actor):
        BattleAction.__init__(self, logger, game_data, battlefield, actor, BattleActionType.END)
    
    def can_ability_use_resources(self):
        return True

    def can_ability_be_used(self):
        return True

    def can_ability_apply_to_target(self):
        return True

    def act(self):
        return
