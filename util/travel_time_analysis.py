import numpy as np
from util.vec import Vec3
from util.turning import curvature

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
        retVal += 991 + 1/3 if v <= 2300 else 0
    return retVal

def calc_straight_time(speed, car_location, target_location, boost=True):
    # Speed change is v = v_0 + at
    # Distance change is d = v_0t + 0.5at^2
    # Time to reach target is t = (-v_0 + sqrt(v_0^2 + 2ad))/a
    d = np.linalg.norm(target_location - car_location)
    v = speed
    t = (-v + np.sqrt(v**2 + 2*acceleration(v, boost)*d))/acceleration(v, boost) 
    return t

# After testing it was found out that the difference this introduces is miniscule for the field size we are working with.
#def calc_straight_time(speed, car_location, target_location, boost=True, boost_amount=100, delta_t=1/120):
#    # Speed change is v = v_0 + at
#    # Distance change is d = v_0t + 0.5at^2
#    # Time to reach target is t = (-v_0 + sqrt(v_0^2 + 2ad))/a
#    v = speed
#    d = np.linalg.norm(target_location - car_location) 
#    t = 0
#    #t2 = (-v + np.sqrt(v**2 + 2*acceleration(v, boost)*d))/acceleration(v, boost) 
#    boost_amount = boost_amount * 3/100
#    while d>0:
#        d -= v*delta_t
#        v += acceleration(speed, boost and boost_amount > 0)*delta_t
#        t += delta_t
#        boost_amount -= delta_t
#    return t

def simple_check_collision(car_orientation, car_location, target_location, car_length=118, car_width=84, length_offset=14, ball_radius=93):
    car_location = car_location + car_orientation*length_offset
    car_to_target = target_location - car_location
    return np.linalg.norm(car_to_target) < max(car_length, car_width)/2 + ball_radius

def simplest_calc_turning_time(speed, orientation: Vec3, car_location: Vec3, target_location: Vec3,
                               epsilon=0.05, max_iter=10, straight_boost=True,
                               car_length=118, car_width=84, length_offset=14, ball_radius=93):
    """
    Calculate the time it takes to turn the car to a certain orientation
    """

    # TODO: Account for ball radius and car width.

    s = speed
    a = orientation.as_numpy()/np.linalg.norm(orientation.as_numpy())
    b = target_location.as_numpy()
    c = car_location.as_numpy()
    time_taken = 0
    turn_dir = np.sign(np.cross(a, b - c)[2]) # -1 if left, 1 if right
    # Calculate the angle between the car orientation and the target orientation
    angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(b - c)))
    vel_ang = speed * curvature(s)
    iter_count = 0
    while (np.abs(angle) > epsilon and iter_count < max_iter and time_taken <= 6
           and not simple_check_collision(a, c, b, car_length=car_length, car_width=car_width, length_offset=length_offset, ball_radius=ball_radius)):
        time_to_turn = angle / vel_ang
        c = c+np.sqrt(2*(1/curvature(s))**2*(1-np.cos(turn_dir*angle)))*np.array([[np.cos(turn_dir*angle/2), -np.sin(turn_dir*angle/2), 0],
                                                                                  [np.sin(turn_dir*angle/2), np.cos(turn_dir*angle/2), 0],
                                                                                  [0, 0, 1]])@a
        a = np.array([[np.cos(turn_dir*angle), -np.sin(turn_dir*angle), 0],
                      [np.sin(turn_dir*angle), np.cos(turn_dir*angle), 0],
                      [0, 0, 1]])@a
        
        # Calculate the angle between the car orientation and the target orientation
        angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(b - c)))
        time_taken += time_to_turn
        iter_count += 1
    if iter_count >= max_iter:
        return None
    return time_taken, calc_straight_time(s, c, b, boost=straight_boost)

def calc_turning_time(speed, orientation: Vec3, car_location: Vec3, target_location: Vec3,
                      desiredSpeed=850, brake=True, epsilon=0.05, deltaT=1/120, max_iter=1000, straight_boost=True):
    """
    Calculate the time it takes to turn the car to a certain orientation
    """

    s = speed
    a = orientation.as_numpy()/np.linalg.norm(orientation.as_numpy())
    b = target_location.as_numpy()
    c = car_location.as_numpy()
    brake_speed = 3500 if brake else 525
    time_to_desired_speed = (s - desiredSpeed) / brake_speed
    time_taken = 0
    # TODO: Decide if we are to turn left or right
    turn_dir = np.sign(np.cross(a, b - c)[2]) # -1 if left, 1 if right
    # Calculate the angle between the car orientation and the target orientation
    angle = np.arccos(np.dot(a, b - c) / (np.linalg.norm(b - c)))
    vel_ang = speed * curvature(s)
    #print("Start angle: ", angle)
    for i in range(int(time_to_desired_speed//deltaT)):
        if angle < epsilon:
            break
        else:
            s -= brake_speed*deltaT
            #vel_ang = speed * curvature(s)
            vel_ang = min(speed * curvature(s), 9.11*time_taken)
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
    #max_vel_ang = speed * curvature(s)
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