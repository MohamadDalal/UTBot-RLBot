from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction, Slice

from util.drive import steer_toward_target
from util.vec import Vec3
from util.turning import desired_curvature, desired_curvature2, curvature
from util.travel_time_analysis import simplest_calc_turning_time

from math import pi, cos, sqrt
from time import perf_counter


LONG_OFFSET = 200

def sign(num) -> int:
    if num >= 0 :    return 1
    elif num < 0:   return -1
    else:           return 0

def clamp2D(direction:Vec3, start:Vec3, end:Vec3):
    is_right = direction.dot(end.cross(Vec3(0,0,-1))) < 0
    is_left = direction.dot(start.cross(Vec3(0,0,-1))) > 0

    if ((is_right and is_left) if (end.dot(start.cross(Vec3(0,0,-1))) > 0) else (is_right or is_left)):
        return direction
    elif start.dot(direction) < end.dot(direction):
        return end
    else:
        return start

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

def turn_radius2(v):
    if v == 0:
        return 0
    return 1.0 / curvature(v)

def chaseGoal(self: BaseAgent, packet: GameTickPacket, field_info: FieldInfoPacket, controls: SimpleControllerState, ball_location: Vec3 = None):
    # TODO: If the balle is behind the car after the turn, then we should drive a bit more before making the turn
    # TODO: If curvature too large then drift
    car_location = Vec3(packet.game_cars[self.index].physics.location)
    if ball_location is None:
        ball_location = Vec3(packet.game_ball.physics.location)
    if (self.team + 1) % 2 == 0:
        opponent_goal = field_info.goals[(self.team + 1) % 2]
        left_target_location = Vec3(opponent_goal.location) - Vec3(0.5*opponent_goal.width,0,0) + Vec3(200,0,0)
        right_target_location:Vec3 = left_target_location + Vec3(opponent_goal.width,0,0) - Vec3(400,0,0)
    else:
        opponent_goal = field_info.goals[(self.team + 1) % 2]
        left_target_location = Vec3(opponent_goal.location) + Vec3(0.5*opponent_goal.width,0,0) - Vec3(200,0,0)
        right_target_location:Vec3 = left_target_location - Vec3(opponent_goal.width,0,0) + Vec3(400,0,0)

    car_to_ball = ball_location - car_location
    car_to_ball_direction = car_to_ball.normalized()
    ball_to_left_target_direction = (left_target_location - ball_location).normalized()
    ball_to_right_target_direction = (right_target_location - ball_location).normalized()

    direction_of_approach = clamp2D(car_to_ball_direction, ball_to_left_target_direction, ball_to_right_target_direction)
    #self.renderer.draw_line_3d(ball_location, left_target_location, self.renderer.orange() if self.index else self.renderer.blue())
    #self.renderer.draw_line_3d(ball_location, right_target_location, self.renderer.orange() if self.index else self.renderer.blue())
    if car_to_ball.length() > LONG_OFFSET:
        offset_ball_location = ball_location - (direction_of_approach * LONG_OFFSET)
    else:
        offset_ball_location = ball_location - (direction_of_approach * 92.75)
    side_of_approach_direction = sign(direction_of_approach.cross(Vec3(0, 0, 1)).dot(car_to_ball))
    #print(side_of_approach_direction)
    car_to_ball_perpendicular = car_to_ball.cross(Vec3(0, 0, side_of_approach_direction)).normalized()
    adjustment = abs((car_to_ball.flat()).ang_to(direction_of_approach.flat())) * 2560
    final_target = offset_ball_location + (car_to_ball_perpendicular * adjustment)
    #self.renderer.draw_line_3d(car_location, final_target, self.renderer.orange() if self.index else self.renderer.blue())
    #self.renderer.draw_line_3d(ball_location, ball_location+direction_of_approach*180, self.renderer.orange() if self.index else self.renderer.blue())
    #self.renderer.draw_line_3d(offset_ball_location, final_target, self.renderer.orange() if self.index else self.renderer.blue())

    min_turn_radius = turn_radius2(Vec3(packet.game_cars[self.index].physics.velocity).length())
    wanted_turn_radius = Vec3.length(offset_ball_location-car_location)
    #self.renderer.draw_string_3d(car_location+Vec3(0,0,80), 1, 1, f"Min turn radius: {min_turn_radius}", self.renderer.white())
    #self.renderer.draw_string_3d(car_location+Vec3(0,0,70), 1, 1, f"Wanted turn radius: {wanted_turn_radius}", self.renderer.white())
    
    radius_plus, radius_minus = turn_radius(Vec3(packet.game_cars[self.index].physics.velocity).flat(), direction_of_approach.flat(), car_location.flat(), offset_ball_location.flat())
    #needed_radius = turn_radius(Vec3(packet.game_cars[self.index].physics.velocity).flat(), direction_of_approach, car_location, offset_ball_location)
    needed_radius = radius_plus if abs(radius_plus) < abs(radius_minus) else radius_minus
    self.renderer.draw_string_3d(car_location+Vec3(0,0,90), 1, 1, f"Radius min: {min_turn_radius}", self.renderer.white())
    self.renderer.draw_string_3d(car_location+Vec3(0,0,80), 1, 1, f"Radius-: {radius_minus}", self.renderer.white())
    self.renderer.draw_string_3d(car_location+Vec3(0,0,70), 1, 1, f"Radius+: {radius_plus}", self.renderer.white())
    #self.renderer.draw_string_3d(car_location+Vec3(0,0,70), 1, 1, f"Radius: {needed_radius}", self.renderer.white())
    p = car_location.flat() + needed_radius*Vec3(packet.game_cars[self.index].physics.velocity).flat().cross(Vec3(0,0,-1)).normalized()
    turn_target = offset_ball_location.flat() - (direction_of_approach.flat().dot(offset_ball_location.flat() - p))*direction_of_approach.flat()
    self.renderer.draw_line_3d(car_location, p, self.renderer.green())
    self.renderer.draw_line_3d(turn_target, turn_target + needed_radius*direction_of_approach.flat().cross(Vec3(0,0,-1)).normalized(), self.renderer.green())
    self.renderer.draw_line_3d(car_location, car_location + 200*Vec3(packet.game_cars[self.index].physics.velocity).flat().normalized(), self.renderer.red())
    self.renderer.draw_line_3d(offset_ball_location, offset_ball_location + 200*direction_of_approach.flat().normalized(), self.renderer.red())
    #self.renderer.draw_line_3d(car_location, car_location + radius_plus*Vec3(packet.game_cars[self.index].physics.velocity).flat().cross(Vec3(0,0,-1)).normalized(), self.renderer.red())

    controls.steer =  steer_toward_target(packet.game_cars[self.index], final_target)
    #self.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"steer: {controls.steer}", self.renderer.white())


def turn_radius(current_orientation: Vec3, desired_orientation: Vec3, current_location: Vec3, desired_location: Vec3, epsilon=1e-6):
    # Calculate the radius of the circle we need to turn in
        # Needs to consider when we cannot possible turn for the ball with the desired oriantation
        radius_direction = current_orientation.cross(Vec3(0,0,-1)).normalized()
        d = (desired_orientation.dot(radius_direction))*desired_orientation - radius_direction
        if abs(d.dot(d)-1) < epsilon:
            # Return half the distance from current_location to desired line
            #print("Parallel")
            #dist = (current_location - desired_location).length()**2 - current_location.dot(desired_orientation)**2
            dist = 0.5*(desired_location - current_location - desired_orientation.dot(desired_location - current_location)*desired_orientation).length()
            return dist, -dist
        c = desired_location - current_location + (desired_orientation.dot(current_location) - desired_orientation.dot(desired_location))*desired_orientation
        det = c.dot(d)**2-(d.dot(d)-1)*c.dot(c)
        #print(c, d)
        if det < 0:
            print(det)
            return 0, 0
        radius_plus = (-c.dot(d)+sqrt(det))/(d.dot(d)-1)
        radius_minus = (-c.dot(d)-sqrt(det))/(d.dot(d)-1)
        #return radius_plus if abs(radius_plus) < abs(radius_minus) else radius_minus
        return radius_plus, radius_minus

def max_speed_given_radius(v):
    # Calculate the max speed we can go in given the radius we need to traverse
    pass

def chase_ball(bot: BaseAgent, packet: GameTickPacket, field_info: FieldInfoPacket, controls: SimpleControllerState, ball_prediction: BallPrediction,
               max_iter=10, k_epsilon=1e-4):
    # Plan:
    # 1. Get steering from chase target
    # 2. See if we can turn to target
    # 3. If not then adjust steering (coast or drift)
    # 4. Use a time estimator to see if we are chasing the correct ball
    # 5. If not then recalculate steering
    start_time = perf_counter()

    ball_location = Vec3(packet.game_ball.physics.location)
    #ball_velocity = Vec3(packet.game_ball.physics.velocity)
    car_location = Vec3(packet.game_cars[bot.index].physics.location)
    car_velocity = Vec3(packet.game_cars[bot.index].physics.velocity)
    car_speed = car_velocity.length()
    try:
        car_velocity_direction = car_velocity.normalized()
        car_velocity_direction_flat = car_velocity.flat().normalized()
    except ZeroDivisionError:
        print("Car velocity is zero")
        controls.throttle = 1.0
        return
    time_to_ball = None
    i = 0
    slice_increment = 20
    min_time_dif = len(ball_prediction.slices) - 1
    #ball_slice = ball_prediction.slices[0]
    # We need to adjust car speed to make the circle smaller

    for i in range(0, len(ball_prediction.slices), slice_increment):
        time_to_ball = simplest_calc_turning_time(car_speed, car_velocity_direction_flat, car_location.flat(), ball_location.flat(),
                                                  car_length=150)
        if time_to_ball is None:
            #print("Time to ball is None at index: ", i)
            continue
        time_to_ball = time_to_ball[0] + time_to_ball[1]
        min_time_dif = min(int(time_to_ball*60), min_time_dif)
        ball_location = Vec3(ball_prediction.slices[i].physics.location)
    for i in range(max(min_time_dif-slice_increment//2, 0), min(min_time_dif+slice_increment//2, len(ball_prediction.slices))):
        time_to_ball = simplest_calc_turning_time(car_speed, car_velocity_direction_flat, car_location.flat(), ball_location.flat(),
                                                  car_length=150)
        if time_to_ball is None:
            #print("Time to ball is None at index: ", i)
            continue
        time_to_ball = time_to_ball[0] + time_to_ball[1]
        min_time_dif = min(int(time_to_ball*60), min_time_dif)
        ball_location = Vec3(ball_prediction.slices[i].physics.location)
    print("Selected index: ", min_time_dif)
    ball_location = Vec3(ball_prediction.slices[min_time_dif].physics.location)
    # Draw some things to help understand what the bot is thinking
    bot.renderer.draw_line_3d(car_location, ball_location, bot.renderer.white())
    bot.renderer.draw_string_3d(car_location, 1, 1, f'Speed: {car_velocity.length():.1f}', bot.renderer.white())
    bot.renderer.draw_rect_3d(ball_location, 8, 8, True, bot.renderer.cyan(), centered=True)

    #ball_location = ball_prediction.slices[int(time_to_ball*60)].physics.location
    #ball_location = Vec3(ball_prediction.slices[0].physics.location)
    inverse_k = curvature(car_speed)    # The maximum curvature we can turn. Bigger value means smaller circle.
    desired_k = desired_curvature(car_location, ball_location, car_velocity_direction)
    desired_k_boost = desired_curvature2(car_location, ball_location, car_velocity_direction) # The maximum curvature we want to be able to turn
    #boost_k = curvature(min(2300,car_speed+500)) # The maximum curvature we can turn with boost
    boost_k = k_epsilon*10

    steering = steer_toward_target(packet.game_cars[bot.index], ball_location)
    #print(car_speed, inverse_k, desired_k, boost_k, steering)
    if steering == 1:
        # Can't turn with current speed
        if inverse_k < desired_k:
            controls.throttle = -1
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f"ChaseBall: Overturn", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"ChaseBall: Desired: {desired_k:.6f}", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,80), 1, 1, f"ChaseBall: Current: {inverse_k:.6f}", bot.renderer.white())
            #controls.throttle = 1
            #controls.handbrake = 1
        # Can turn but only with current speed
        elif inverse_k < desired_k + k_epsilon:
            controls.throttle = 0.02
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f"ChaseBall: Perfect", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"ChaseBall: Desired: {desired_k:.6f}", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,80), 1, 1, f"ChaseBall: Current: {inverse_k:.6f}", bot.renderer.white())
            #controls.handbrake = 1
        else:
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f"ChaseBall: Underturn1", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"ChaseBall: Desired: {desired_k:.6f}", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,80), 1, 1, f"ChaseBall: Current: {inverse_k:.6f}", bot.renderer.white())
            controls.throttle = 1
    else:
        # We can turn we a lot of speed so use boost
        if boost_k > desired_k_boost:
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f"ChaseBall: Boost", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"ChaseBall: Desired: {desired_k_boost:.6f}", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,70), 1, 1, f"ChaseBall: Old: {desired_k:.6f}", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,80), 1, 1, f"ChaseBall: Boost: {boost_k:.6f}", bot.renderer.white())
            controls.throttle = 1
            controls.boost = True if not packet.game_cars[bot.index].is_super_sonic else False
        # Can turn with higher speeds
        elif inverse_k > desired_k:
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f"ChaseBall: Underturn2", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"ChaseBall: Desired: {desired_k:.6f}", bot.renderer.white())
            bot.renderer.draw_string_3d(car_location+Vec3(0,0,80), 1, 1, f"ChaseBall: Current: {inverse_k:.6f}", bot.renderer.white())
            controls.throttle = 1
    if packet.game_cars[bot.index].physics.rotation.pitch < -pi/2:
        controls.jump = True
    controls.steer = steering
    end_time = perf_counter()
    #print(f"Time to execute: {(end_time-start_time)/120:.2f} frames")
    return

