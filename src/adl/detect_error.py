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

# def _check_sequence_wloc(graph, seq=[], task_step_num=0, num_tasks=-1, current=None, loc=[]):
#     """
#     Use recursion to check sequence using estimotes + ambient sensors (with location)
#     """
#     # check if first sensor is allowed
#     if seq[0] not in graph['allow'] and (seq[0], loc[0]) not in graph['allow']:
#         return task_step_num, False, graph['current'], False, graph['current']
#
#     # check if task has been completed
#     if task_step_num == num_tasks and (seq[0] in graph['Done'] or (seq[0], loc[0]) in graph['Done']):
#         return task_step_num, True, graph['current'], True, graph['next']
#
#     # estimote sensor including change-location (FIFO)
#     result = graph.get(seq[0])
#     # estimote sensor including change-location plus location (FIFO)
#     result_wloc = graph.get((seq[0], loc[0]))
#
#     # check if we have reach end of sequence and is current step completed
#     if len(seq) == 1:
#         if type(result) is dict or type(result_wloc) is dict:
#             return task_step_num, True, graph['current'], False, graph['next']
#         if task_step_num > 0:
#             task_step_num -= 1
#         return task_step_num, True, current, False, graph['current']
#
#     # at this point, we assume we have not reached end of sequence
#     # go through the rest of the sequence and if any of the conditions are true,
#     # we use the next step's graph as the starting point
#     if type(result_wloc) is dict:
#         return _check_sequence_wloc(result_wloc, seq[1:], task_step_num+1, num_tasks, graph['current'], loc[1:])
#     elif type(result) is dict:
#         return _check_sequence_wloc(result, seq[1:], task_step_num+1, num_tasks, graph['current'], loc[1:])
#
#     # catch-all, when first sensor in sequence is allowed but does not complete
#     # the step, we continue to check the next sensor in the sequence
#     return _check_sequence_wloc(graph, seq[1:], task_step_num, num_tasks, current, loc[1:])

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
            # return _check_sequence_wloc(result_wloc, seq[1:], task_step_num+1, num_tasks, graph['current'], loc[1:])
        elif type(result) is dict:
            current = graph['current']
            graph = result
            task_step_num += 1
            # return _check_sequence_wloc(result, seq[1:], task_step_num+1, num_tasks, graph['current'], loc[1:])

        # catch-all, when first sensor in sequence is allowed but does not complete
        # the step, we continue to check the next sensor in the sequence
        # return _check_sequence_wloc(graph, seq[1:], task_step_num, num_tasks, current, loc[1:])


# def _check_sequence(graph, seq=[], task_step_num=0, num_tasks=-1, current=None):
#     """
#     Use recursion to check sequence using estimotes only
#     """
#     # check if first sensor is allowed
#     if seq[0] not in graph['allow']:
#         return task_step_num, False, graph['current'], False, graph['current']
#
#     # check if task has been completed
#     if task_step_num == num_tasks and seq[0] in graph['Done']:
#         return task_step_num, True, graph['current'], True, graph['next']
#
#     # estimote sensor (FIFO)
#     result = graph.get(seq[0])
#
#     # check if we have reach end of sequence and is current step completed
#     if len(seq) == 1:
#         if type(result) is dict:
#             return task_step_num, True, graph['current'], False, graph['next']
#         if task_step_num > 0:
#             task_step_num -= 1
#         return task_step_num, True, current, False, graph['current']
#
#     # at this point, we assume we have not reached end of sequence
#     # go through the rest of the sequence and if any of the conditions are true,
#     # we use the next step's graph as the starting point
#     if type(result) is dict:
#         return _check_sequence(result, seq[1:], task_step_num+1, num_tasks, graph['current'])
#
#     # catch-all, when first sensor in sequence is allowed but does not complete
#     # the step, we continue to check the next sensor in the sequence
#     return _check_sequence(graph, seq[1:], task_step_num, num_tasks, current)

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
            #return _check_sequence(result, seq[1:], task_step_num+1, num_tasks, graph['current'])

        # catch-all, when first estimote in sequence is allowed but does not complete
        # the step, we continue to check the next estimote in the sequence
        # return _check_sequence(graph, seq[1:], task_step_num, num_tasks, current)


if __name__ == '__main__':
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
