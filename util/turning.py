from util.vec import Vec3
from math import sin, pi
import numpy as np

# v is the magnitude of the velocity in the car's forward direction
def curvature(v):
    if 0.0 <= v < 500.0:
        return 0.006900 - 5.84e-6 * v
    if 500.0 <= v < 1000.0:
        return 0.005610 - 3.26e-6 * v
    if 1000.0 <= v < 1500.0:
        return 0.004300 - 1.95e-6 * v
    if 1500.0 <= v < 1750.0:
        return 0.003025 - 1.1e-6 * v
    if 1750.0 <= v < 2500.0:
        return 0.001800 - 4e-7 * v
    if v >= 2500.0:
        return max(0.001800 - 4e-7 * v, 0.0)
    return 0.0

def inverse_curvature(k):
    if k > 0.006900:
        return 0.0
    if 0.006900 >= k > 0.00398:
        return (0.006900 - k)/(5.84e-6)
    if 0.00398 >= k > 0.00235:
        return (0.005610 - k)/3.26e-6
    if 0.00235 >= k > 0.001375:
        return (0.004300 - k)/1.95e-6
    if 0.001375 >= k > 0.0011:
        return (0.003025 - k)/1.1e-6
    if 0.0011 >= k > 0.00088:
        return (0.001800 - k)/4e-7
    return 2300

def desired_curvature(source: Vec3, target: Vec3, orientation: Vec3, epsilon=1e-5):
    angle_to_target = orientation.ang_to(target - source)
    dist = (target - source).length()
    angle = abs(pi/2 - angle_to_target)
    if sin(2*angle) < epsilon:
        return 2/dist
    radius = (dist*sin(angle))/sin(2*angle)
    return 1/radius

def desired_curvature2(source: Vec3, target: Vec3, orientation: Vec3, epsilon=1e-5,
                        car_length=118, car_width=84, length_offset=14, ball_radius=93):
    turn_dir = np.sign(np.cross(orientation.as_numpy(), (target - source).as_numpy())[2])
    car_size = max(car_length, car_width)/2
    new_source = np.array([[np.cos(turn_dir*pi/2), -np.sin(turn_dir*pi/2), 0],
                           [np.sin(turn_dir*pi/2), np.cos(turn_dir*pi/2), 0],
                           [0, 0, 1]])@orientation.as_numpy()*car_size + orientation.as_numpy()*length_offset
    new_target = target - (target - source).normalized()*ball_radius
    return desired_curvature(Vec3.from_numpy(new_source), new_target, orientation, epsilon)