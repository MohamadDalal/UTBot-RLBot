import numpy as np
import matplotlib.pyplot as plt

def clamp(x, min_val, max_val):
    return max(min(x, max_val), min_val)

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
    if 1750.0 <= v <= 2500.0:
        return 0.001800 - 4e-7 * v

    return 0.0

def angular_velocity(s):
    s = clamp(s, 0, 2500)
    return s * curvature(s)

x = np.linspace(0, 2500, 100)
plt.plot(x, [angular_velocity(s) for s in x])
plt.xlabel('Speed')
plt.ylabel('Angular velocity')
plt.title('Angular velocity as a function of speed')
plt.show()