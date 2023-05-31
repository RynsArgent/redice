from game_data import *

"""
Information of a Player or NPC in the world.
"""
class Character:
    def __init__(self, game_data, name, class_uids):
        self.game_data = game_data
        self.class_levels = {}
        self.name = ""
        self.max_health = 0
        self.base_init = 0
        self.primary_class_id = ""
        for class_uid in class_uids:
            self.__add_level(class_uid)
        self.__compute_max_health()
        self.__compute_base_init()
            
    def __add_level(self, class_uid):
        if class_uid in self.class_levels:
            self.class_levels[class_uid] = self.class_levels[class_uid] + 1
        else:
            self.class_levels[class_uid] = 1
        if not self.primary_class_id:
            self.primary_class_id = class_uid

    def gain_level(self, class_uid):
        self.__add_level(class_uid)
        self.__compute_max_health()
        self.__compute_base_init()

    def __compute_max_health(self):
        total_health = 0
        for class_id in self.class_levels:
            class_level = self.class_levels[class_id]
            class_data = self.game_data.get_row(SheetId.Classes, class_id)
            total_health += class_data.health * class_level
        self.max_health = total_health

    def __compute_base_init(self):
        if len(self.class_levels) <= 0:
            self.base_init = 0
            return
        total_init = 0
        total_levels = 0
        for class_id in self.class_levels:
            class_level = self.class_levels[class_id]
            class_data = self.game_data.get_row(SheetId.Classes, class_id)
            total_init += class_data.init * class_level
            total_levels += class_level
        self.base_init = total_init / total_levels
