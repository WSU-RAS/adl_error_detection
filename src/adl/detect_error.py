#!/usr/bin/env python

from collections import deque
from util import WaterPlantsDag, WalkDogDag, TakeMedicationDag
from util import Items


def check_sequence(graph, seq=[], task_step_num=0, num_tasks=-1, loc=[]):
    """
    Checks for error in a sequence based on directed acyclic graph, returning
    five values: what step in the task, is current task step completed,
    name of the current step in the task, is next task step completed, and
    name of the next step in the task.

    :param Dag graph: Directed acyclic graph of the start task step
    :param list seq: Sequence of triggered sensors
    :param int task_step_num: Start task step
    :param int num_tasks: Total number of steps in tasks (subtasks)
    :param list loc: Location for each triggered sensor
    :rtype: int, bool, str, bool, str
    """
    if seq == []:
        return task_step_num, False, graph['current'], False, "ERROR sequence empty"
    if num_tasks == -1:
        return task_step_num, False, graph['current'], False, "ERROR num_tasks not provided"

    if loc == []:
        return _check_sequence(graph, seq, task_step_num, num_tasks-1, current=graph['current'])
    return _check_sequence_wloc(graph, seq, task_step_num, num_tasks-1, current=graph['current'], loc=loc)

def _check_sequence_wloc(graph, seq=[], task_step_num=0, num_tasks=-1, current=None, loc=[]):
    """
    Check sequence using estimotes + ambient sensors (with location)
    """
    sequence = deque(seq)
    location = deque(loc)
    while len(sequence) > 0:
        estimote = sequence.popleft()
        ambient_sensor = location.popleft()

        # check if first estimote or (estimote, ambient) is allowed
        if estimote not in graph['allow'] and (estimote, ambient_sensor) not in graph['allow']:
            return task_step_num, False, graph['current'], False, graph['current']

        # check if task has been completed
        if task_step_num == num_tasks and \
          (estimote in graph['Done'] or (estimote, ambient_sensor) in graph['Done']):
            return task_step_num, True, graph['current'], True, graph['next']

        # estimote sensor including change-location (FIFO)
        result = graph.get(estimote)
        # estimote sensor including change-location plus location (FIFO)
        result_wloc = graph.get((estimote, ambient_sensor))

        # check if we have reach end of sequence and is current step completed
        if len(sequence) == 0:
            if type(result) is dict or type(result_wloc) is dict:
                return task_step_num, True, graph['current'], False, graph['next']
            if task_step_num > 0:
                task_step_num -= 1
            return task_step_num, True, current, False, graph['current']

        # at this point, we assume we have not reached end of sequence
        # go through the rest of the sequence and if any of the conditions are true,
        # we use the next step's graph as the starting point
        if type(result_wloc) is dict:
            current = graph['current']
            graph = result_wloc
            task_step_num += 1

        elif type(result) is dict:
            current = graph['current']
            graph = result
            task_step_num += 1

def _check_sequence(graph, seq=[], task_step_num=0, num_tasks=-1, current=None):
    """
    Check sequence using estimotes only
    """
    sequence = deque(seq)
    while len(sequence) > 0:
        estimote = sequence.popleft()

        # check if estimote is allowed
        if estimote not in graph['allow']:
            return task_step_num, False, graph['current'], False, graph['current']

        # check if task has been completed
        if task_step_num == num_tasks and estimote in graph['Done']:
            return task_step_num, True, graph['current'], True, graph['next']

        # estimote sensor (FIFO)
        result = graph.get(estimote)

        # check if we have reach end of sequence and is current step completed
        if len(sequence) == 0:
            if type(result) is dict:
                return task_step_num, True, graph['current'], False, graph['next']
            if task_step_num > 0:
                task_step_num -= 1
            return task_step_num, True, current, False, graph['current']

        # at this point, we assume we have not reached end of sequence
        # go through the rest of the sequence and if any of the conditions are true,
        # we use the next step's graph as the starting point
        if type(result) is dict:
            current = graph['current']
            graph = result
            task_step_num += 1

def check_sequence_wloc_gen(graph, task_step_num=0, num_tasks=-1, current=None):
    """
    Uses python generator to check for error in a sequence (estimotes + ambient sensors)
    using a directed acyclic graph, returning five values: what step in the task,
    is current task step completed, name of the current step in the task,
    is next task step completed, and name of the next step in the task.

    :param Dag graph: Directed acyclic graph of the start task step
    :param int task_step_num: Start task step
    :param int num_tasks: Total number of steps in tasks (subtasks)
    :param str current: current step in the task
    :rtype: int, bool, str, bool, str
    """
    num_tasks -= 1
    is_complete = False
    has_error = False
    error_result = None
    while True:
        estimote, ambient_sensor = yield

        if has_error:
            yield error_result

        # check if first estimote or (estimote, ambient) is allowed
        elif estimote not in graph['allow'] and (estimote, ambient_sensor) not in graph['allow']:
            has_error = True
            error_result = (task_step_num, False, graph['current'], False, graph['current'])
            yield error_result

        # check if task has been completed
        elif is_complete or (task_step_num == num_tasks and \
          (estimote in graph['Done'] or (estimote, ambient_sensor) in graph['Done'])):
            is_complete = True
            yield task_step_num, True, graph['current'], True, graph['next']

        else:
            # at this point, we assume we have not reached end of sequence
            # go through the rest of the sequence and if any of the conditions are true,

            # estimote sensor including change-location (FIFO)
            result = graph.get(estimote)
            # estimote sensor including change-location plus location (FIFO)
            result_wloc = graph.get((estimote, ambient_sensor))

            # is current step completed
            if type(result) is dict or type(result_wloc) is dict:
                yield task_step_num, True, graph['current'], False, graph['next']
                current = graph['current']
                # we use the next step's graph as the starting point
                graph = result_wloc if type(result_wloc) is dict else result
                task_step_num += 1
            else:
                # current step incomplete
                temp_task_step_num = task_step_num
                if task_step_num > 0:
                    temp_task_step_num -= 1
                # previous step
                yield temp_task_step_num, True, current, False, graph['current']

def check_sequence_gen(graph, task_step_num=0, num_tasks=-1, current=None):
    """
    Uses python generator to check for error in a sequence (estimotes only)
    using a directed acyclic graph, returning five values: what step in the task,
    is current task step completed, name of the current step in the task,
    is next task step completed, and name of the next step in the task.

    :param Dag graph: Directed acyclic graph of the start task step
    :param int task_step_num: Start task step
    :param int num_tasks: Total number of steps in tasks (subtasks)
    :param str current: current step in the task
    :rtype: int, bool, str, bool, str
    """
    num_tasks -= 1
    is_complete = False
    has_error = False
    error_result = None
    while True:
        estimote = yield

        if has_error:
            yield error_result

        # check if estimote is allowed
        elif estimote not in graph['allow']:
            has_error = True
            error_result = (task_step_num, False, graph['current'], False, graph['current'])
            yield error_result

        # check if task has been completed
        elif is_complete or (task_step_num == num_tasks and estimote in graph['Done']):
            is_complete = True
            yield task_step_num, True, graph['current'], True, graph['next']

        else:
            # at this point, we assume we have not reached end of sequence
            # go through the rest of the sequence and if any of the conditions are true,

            # estimote sensor (FIFO)
            result = graph.get(estimote)

            # is current step completed
            if type(result) is dict:
                yield task_step_num, True, graph['current'], False, graph['next']
                current = graph['current']
                # we use the next step's graph as the starting point
                graph = result
                task_step_num += 1
            else:
                # current step incomplete
                temp_task_step_num = task_step_num
                if task_step_num > 0:
                    temp_task_step_num -= 1
                yield temp_task_step_num, True, current, False, graph['current']


if __name__ == '__main__':
    sequence = ['U', 'L', 'K', 'D', 'DR']
    check = check_sequence_gen(
        WalkDogDag.task_start,
        num_tasks=WalkDogDag.num_tasks,
        current=WalkDogDag.task_start['current'])
    for sensor in sequence:
        try:
            next(check)
            print(check.send(sensor))
        except StopIteration:
            print("Error in sequence")

    next(check)
    print(check.send('DR'))

    check.close()

    sequence = ['W', 'S', 'P3', 'P2', 'P2']
    check = check_sequence_gen(
        WaterPlantsDag.task_start,
        num_tasks=WaterPlantsDag.num_tasks,
        current=WaterPlantsDag.task_start['current'])
    for sensor in sequence:
        try:
            next(check)
            print(check.send(sensor))
        except StopIteration:
            print("Error in sequence")

    check.close()

    print(check_sequence(
        WaterPlantsDag.water_plantcoffee,
        seq=['W','W','W'],
        task_step_num=2,
        num_tasks=WaterPlantsDag.num_tasks))

    print(check_sequence(
        WaterPlantsDag.task_start,
        seq=['W', 'S', 'P2', 'P3', 'S'],
        num_tasks=WaterPlantsDag.num_tasks))

    print(check_sequence(
        WaterPlantsDag.task_start,
        seq=['W', 'S', 'P2', 'P3', 'S', 'W'],
        num_tasks=WaterPlantsDag.num_tasks))

    print(check_sequence(
        WalkDogDag.task_start,
        seq=['U', 'U', 'U'],
        num_tasks=WalkDogDag.num_tasks))

    print(check_sequence(
        WalkDogDag.task_start,
        seq=['U', 'L', 'K', 'D', 'DR'],
        num_tasks=WalkDogDag.num_tasks))

    print(check_sequence(
        TakeMedicationDag.task_start,
        seq=['F', 'F', 'C', 'C', 'F', 'F', 'C', 'F', 'S', 'S',
             'F', 'C', 'C', 'C', 'F', 'F', 'C', 'C', 'M', 'CH',
             'CH', 'C', 'F', 'F', 'F', 'M', 'M', 'C', 'C', 'C',
             'CH', 'C', 'CH', 'M', 'F', 'C', 'C', 'M', 'F', 'M',
             'F', 'M', 'C', 'F', 'F', 'S', 'C', 'C', 'F', 'M',
             'M', 'F', 'C', 'M', 'C', 'C', 'G', 'M', 'G', 'M'],
        num_tasks=TakeMedicationDag.num_tasks))
