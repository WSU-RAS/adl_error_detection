from convert_points import convert_point, calculate_errors
from translate_matrix import calculate_average_transform_constants

input_points = [
    ((-1.08, -0.909), (0.0, 0.0)),
    ((0.0, 0.0), (0.932, 1.0)),
    ((-0.738, 4.27), (0.0, 5.22)),
    ((3.2, 0.747), (4.25, 2.04)),
    ((3.28, 2.29), (4.25, 3.62)),
    ((3.38, 3.19), (4.25, 4.52)),
    ((3.41, 3.89), (4.25, 5.22)),
    ((5.68, 0.542), (6.7222, 2.05)),
    ((5.7, 2.01), (6.6663, 3.54)),
    ((6.51, -1.58), (7.8022, 0.02)),
    ((6.56, 0.471), (7.6222, 2.06)),
    ((6.65, 1.87), (7.6222, 3.48)),
    ((7.81, 0.345), (8.9622, 2.06)),
    ((8.0, 1.81), (8.9522, 3.48)),
    ((8.04, 2.8), (8.9522, 4.51))
]

a, b, c, d, e, f = calculate_average_transform_constants(input_points)

print("a = {:.6f}".format(a))
print("b = {:.6f}".format(b))
print("c = {:.6f}".format(c))
print("d = {:.6f}".format(d))
print("e = {:.6f}".format(e))
print("f = {:.6f}".format(f))

for index, pair in enumerate(input_points):
    input_point = pair[0]
    print("Transformed point #{index}: ({ip[0]:.3f},{ip[1]:.3f}) -> ({op[0]:.3f},{op[1]:.3f})"
          .format(index=index + 1, ip=input_point, op=convert_point(input_point, a, b, c, d, e, f)))

x_error, y_error, euclidean_error = calculate_errors(input_points, a, b, c, d, e, f)
print("Average x error is: {:.4f}".format(x_error))
print("Average y error is: {:.4f}".format(y_error))
print("Average Euclidean error is: {:.4f}".format(euclidean_error))
