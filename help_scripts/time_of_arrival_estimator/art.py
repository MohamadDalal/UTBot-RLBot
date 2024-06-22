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
    if 1750.0 <= v < 2500.0:
        return 0.001800 - 4e-7 * v

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

def acceleration(v, boost=False):
    retVal = 0
    if 0.0 <= v < 1400.0:
        retVal = 1600 - (1440/1400)*v
    elif 1400.0 <= v < 1410.0:
        retVal = 160 - 16*(v-1400)
    elif 1410.0 <= v <= 2300.0:
        retVal = 0
    else:
        return 0
    if boost:
        retVal += 991 + 1/3
    return retVal

def calc_straight_time(speed, car_location, target_location, boost=True):
    # Speed change is v = v_0 + at
    # Distance change is d = v_0t + 0.5at^2
    # Time to reach target is t = (-v_0 + sqrt(v_0^2 + 2ad))/a
    d = np.linalg.norm(target_location - car_location)
    v = speed
    t = (-v + np.sqrt(v**2 + 2*acceleration(v, boost)*d))/acceleration(v, boost) 
    return t

def desired_curvature(source, target, angle_to_target):
    dist = np.linalg.norm(target - source)
    angle = np.abs(np.pi/2 - angle_to_target)
    radius = (dist*np.sin(angle))/np.sin(2*angle)
    return 1/radius


def calc_turning_time(speed, orientation, car_location, target_location, desiredSpeed=850, brake=True, epsilon=0.05, deltaT=1/120, max_iter=1000, straight_boost=True):
    """
    Calculate the time it takes to turn the car to a certain orientation
    """

    

    s = speed
    a = orientation/np.linalg.norm(orientation)
    b = target_location
    c = car_location
    brake_speed = 3500 if brake else 525
    # TODO: Decide if we are to turn left or right
    turn_dir = np.sign(np.cross(a, b - c)[2]) # -1 if left, 1 if right
    # Calculate the angle between the car orientation and the target orientation
    angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(b - c)))
    vel_ang = speed * curvature(s)
    if desiredSpeed is None:
        desiredSpeed = inverse_curvature(desired_curvature(c, b, angle))
    if desiredSpeed <= 0:
        return np.inf, np.inf
    elif desiredSpeed > s:
        time_to_desired_speed = (desiredSpeed - s) / acceleration(s, boost=straight_boost)
    else:
        time_to_desired_speed = (s - desiredSpeed) / brake_speed
    time_taken = 0
    #print("Start angle: ", angle)
    for i in range(int(time_to_desired_speed//deltaT)):
        if angle < epsilon:
            break
        else:
            s -= brake_speed*deltaT
            s = clamp(s, 0, 2500)
            vel_ang = speed * curvature(s)
            a = np.array([[np.cos(turn_dir*vel_ang*deltaT), -np.sin(turn_dir*vel_ang*deltaT), 0],
                        [np.sin(turn_dir*vel_ang*deltaT), np.cos(turn_dir*vel_ang*deltaT), 0],
                        [0, 0, 1]])@a
            vel = s*a
            c = c+vel*deltaT
            # Calculate the angle between the car orientation and the target orientation
            angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(b - c)))
            time_taken += deltaT
    #print("Middle angle: ", angle)
    iter_count = 0
    #print(s)
    while np.abs(angle) > epsilon and iter_count < max_iter:
        time_to_turn = angle / vel_ang
        c = c+np.sqrt(2*(1/curvature(s))**2*(1-np.cos(turn_dir*angle)))*np.array([[np.cos(turn_dir*angle/2), -np.sin(turn_dir*angle/2), 0],
                                                                                  [np.sin(turn_dir*angle/2), np.cos(turn_dir*angle/2), 0],
                                                                                  [0, 0, 1]])@a
        a = np.array([[np.cos(turn_dir*angle), -np.sin(turn_dir*angle), 0],
                      [np.sin(turn_dir*angle), np.cos(turn_dir*angle), 0],
                      [0, 0, 1]])@a
        vel = s*a
        
        # Calculate the angle between the car orientation and the target orientation
        angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(b - c)))
        time_taken += time_to_turn
        iter_count += 1
    if iter_count >= max_iter:
        return np.inf, np.inf
    #print("End angle: ", angle)
    return time_taken, calc_straight_time(s, c, b, boost=straight_boost)


# Generate x and y values
x = np.linspace(-1000, 1000, 100)
y = np.linspace(-1000, 1000, 100)
X, Y = np.meshgrid(x, y)

velX = 0
velY = 1

# Moving directly backwards is a deceleration of 3500 uu/s. So the distance travelled is:
# v = u + at
# D = ut + 0.5at^2
# t = (-u + sqrt(u^2 - 2aD))/a

# Calculate z values
#Z = (X + Y + 5)**0.5
funcZ = lambda x, y: calc_turning_time(1440, np.array([velX, velY, 0]), np.array([0, 0, 0]), np.array([x, y, 0]),
                                       brake = True, desiredSpeed=None, max_iter=100)
#print([[funcZ(x, y) for x in x] for y in y])
Times = np.array([[funcZ(x, y) for x in x] for y in y])
Z = np.array([[np.sum(Times[i][j]) for j in range(len(x))] for i in range(len(y))])
Z_turn = np.array([[Times[i][j][0] for j in range(len(x))] for i in range(len(y))])
Z_straight = np.array([[Times[i][j][1] for j in range(len(x))] for i in range(len(y))])
print(Z)

# Create contour plot
#plt.contour(X, Y, Z)
plt.imshow(Z, extent=[-1000, 1000, -1000, 1000], origin='lower',
           cmap='magma')
plt.colorbar()

# Add labels and title
plt.xlabel('x')
plt.ylabel('y')
plt.title('Time taken to reach the ball at a certain position')
#plt.savefig("help_scripts\\time_of_arrival_estimator\\first_try_brake.png", bbox_inches='tight', dpi=300)

# Show the plot
plt.show()