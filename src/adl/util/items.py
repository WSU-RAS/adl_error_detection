#!/usr/bin/env python

from constants import Task
from dag import WaterPlantsDag, TakeMedicationDag, WalkDogDag
from dag import WaterPlantsWithLocationDag, TakeMedicationWithLocationDag, WalkDogWithLocationDag

# Decode item numbers are based on Estimote Pairings and Script 2.0
# Experiment Date: 2018-02-13

class TaskToDag(object):

    mapping = {
        Task.WATER_PLANTS: (WaterPlantsDag, WaterPlantsWithLocationDag),
        Task.TAKE_MEDS: (TakeMedicationDag, TakeMedicationWithLocationDag),
        Task.WALK_DOG: (WalkDogDag, WalkDogWithLocationDag)
    }

class Items(object):

    encode = {
        'W': (0, 'water_can', [Task.WATER_PLANTS]),
        'S': (1, 'sink_tap', [Task.WATER_PLANTS, Task.TAKE_MEDS]),
        'P1': (2, 'windowsill_plant', [Task.WATER_PLANTS]),
        'P2': (3, 'coffee_table_plant', [Task.WATER_PLANTS]),
        'P3': (4, 'side_table_plant', [Task.WATER_PLANTS]),
        'U': (5, 'umbrella', [Task.WALK_DOG]),
        'L': (6, 'leash', [Task.WALK_DOG]),
        'K': (7, 'keys', [Task.WALK_DOG]),
        'D': (8, 'dog', [Task.WALK_DOG]),
        'DR': (9, 'door', [Task.WALK_DOG]),
        'F': (10, 'food', [Task.TAKE_MEDS]),
        'C': (11, 'cup', [Task.TAKE_MEDS]),
        'M': (12, 'medication', [Task.TAKE_MEDS]),
        'CH': (13, 'chair', [Task.TAKE_MEDS]),
        'G': (14, 'garbage', [Task.TAKE_MEDS]),
        'PL': (15, 'pills', [Task.TAKE_MEDS]),
    }

    decode = {
        #Estimotes
        'EST323': 'U',
        'EST324': 'U',
        'EST321': 'L',
        'EST322': 'L',
        'EST319': 'K',
        'EST320': 'K',
        'EST327': 'D',
        'EST328': 'D',
        'EST325': 'DR',
        'EST326': 'DR',
        'D001': 'DR', #Smart Home sensor

        'EST317': 'F',
        'EST318': 'F',
        'EST311': 'C',
        'EST312': 'C',
        'EST313': 'M',
        'EST314': 'M',
        'EST329': 'G',
        'EST330': 'G',
        'D011': 'G', #Smart Home sensor
        'EST301': 'CH',
        'EST310': 'CH',

        'EST308': 'W',
        'EST309': 'W',
        'EST302': 'P3',
        'EST303': 'P3',
        'EST306': 'P1',
        'EST307': 'P1',
        'EST304': 'P2',
        'EST305': 'P2',
        'EST315': 'S',
        'EST316': 'S',

        #Old Sensor
        'EST096': 'U',
        'EST097': 'U',
        'EST073': 'L',
        'EST074': 'L',
        'EST030': 'K',
        'EST123': 'K',
        'EST122': 'D',
        'EST100': 'D',
        'EST071': 'DR',
        'EST023': 'DR',

        'EST098': 'F',
        'EST099': 'F',
        'EST079': 'C',
        'EST080': 'C',
        'EST089': 'M',
        'EST090': 'M',
        'EST075': 'G',
        'EST076': 'G',
        'EST011': 'CH',
        'EST078': 'CH',

        'EST022': 'W',
        'EST124': 'W',
        'EST024': 'P3',
        'EST086': 'P3',
        'EST087': 'P1',
        'EST088': 'P1',
        'EST083': 'P2',
        'EST084': 'P2',
        'EST093': 'S',
        'EST121': 'S',
    }

class Locations(object):

    encode = {
        'L': (0, 'living_entertainment', [Task.WALK_DOG, Task.TAKE_MEDS, Task.WATER_PLANTS]),
        'LD': (1, 'living_dining', [Task.WALK_DOG, Task.TAKE_MEDS, Task.WATER_PLANTS]),
        'K': (2, 'kitchen', [Task.TAKE_MEDS, Task.WATER_PLANTS]),
        'KH': (3, 'kitchen_hallway', [Task.WALK_DOG]),
        'H': (4, 'hallway', [Task.WALK_DOG])
    }

    decode = {
        #Ambient sensors

        #Living room left side
        'M002': 'L', 'M003': 'L',
        'M006': 'LD', 'M007': 'LD',

        #Living room to Dining room
        'M008': 'LD',

        #Dining room
        'M009': 'LD', 'M010': 'LD',
        'M013': 'LD', 'M014': 'LD',

        #Kitchen
        'M016': 'K', 'M017': 'K', 'M018': 'K',

        #Kitchen window
        'M051': 'K',

        #Kitchen hallway
        'M019': 'KH',

        #Hallway
        'M023': 'H', 'M021': 'H',
        'M022': 'H', 'M024': 'H', 'M025': 'H',
        'M060': 'H', 'M059': 'H', 'M058': 'H', 'M057': 'H', 'M056': 'H',
        'M055': 'H', 'M054': 'H'
    }
