import numpy as np

import matplotlib.pyplot as plt

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

    return 0.0

def calc_turning_time(speed, orientation, car_location, target_location, epsilon=1e-4, deltaT=1/120):
    """
    Calculate the time it takes to turn the car to a certain orientation
    """
    s = speed
    a = orientation
    b = target_location
    c = car_location
    steps_taken = 0

    # Calculate the angle between the car orientation and the target orientation
    angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(target_location - car_location)))
    while np.abs(angle) > epsilon:
        steps_taken += 1
        speed -= 3500*deltaT 
        current_curvature = curvature(speed)

        # Calculate the angle between the car orientation and the target orientation
        angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(target_location - car_location)))

    # Calculate the time it takes to turn the car to the target orientation
    turning_time = angle / speed

    return turning_time


# Generate x and y values
x = np.linspace(-10, 10, 100)
y = np.linspace(-10, 10, 100)
X, Y = np.meshgrid(x, y)

velX = 0
velY = 1

# Moving directly backwards is a deceleration of 3500 uu/s. So the distance travelled is:
# v = u + at
# D = ut + 0.5at^2
# t = (-u + sqrt(u^2 - 2aD))/a

# Calculate z values
Z = (X + Y + 5)**0.5

# Create contour plot
plt.contour(X, Y, Z)

# Add labels and title
plt.xlabel('x')
plt.ylabel('y')
plt.title('Contour Map of z = x^2 + y^2')

# Show the plot
plt.show()