import constants
from game_data import *

"""
Game Data defining a Class
"""
class DieFace:
    def __init__(self, game_data, face_id):
        self.game_data = game_data
        self.face_id = face_id
        face_data = game_data.get_row(SheetId.Faces, face_id)
        self.index = face_data.index
        self.x = face_data.base_x

    def get_details(self):
        face_data = self.game_data.get_row(SheetId.Faces, self.face_id)
        return  '{0}-{1}'.format(face_data.ability_id, self.x)


"""
Base Die for a Unit
"""
class BaseDie:
    def __init__(self, game_data, faces):
        self.game_data = game_data
        self.faces = faces
        self.roll = -1

    def reset(self):
        self.roll = -1

    def roll_dice(self, rng):
        self.roll = rng.randint(0, constants.NUM_DIE_FACES - 1)

    def get_face(self, face_index):
        if face_index < 0 or face_index >= constants.NUM_DIE_FACES:
            return None
        return self.faces[face_index]

    def get_rolled_face(self):
        return self.get_face(self.roll)

    def get_details(self):
        ret = ''
        for i in range(len(self.faces)):
            face = self.faces[i]
            face_details = face.get_details()
            if self.roll == i:
                ret += '[*{0}*]'.format(face_details)
            else:
                ret += '[ {0} ]'.format(face_details)
        return ret

"""
Class Die for a Unit
"""
class ClassDie(BaseDie):
    def __init__(self, game_data, class_id):
        self.class_id = class_id
        faces = [None] * constants.NUM_DIE_FACES
        class_data = game_data.get_row(SheetId.Classes, class_id)
        class_faces = class_data.faces
        for i in range(constants.NUM_DIE_FACES):
            face_id = class_faces[i]
            faces[i] = DieFace(game_data, face_id)
        BaseDie.__init__(self, game_data, faces)

"""
Generated Die which are temporary for a Unit
"""
class GeneratedDie(BaseDie):
    def __init__(self, game_data, faces):
        BaseDie.__init__(self, game_data, faces)
