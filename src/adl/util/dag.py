#!/usr/bin/env python
'''
Estimotes:
W   watercan                F   food/snack
S   sink                    C   cup
P1  windowsill plant        M   medication
P2  coffee table plant      CH  chair
P3  side table plant        G   garbage
U   umbrella
L   leash
K   keys
D   dog
DR  door

Location Change:
L>K living_room to kitchen
K>L kitchen to living_room
L>H living_room to hallway
H>KH hallway to kitchen_hallway
KH>H kitchen_hallway to kitchen
'''


class WaterPlantsDag(object):

    return_can = {
        'allow': ['S', 'W'],
        'Done': ['W'],
        'current': 'return_can',
        'next': 'Done'
    }
    rinse_can = {
        'allow': ['S', 'P3', 'P2', 'W'],
        'S': return_can,
        'current': 'rinse_can',
        'next': 'return_can'
    }
    water_plantside = {
        'allow': ['P3', 'P2', 'W'],
        'P3': rinse_can,
        'current': 'water_plantside',
        'next': 'rinse_can'
    }
    water_plantcoffee = {
        'allow': ['P2', 'S', 'W'],
        'P2': water_plantside,
        'current': 'water_plantcoffee',
        'next': 'water_plantside'
    }
    fill_can = {
        'allow': ['S', 'W'],
        'S': water_plantcoffee,
        'current': 'fill_can',
        'next': 'water_plantcoffee'
    }
    get_can = {
        'allow': ['W'],
        'W': fill_can,
        'current': 'get_can',
        'next': 'fill_can'
    }
    task_end = return_can
    task_start = get_can

    subtask = {
        'get_can': 0,
        'fill_can': 1,
        'water_plantcoffee': 2,
        'water_plantside': 3,
        'rinse_can': 4,
        'return_can': 5,
        'Done': 6
    }
    subtask_info = {
        # Note: for now we'll just show the button "guide me to object" for objects to
        # be retreived since we aren't tracking them as they're moving.
        #   (description              , query object , code, current dag , next dag if error)
        0: ('Retrieve water can'      , 'watercan'   , 'W' , get_can          , fill_can),
        1: ('Fill water can'          , 'sink'       , 'S' , fill_can         , water_plantcoffee),
        2: ('Water coffee table plant', 'plantcoffee', 'P2', water_plantcoffee, rinse_can),
        3: ('Water side table plant'  , 'plantside'  , 'P3', water_plantside  , rinse_can),
        4: ('Rinse water can'         , 'sink'       , 'S' , rinse_can        , return_can),
        5: ('Return water can'        , None         , 'W' , return_can       , None),
        6: ('Completed'               , None         , None, None             , None)
    }
    num_tasks = 6

class WaterPlantsWithLocationDag(object):

    return_can = {
        'allow': ['LD>L', ('W', 'L'), 'S', 'W', 'L>LD', 'K>LD', 'LD>K'],
        'Done': ['LD>L', ('W', 'L')],
        'current': 'return_can',
        'next': 'Done'
    }
    rinse_can = {
        'allow': ['S', 'P3', 'P2', 'W', 'LD>K', 'K>LD', 'LD>L', 'L>LD'],
        'S': return_can,
        'current': 'rinse_can',
        'next': 'return_can'
    }
    water_plantside = {
        'allow': ['P3', 'P2', 'W', 'L>LD', 'LD>L'],
        'P3': rinse_can,
        'current': 'water_plantside',
        'next': 'rinse_can'
    }
    water_plantcoffee = {
        'allow': ['P2', 'S', 'W', 'K>LD', 'LD>K', 'LD>L', 'L>LD'],
        'P2': water_plantside,
        'current': 'water_plantcoffee',
        'next': 'water_plantside'
    }
    fill_can = {
        'allow': ['S', 'LD>L', 'L>LD', 'LD>K', 'K>LD', 'W'],
        'S': water_plantcoffee,
        'current': 'fill_can',
        'next': 'water_plantcoffee'
    }
    get_can = {
        'allow': ['W', 'L>LD', 'LD>L'],
        'W': fill_can,
        'current': 'get_can',
        'next': 'fill_can'
    }
    task_end = return_can
    task_start = get_can

    subtask = {
        'get_can': 0,
        'fill_can': 1,
        'water_plantcoffee': 2,
        'water_plantside': 3,
        'rinse_can': 4,
        'return_can': 5,
        'Done': 6
    }
    subtask_info = {
        # Note: for now we'll just show the button "guide me to object" for objects to
        # be retreived since we aren't tracking them as they're moving.
        #   (description              , query object , code , current dag , next dag if error)
        0: ('Retrieve water can'      , 'watercan'   , 'W'  , get_can          , fill_can),
        1: ('Fill water can'          , 'sink'       , 'S'  , fill_can         , water_plantcoffee),
        2: ('Water coffee table plant', 'plantcoffee', 'P2' , water_plantcoffee, rinse_can),
        3: ('Water side table plant'  , 'plantside'  , 'P3' , water_plantside  , rinse_can),
        4: ('Rinse water can'         , 'sink'       , 'S'  , rinse_can        , return_can),
        5: ('Return water can'        , None         , 'K>L', return_can       , None),
        6: ('Completed'               , None         , None , None             , None)
    }
    num_tasks = 6


class WalkDogDag(object):

    exit_house = {
        'allow': ['DR', 'U', 'L', 'K', 'D'],
        'Done': ['DR'],
        'current': 'exit_house',
        'next': 'Done'
    }
    leash_dog = {
        'allow': ['D', 'U', 'L', 'K'],
        'D': exit_house,
        'current': 'leash_dog',
        'next': 'exit_house'
    }
    get_keys = {
        'allow': ['K', 'U', 'L'],
        'K': leash_dog,
        'current': 'get_keys',
        'next': 'leash_dog'
    }
    get_leash = {
        'allow': ['L', 'U'],
        'L': get_keys,
        'current': 'get_leash',
        'next': 'get_keys'
    }
    get_umbrella = {
        'allow': ['U'],
        'U': get_leash,
        'current': 'get_umbrella',
        'next': 'get_leash'
    }
    task_end = exit_house
    task_start = get_umbrella

    subtask = {
        'get_umbrella': 0,
        'get_leash': 1,
        'get_keys': 2,
        'leash_dog': 3,
        'exit_house': 4,
        'Done': 5
    }
    subtask_info = {
        #   (description       , query object, code, current dag , next dag if error)
        0: ('Retrieve Umbrella', 'umbrella'  , 'U' , get_umbrella, get_keys),
        1: ('Retrieve Leash'   , 'leash'     , 'L' , get_leash   , leash_dog),
        2: ('Retrieve Keys'    , 'keys'      , 'K' , get_keys    , exit_house),
        3: ('Leash Dog'        , 'dog'       , 'D' , leash_dog   , exit_house),
        4: ('Exit'             , None        , 'DR', exit_house  , None),
        5: ('Completed'        , None        , None, None        , None)
    }
    num_tasks = 5

class WalkDogWithLocationDag(object):

    exit_house = {
        'allow': ['DR', 'U', 'L', 'K', 'H>KH', 'KH>H', 'D'],
        'Done': ['DR'],
        'current': 'exit_house',
        'next': 'Done'
    }
    leash_dog = {
        'allow': ['D', 'U', 'L', 'K', 'H>KH', 'KH>H'],
        'D': exit_house,
        'current': 'leash_dog',
        'next': 'exit_house'
    }
    get_keys = {
        'allow': ['K', 'U', 'L', 'KH>H', 'H>KH'],
        'K': leash_dog,
        'current': 'get_keys',
        'next': 'leash_dog'
    }
    get_leash = {
        'allow': ['L', 'U'],
        'L': get_keys,
        'current': 'get_leash',
        'next': 'get_keys'
    }
    get_umbrella = {
        'allow': ['U', 'L>H', 'LD>H', 'H>LD', 'L>LD', 'LD>L'],
        'U': get_leash,
        'current': 'get_umbrella',
        'next': 'get_leash'
    }
    task_end = exit_house
    task_start = get_umbrella

    subtask = {
        'get_umbrella': 0,
        'get_leash': 1,
        'get_keys': 2,
        'leash_dog': 3,
        'exit_house': 4,
        'Done': 5
    }
    subtask_info = {
        #   (description       , query object, code, current dag , next dag if error)
        0: ('Retrieve Umbrella', 'umbrella'  , 'U' , get_umbrella, get_keys),
        1: ('Retrieve Leash'   , 'leash'     , 'L' , get_leash   , leash_dog),
        2: ('Retrieve Keys'    , 'keys'      , 'K' , get_keys    , exit_house),
        3: ('Leash Dog'        , 'dog'       , 'D' , leash_dog   , exit_house),
        4: ('Exit'             , None        , 'DR', exit_house  , None),
        5: ('Completed'        , None        , None, None        , None)
    }
    num_tasks = 5

class TakeMedicationDag(object):

    throw_garbage = {
        'allow': ['G', 'S', 'C', 'F'],
        'Done': ['G'],
        'current': 'throw_garbage',
        'next': 'Done'
    }
    rinse_cup = {
        'allow': ['S', 'CH', 'C', 'M', 'F'],
        'S': throw_garbage,
        'current': 'rinse_cup',
        'next': 'throw_garbage'
    }
    stand_up = {
        'allow': ['CH', 'C', 'M', 'F'],
        'CH': rinse_cup,
        'current': 'stand_up',
        'next': 'rinse_cup'
    }
    drink_water = {
        'allow': ['C', 'M', 'F'],
        'C': stand_up,
        'current': 'drink_water',
        'next': 'stand_up'
    }
    take_med = {
        'allow': ['M', 'F'],
        'M': drink_water,
        'current': 'take_med',
        'next': 'drink_water'
    }
    eat_food = {
        'allow': ['F', 'C', 'CH'],
        'F': take_med,
        'current': 'eat_food',
        'next': 'take_med'
    }
    sit_chair = {
        'allow': ['CH', 'M', 'C', 'F'],
        'CH': eat_food,
        'current': 'sit_chair',
        'next': 'eat_food'
    }
    get_med = {
        'allow': ['M', 'S', 'C', 'F'],
        'M': sit_chair,
        'current': 'get_med',
        'next': 'sit_chair'
    }
    fill_cup = {
        'allow': ['S', 'C', 'F'],
        'S': get_med,
        'current': 'fill_cup',
        'next': 'get_med'
    }
    get_cup = {
        'allow': ['C', 'F'],
        'C': fill_cup,
        'current': 'get_cup',
        'next': 'fill_cup'
    }
    get_food = {
        'allow': ['F'],
        'F': get_cup,
        'current': 'get_food',
        'next': 'get_cup'
    }
    task_end = throw_garbage
    task_start = get_food

    subtask = {
        'get_food': 0,
        'get_cup': 1,
        'fill_cup': 2,
        'get_med': 3,
        'sit_chair': 4,
        'eat_food': 5,
        'take_med': 6,
        'drink_water': 7,
        'stand_up': 8,
        'rinse_cup': 9,
        'throw_garbage': 10,
        'Done': 11
    }
    subtask_info = {
        #   (description          , query object, code, current dag  , next dag if error)
        0:  ('Retrieve food'      , 'food'      , 'F' , get_food     , fill_cup),
        1:  ('Retrieve cup'       , 'glass'     , 'C' , get_cup      , fill_cup),
        2:  ('Fill cup'           , 'sink'      , 'S' , fill_cup     , sit_chair),
        3:  ('Retrieve medication', 'pillbottle', 'M' , get_med      , eat_food),
        4:  ('Sit chair'          , None        , 'CH', sit_chair    , take_med),
        5:  ('Eat food'           , None        , 'F' , eat_food     , drink_water),
        6:  ('Take medication'    , 'pills'     , 'PL' , take_med     , stand_up),
        7:  ('Drink water'        , None        , 'C' , drink_water  , rinse_cup),
        8:  ('Stand up'           , None        , 'CH', stand_up     , throw_garbage),
        9:  ('Rinse cup'          , 'sink'      , 'C' , rinse_cup    , None),
        10: ('Throw garbage'      , None        , 'G' , throw_garbage, None),
        11: ('Completed'          , None        , None, None         , None)
    }
    num_tasks = 11

class TakeMedicationWithLocationDag(object):

    throw_garbage = {
        'allow': ['G', 'C', 'F', 'S'],
        'Done': ['G'],
        'current': 'throw_garbage',
        'next': 'Done'
    }
    rinse_cup = {
        'allow': ['S', 'CH', 'M', 'F', 'C', 'LD>K'],
        'S': throw_garbage,
        'current': 'rinse_cup',
        'next': 'throw_garbage'
    }
    stand_up = {
        'allow': ['CH', 'F', 'M', 'C', 'LD>K'],
        'LD>K': rinse_cup,
        'CH': rinse_cup,
        'current': 'stand_up',
        'next': 'rinse_cup'
    }
    drink_water = {
        'allow': [('C', 'LD'), 'F', 'M'],
        ('C', 'LD'): stand_up,
        'current': 'drink_water',
        'next': 'stand_up'
    }
    take_med = {
        'allow': [('M', 'LD'), 'F'],
        ('M', 'LD'): drink_water,
        'current': 'take_med',
        'next': 'drink_water'
    }
    eat_food = {
        'allow': [('F', 'LD'), 'C', 'CH'],
        ('F', 'LD'): take_med,
        'current': 'eat_food',
        'next': 'take_med'
    }
    sit_chair = {
        'allow': ['CH', 'M', 'C', 'F', 'CH'],
        'CH': eat_food,
        'current': 'sit_chair',
        'next': 'eat_food'
    }
    put_med = {
        'allow': ['K>LD', ('M', 'LD'), 'M', 'C', 'F'],
        'K>LD': sit_chair,
        ('M','LD'): sit_chair,
        'current': 'put_med',
        'next': 'sit_chair'
    }
    get_med = {
        'allow': [('M', 'K'), ('M', 'LD'), 'F', 'C', 'LD>K', 'K>LD'],
        ('M', 'K'): put_med,
        ('M', 'LD'): sit_chair,
        'current': 'get_med',
        'next': 'put_med'
    }
    put_food_cup = {
        'allow': ['K>LD', 'LD>K', 'F', 'C', 'S', ('F', 'LD'), ('C', 'LD')],
        'K>LD': get_med,
        ('F', 'LD'): get_med,
        ('C', 'LD'): get_med,
        'current': 'put_food_cup',
        'next': 'get_med'
    }
    fill_cup = {
        'allow': ['S', 'F', 'C'],
        'S': put_food_cup,
        'current': 'fill_cup',
        'next': 'put_food_cup'
    }
    get_cup = {
        'allow': [('C', 'K'), 'F'],
        ('C', 'K'): fill_cup,
        'current': 'get_cup',
        'next': 'fill_cup'
    }
    get_food = {
        'allow': [('F', 'K'), 'L>LD', 'LD>L', 'L>K', 'LD>K', 'K>LD'],
        ('F', 'K'): get_cup,
        'current': 'get_food',
        'next': 'get_cup'
    }
    task_end = throw_garbage
    task_start = get_food

    subtask = {
        'get_food': 0,
        'get_cup': 1,
        'fill_cup': 2,
        'put_food_cup': 3,
        'get_med': 4,
        'put_med': 5,
        'sit_chair': 6,
        'eat_food': 7,
        'take_med': 8,
        'drink_water': 9,
        'stand_up': 10,
        'rinse_cup': 11,
        'throw_garbage': 12,
        'Done': 13
    }
    subtask_info = {
        #   (description            , query object, code , current dag  , next dag if error)
        0:  ('Retrieve food'        , 'food'      , 'F'  , get_food     , fill_cup),
        1:  ('Retrieve cup'         , 'glass'     , 'C'  , get_cup      , fill_cup),
        2:  ('Fill cup'             , 'sink'      , 'S'  , fill_cup     , put_food_cup),
        3:  ('Put food/cup on table', None        , 'K>L', put_food_cup , put_med),
        4:  ('Retrieve medication'  , 'pillbottle', 'M'  , get_med      , eat_food),
        5:  ('Put med on table'     , None        , 'K>L', put_med      , eat_food),
        6:  ('Sit chair'            , None        , 'CH' , sit_chair    , take_med),
        7:  ('Eat food'             , None        , 'F'  , eat_food     , drink_water),
        8:  ('Take medication'      , 'pills'     , 'PL'  , take_med     , stand_up),
        9:  ('Drink water'          , None        , 'C'  , drink_water  , rinse_cup),
        10: ('Stand up'             , None        , 'CH' , stand_up     , throw_garbage),
        11: ('Rinse cup'            , 'sink'      , 'C'  , rinse_cup    , None),
        12: ('Throw garbage'        , None        , 'G'  , throw_garbage, None),
        13: ('Completed'            , None        , None , None         , None)
    }
    num_tasks = 13


if __name__ == '__main__':
    w = WaterPlantsDag()
    print(w.fill_can['current'])
    print(w.fill_can['S']['P2']['P3']['S']['Done'])

    wd = WalkDogDag()
    print(wd.get_leash['L']['next'])
    print(wd.get_leash['L']['K']['D']['Done'])
