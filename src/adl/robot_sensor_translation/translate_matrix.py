#!/usr/bin/env python

from typing import List, Tuple
import itertools

import numpy as np


def calculate_transform_constants_from_points(points):
    p = np.array([
        [points[0][0][0], points[0][0][1], 1],
        [points[1][0][0], points[1][0][1], 1],
        [points[2][0][0], points[2][0][1], 1]
    ])
    q = np.array([
        [points[0][1][0]],
        [points[1][1][0]],
        [points[2][1][0]]
    ])
    r = np.array([
        [points[0][1][1]],
        [points[1][1][1]],
        [points[2][1][1]]
    ])
    s = np.linalg.solve(p, q)
    t = np.linalg.solve(p, r)

    a = float(s[0])
    b = float(s[1])
    c = float(s[2])
    d = float(t[0])
    e = float(t[1])
    f = float(t[2])

    return a, b, c, d, e, f

calculate_transform_constants_from_points.__annotations__ = {
    'points': List[Tuple[Tuple[float, float], Tuple[float, float]]],
    'return': Tuple[float, float, float, float, float, float]
}

def calculate_average_transform_constants(points):
    combinations = [list(combo) for combo in itertools.combinations(points, 3)]
    avg_a = 0
    avg_b = 0
    avg_c = 0
    avg_d = 0
    avg_e = 0
    avg_f = 0

    for combo in combinations:
        a, b, c, d, e, f = calculate_transform_constants_from_points(combo)
        avg_a += a
        avg_b += b
        avg_c += c
        avg_d += d
        avg_e += e
        avg_f += f

    avg_a = avg_a / len(combinations)
    avg_b = avg_b / len(combinations)
    avg_c = avg_c / len(combinations)
    avg_d = avg_d / len(combinations)
    avg_e = avg_e / len(combinations)
    avg_f = avg_f / len(combinations)

    return avg_a, avg_b, avg_c, avg_d, avg_e, avg_f

calculate_average_transform_constants.__annotations__ = {
    'points': List[Tuple[Tuple[float, float], Tuple[float, float]]],
    'return': Tuple[float, float, float, float, float, float]
}
