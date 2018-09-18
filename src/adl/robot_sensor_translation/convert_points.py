#!/usr/bin/env python

import math
from typing import Tuple, List

a_default = 0.999198
b_default = -0.052252
c_default = 1.056307
d_default = 0.080343
e_default = 1.005433
f_default = 1.052456


def convert_point(point, a=a_default, b=b_default, c=c_default,
                  d=d_default, e=e_default, f=f_default):
    """
    Convert an (x,y) point from robot space to sensor map space.
    Conversion uses formulas:
        x' = ax + by + c
        y' = dx + ey + f
    where a, b, c, d, e, and f are constants determined from training points.  Default constants have been calculated
    from 15 pairs of training points.

    :param point: (x,y) coordinate from robot space to be converted
    :param a: Uses default if not provided
    :param b: Uses default if not provided
    :param c: Uses default if not provided
    :param d: Uses default if not provided
    :param e: Uses default if not provided
    :param f: Uses default if not provided
    :return:  The converted point (x',y') in sensor map space
    """

    calculated_xp = a * point[0] + b * point[1] + c
    calculated_yp = d * point[0] + e * point[1] + f

    return calculated_xp, calculated_yp

convert_point.__annotations__ = {
    'point': Tuple[float, float], 'a': float, 'b': float, 'c': float,
    'd': float, 'e': float, 'f': float, 'return': Tuple[float, float]}

def calculate_errors(points, a, b, c, d, e, f):
    x_avg_error = 0
    y_avg_error = 0
    avg_euclidean_error = 0

    for index, pair in enumerate(points):
        output_point = pair[1]
        x_calc, y_calc = convert_point(pair[0], a, b, c, d, e, f)
        x_error = abs(x_calc - output_point[0])
        y_error = abs(y_calc - output_point[1])
        x_avg_error += x_error
        y_avg_error += y_error
        avg_euclidean_error += math.sqrt(x_error ** 2 + y_error ** 2)

    x_avg_error = x_avg_error / len(points)
    y_avg_error = y_avg_error / len(points)
    avg_euclidean_error = avg_euclidean_error / len(points)

    return x_avg_error, y_avg_error, avg_euclidean_error

calculate_errors.__annotations__ = {
    'point': List[Tuple[Tuple[float, float], Tuple[float, float]]],
    'a': float, 'b': float, 'c': float, 'd': float, 'e': float, 'f': float,
    'return': Tuple[float, float, float]}
