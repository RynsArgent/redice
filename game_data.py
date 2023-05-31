import json
import warnings
from game_data_obj import *
from enum import Enum

"""
Expected sheets contained in the JSON file
"""
class SheetId(Enum):
    Abilities = 0
    Classes = 1
    Faces = 2

"""
Manager to quickly access data objects from a JSON file
Ideally, we want this JSON file to be generated from a google spreadsheet
"""
class GameData:
    def __init__(self, filename):
        self.raw = self.load(filename)
        self.data = {}
        for sheet_id in self.raw:
            rows = {}
            sheet_data = self.raw[sheet_id]
            sheet_index = SheetId[sheet_id]
            for row_id in sheet_data:
                row_data = sheet_data[row_id]
                row_obj = None
                if sheet_index == SheetId.Abilities:
                    row_obj = AbilityData(row_data)
                elif sheet_index == SheetId.Classes:
                    row_obj = ClassData(row_data)
                elif sheet_index == SheetId.Faces:
                    row_obj = FaceData(row_data)
                else:
                    warnings.warn('Unknown sheet id {0}'.format(sheet_id))
                rows[row_id] = row_obj
            self.data[sheet_index] = rows
    
    def load(self, filename):
        # Opening JSON file
        f = open(filename)
        raw_json = json.load(f)
        # Closing file
        f.close()
        return raw_json

    def get_sheet(self, sheet_id):
        return self.data[sheet_id]

    def get_row(self, sheet_id, row_id):
        return self.data[sheet_id][row_id]

