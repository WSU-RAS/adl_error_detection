#!/usr/bin/env python

class Goal:
    size = 3
    BASE = 0
    HUMAN = 1
    OBJECT = 2
    types = {
        BASE: "Go to base",
        HUMAN: "Find human",
        OBJECT: "Guide to object"
    }

class Task:
    size = 3
    WATER_PLANTS = 0
    TAKE_MEDS = 1
    WALK_DOG = 2
    types = {
        WATER_PLANTS: "Water_Plants",
        TAKE_MEDS: "Take_Medication",
        WALK_DOG: "Walk_Dog"
    }

    @staticmethod
    def str_to_num(task_str):
        if Task.types[Task.WATER_PLANTS] == task_str:
            return Task.WATER_PLANTS
        elif Task.types[Task.TAKE_MEDS] == task_str:
            return Task.TAKE_MEDS
        elif Task.types[Task.WALK_DOG] == task_str:
            return Task.WALK_DOG
        else:
            return -1
