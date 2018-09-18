"""
Example of how to use the convert_points function.
convert_point function takes in an input point from the robot (a tuple) and converts it using transformation constants
into an output point on the sensor map (also a tuple).  There are default values for the transform. constants calculated
from 15 reference points, however you may substitute your own.
"""

from convert_points import convert_point  # Importing the convert_points function from the convert_points file.

input_points = [  # Example input points in (x,y) tuple format from robot space.
    (-1.08, -0.909),
    (0.0, 0.0),
    (-0.738, 4.27),
    (3.2, 0.747),
    (3.28, 2.29),
    (3.38, 3.19),
    (3.41, 3.89),
    (5.68, 0.542),
    (5.7, 2.01),
    (6.51, -1.58),
    (6.56, 0.471),
    (6.65, 1.87),
    (7.81, 0.345),
    (8.0, 1.81),
    (8.04, 2.8),
]

for index, input_point in enumerate(input_points):  # For each point in the above list.
    output_point = convert_point(input_point)  # Using function to transform from robot space to sensor space.
    print("Transformed point #{index}: ({ip[0]:.3f},{ip[1]:.3f}) -> ({op[0]:.3f},{op[1]:.3f})"
          .format(index=index + 1, ip=input_point, op=output_point))  # Printing the outputs in readable format.
