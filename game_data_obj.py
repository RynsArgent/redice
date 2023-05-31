import constants
import warnings
from effect import *
from enum import Enum, IntEnum

'''
Locations in Redice are basic. A unit can only be in the Front or the Back on their Side
'''
class Location(IntEnum):
    NONE = 0
    BACK = 1
    FRONT = 2

'''
Team Color Assignment
'''
class Team(Enum):
    NONE = 0
    BLUE = 1
    RED = 2

'''
Ability Categorization
'''
class AbilityType(Enum):
    ATTACK = 0
    SUPPORT = 1
    SPELL = 2
    SKILL = 3

'''
How the Ability is used and the requirements that go with that usage
(i.e. MELEE requires the Unit to be in the frontmost line)
'''
class AbilityUsage(Enum):
    NONE = 0
    MELEE = 1
    RANGED = 2

'''
Whether the Ability should target a specific Unit, Area, or Side
'''
class TargetType(IntEnum):
    NONE = 0
    UNIT = 1
    AREA = 2
    SIDE = 3

'''
Target Team Affiliation Requirements for an Ability
'''
class TargetTeam(IntEnum):
    NONE = 0
    ENEMY = 1
    ALLY = 2

'''
Target Location Requirements for an Ability
'''
class TargetLocation(IntEnum):
    NONE = 0
    FRONTMOST = 1
    BACKMOST = 2

"""
Game Data defining an Ability
"""
class AbilityData:
    def __init__(self, ability_data):
        self.uid = ability_data['uid']
        self.name = ability_data['name']
        self.type = AbilityType[ability_data['type']]
        self.usage = AbilityUsage[ability_data['usage']]
        self.target_type = TargetType[ability_data['target_type']]
        self.target_team = TargetTeam[ability_data['target_team']]
        self.target_location = TargetLocation[ability_data['target_location']]
        self.effects = []
        keys_str = ability_data['keys']
        keys_str = keys_str.strip(' \t\n')
        keys = keys_str.split(';')
        for key_str in keys:
            key_str = key_str.strip(' \t\n')
            components = key_str.split()
            num_components = len(components)
            if (num_components > 0):
                # Parse properties like DAMAGE 2 or HEAL 3
                # Parsing DAMAGE X means X is dependent on the die value
                # We want also APPLY 3 POISON 
                # Would be great also to support DAMAGE 2X
                comp0 = components[0].strip(' \t\n')
                effect_type = EffectType[comp0]

                m = 0
                c = 0
                # Parse the value component
                if (num_components > 1):
                    comp1 = components[1].strip(' \t\n')
                    if comp1.lower() == 'x':
                        m = 1
                    else:
                        try:
                            c = int(comp1)
                        except ValueError as ex:
                            warnings.warn('{0} cannot be converted to int - ability {1}'.format(comp1, self.uid))
                        return ret
                else:
                    # By default if no value is specified set constant to 1
                    c = 1

                # Generate and cache the generated effect
                effect = None
                if effect_type == EffectType.DAMAGE:
                    effect = EffectDamage(m, c)
                    
                if effect != None:
                    self.effects.append(effect)
                else:
                    warnings.warn('Unable to create Effect of type {0} components for ability:{1}'.format(effect_type, self.uid))

    def get_details(self):
        return 'ABILITY {0} - {1}'.format(self.uid, self.type)

"""
Game Data defining a Side of a Die
"""
class FaceData:
    def __init__(self, face_data):
        self.uid = face_data['uid']
        self.index = face_data['index']
        self.ability_id = face_data['ability_id']
        self.base_x = face_data['base_x']

    def get_details(self):
        return 'FACE {0} - {1} {2}'.format(self.uid, self.ability_id, self.base_x)

def get_info_header(content):
    size = len(content)
    ret = ''
    ret += '#' * (4 + size) + '\n'
    ret += '# ' + content + ' #\n'
    ret += '#' * (4 + size) + '\n'
    return ret

def get_log_header(content):
    ret = '-' * (5) + ' ' + content
    return ret

"""
Game Data defining a Class
"""
class ClassData:
    def __init__(self, class_data):
        self.uid = class_data['uid']
        self.index = class_data['index']
        self.name = class_data['name']
        self.health = class_data['health']
        self.init = class_data['init']
        self.tier = class_data['tier']
        self.faces = [None] * constants.NUM_DIE_FACES
        for i in range(constants.NUM_DIE_FACES):
            self.faces[i] = class_data['face_{0}'.format(i + 1)]

    def get_details(self):
        return 'CLASS {0} - {1} health:{2} init:{3} tier:{4} faces:{5}'.format(
            self.uid,
            self.name,
            self.health,
            self.init,
            self.tier,
            ','.join(self.faces))