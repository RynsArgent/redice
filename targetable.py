import warnings
from game_data_obj import *
from die import *

class Targetable:
    def __init__(self, logger, target_type, team, location, label):
        self.logger = logger
        self.target_type = target_type
        # Red / Blue
        self.team = team
        # Front / Back
        self.location = location
        self.label = label

    def apply_effects(self, battlefield, source, effects, x):
        self.logger.warning('Expected to be overriden - applied to:{0}'.format(self.label))

"""
Instance of a Character in the Battlefield
"""
class Unit(Targetable):
    def __init__(self, logger, game_data, character, team, location, label):
        Targetable.__init__(self, logger, TargetType.UNIT, team, location, label)
        self.game_data = game_data
        # Character Data
        self.character = character
        # Tracked Unit Attributes
        self.current_health = character.max_health
        self.total_init = character.base_init
        # Determined at the start of battle to eliminate ties
        self.prec_init = 0
        # References to Instances of Die in play
        self.die = []
        for class_id in character.class_levels:
            num_die = character.class_levels[class_id]
            for i in range(num_die):
                self.die.append(ClassDie(game_data, class_id))

    def roll_all_available_die(self, rng):
        for dice in self.die:
            dice.roll_dice(rng)
    
    def get_die(self, die_index):
        if die_index < 0 or die_index >= len(self.die):
            return None
        return self.die[die_index]

    def is_dead(self):
        return self.current_health <= 0

    def get_percent_health(self):
        return self.current_health / self.character.max_health if self.character.max_health > 0 else 0.0

    def get_primary_class_index(self):
        class_id = self.character.primary_class_id
        class_data = self.game_data.get_row(SheetId.Classes, class_id)
        return class_data.index

    def get_details(self):
        return '{0}: {1}\n{2}/{3} HP'.format(self.label, self.character.name, self.current_health, self.character.max_health)

    def get_formatted_die(self):
        ret = ''
        for i in range(len(self.die)):
            die  = self.die[i]
            ret += 'DICE {0}: {1}\n'.format(i, die.get_details())
        return ret

    def apply_effects(self, battlefield, source, effects, x):
        for effect in effects:
            effect.apply(self.logger, battlefield, source, self, x)

"""
Contains information about the particular area (front or back line)
"""
class Area(Targetable):
    def __init__(self, logger, team, location, label):
        Targetable.__init__(self, logger, TargetType.AREA, team, location, label)
        self.units = []

    def add_unit(self, unit):
        self.units.append(unit)

    def remove_unit(self, unit):
        self.units.remove(unit)

    def apply_effects(self, battlefield, source, effects, x):
        for unit in self.units:
            unit.apply_effects(self.logger, battlefield, source, effects, x)

"""
Contains information about the entire section containing both front and the back line.
If an Effect needs to target all Enemies or All allies, querying the right Side will work
"""
class Side(Targetable):
    def __init__(self, logger, team, label):
        Targetable.__init__(self, logger, TargetType.SIDE, team, Location.NONE, label)
        self.front = Area(logger, team, Location.FRONT, label + '_front')
        self.back = Area(logger, team, Location.BACK, label + '_back')
        self.units = []
        self.dead_list = []

    def add_unit(self, unit):
        self.units.append(unit)
        if unit.location == Location.FRONT:
            self.front.add_unit(unit)
        elif unit.location == Location.BACK:
            self.back.add_unit(unit)
        else:
            self.logger.warning('Adding unit to side but unknown location:{0}'.format(unit.location))

    def remove_unit(self, unit):
        self.units.remove(unit)
        if unit.location == Location.FRONT:
            self.front.remove_unit(unit)
        elif unit.location == Location.BACK:
            self.back.remove_unit(unit)
        else:
            self.logger.warning('Removing unit to side but unknown location:{0}'.format(unit.location))

    def add_to_dead_list(self, unit):
        self.dead_list.append(unit)

    def get_frontmost_line(self):
        if len(self.front.units) > 0:
            return self.front
        elif len(self.back.units) > 0:
            return self.back
        return self.front

    def get_backmost_line(self):
        if len(self.back.units) > 0:
            return self.back
        elif len(self.front.units) > 0:
            return self.front
        return self.back

    def get_unit_count_in_line(self, location):
        if location == Location.FRONT:
            return len(self.front.units)
        elif location == Location.BACK:
            return len(self.back.units)
        return 0

    def apply_effects(self, battlefield, source, effects, x):
        for unit in self.units:
            unit.apply_effects(self.logger, battlefield, source, effects, x)

"""
Information of all enemies and allies in the environment
"""
class Battlefield(Targetable):
    def __init__(self, logger, units, label):
        Targetable.__init__(self, logger, TargetType.NONE, Team.NONE, Location.NONE, label)
        self.blue_side = Side(logger, Team.BLUE, label + '_blue')
        self.red_side = Side(logger, Team.RED, label + '_red')
        self.units = []
        self.dead_list = []
        for unit in units:
            self.add_unit(unit)

    def move_unit(self, unit):
        self.remove_unit(unit)
        if unit.location == Location.FRONT:
            unit.location = Location.BACK
        elif unit.location == Location.BACK:
            unit.location = Location.FRONT
        self.add_unit(unit)

    def add_unit(self, unit):
        self.units.append(unit)
        if unit.team == Team.BLUE:
            self.blue_side.add_unit(unit)
        elif unit.team == Team.RED:
            self.red_side.add_unit(unit)
        else:
            self.logger.warning('Adding unit to battlefield but unknown team:{0}'.format(unit.team))

    def remove_unit(self, unit):
        self.units.remove(unit)
        if unit.team == Team.BLUE:
            self.blue_side.remove_unit(unit)
        elif unit.team == Team.RED:
            self.red_side.remove_unit(unit)
        else:
            self.logger.warning('Removing unit from battlefield but unknown team:{0}'.format(unit.team))

    def add_to_dead_list(self, unit):
        # Add to dead list
        self.dead_list.append(unit)
        if unit.team == Team.BLUE:
            self.blue_side.add_to_dead_list(unit)
        elif unit.team == Team.RED:
            self.red_side.add_to_dead_list(unit)
        else:
            self.logger.warning('Adding unit to dead list but unknown team:{0}'.format(unit.team))

    def get_unit(self, unit_index):
        if unit_index < 0 or unit_index >= len(self.units):
            return None
        return self.units[self.unit_index]

    def get_unit_by_label(self, unit_label):
        for unit in self.units:
            if unit.label.lower() == unit_label.lower():
                return unit
        return None

    def get_frontmost_line(self, team):
        if team == team.BLUE:
            return self.blue_side.get_frontmost_line()
        elif team == team.RED:
            return self.red_side.get_frontmost_line()
        return None

    def get_backmost_line(self, team):
        if team == team.BLUE:
            return self.blue_side.get_backmost_line()
        elif team == team.RED:
            return self.red_side.get_backmost_line()
        return None

    def get_unit_count_in_line(self, team, location):
        if team == team.BLUE:
            return self.blue_side.get_unit_count_in_line(location)
        elif team == team.RED:
            return self.red_side.get_unit_count_in_line(location)
        return 0

    def get_all_units(self, team):
        if team == team.BLUE:
            return self.blue_side.units + self.blue_side.dead_list
        elif team == team.RED:
            return self.red_side.units + self.red_side.dead_list
        else:
            return self.units + self.dead_list

    def apply_effects(self, battlefield, source, effects, x):
        for unit in self.units:
            unit.apply_effects(battlefield, source, effects, x)

    def print_map(self):
        header = get_info_header('MAP')
        unknown = []
        blueBack = []
        blueFront = []
        redBack = []
        redFront = []
        for unit in self.units:
            if unit.team == Team.BLUE and unit.location == Location.BACK:
                blueBack.append(unit.label)
            elif unit.team == Team.BLUE and unit.location == Location.FRONT:
                blueFront.append(unit.label)
            elif unit.team == Team.RED and unit.location == Location.BACK:
                redBack.append(unit.label)
            elif unit.team == Team.RED and unit.location == Location.FRONT:
                redFront.append(unit.label)
            else:
                unknown.append(unit.label)

        self.logger.info(
"""{0}Back:\t{1}
Front:\t{2}

Front:\t{3}
Back:\t{4}\n""".format(header, ' '.join(redBack), ' '.join(redFront), ' '.join(blueFront), ' '.join(blueBack)))
                    
    def print_units(self):
        ret = get_info_header('UNITS')
        for unit in self.units:
            ret += unit.get_details() + '\n'
        self.logger.info(ret)
