from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket, FieldInfoPacket

from util.drive import steer_toward_target
from util.vec import Vec3

from math import pi, cos, sqrt


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

def chaseGoal(self: BaseAgent, packet: GameTickPacket, field_info: FieldInfoPacket, controls: SimpleControllerState):
    car_location = Vec3(packet.game_cars[self.index].physics.location)
    ball_location = Vec3(packet.game_ball.physics.location)
    if (self.team + 1) % 2 == 0:
        opponent_goal = field_info.goals[(self.team + 1) % 2]
        left_target_location = Vec3(opponent_goal.location) + Vec3(0.5*opponent_goal.width,0,0) - Vec3(200,0,0)
        right_target_location:Vec3 = left_target_location - Vec3(opponent_goal.width,0,0) + Vec3(400,0,0)
    else:
        opponent_goal = field_info.goals[(self.team + 1) % 2]
        left_target_location = Vec3(opponent_goal.location) + Vec3(0.5*opponent_goal.width,0,0) + Vec3(200,0,0)
        right_target_location:Vec3 = left_target_location - Vec3(opponent_goal.width,0,0) - Vec3(400,0,0)

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

    #min_turn_radius = turn_radius2(Vec3(packet.game_cars[self.index].physics.velocity).length())
    #wanted_turn_radius = Vec3.length(offset_ball_location-car_location)
    ##self.renderer.draw_string_3d(car_location+Vec3(0,0,80), 1, 1, f"Min turn radius: {min_turn_radius}", self.renderer.white())
    ##self.renderer.draw_string_3d(car_location+Vec3(0,0,70), 1, 1, f"Wanted turn radius: {wanted_turn_radius}", self.renderer.white())
    #
    #radius_plus, radius_minus = turn_radius(Vec3(packet.game_cars[self.index].physics.velocity).flat(), direction_of_approach.flat(), car_location.flat(), offset_ball_location.flat())
    ##needed_radius = turn_radius(Vec3(packet.game_cars[self.index].physics.velocity).flat(), direction_of_approach, car_location, offset_ball_location)
    #needed_radius = radius_plus if abs(radius_plus) < abs(radius_minus) else radius_minus
    #self.renderer.draw_string_3d(car_location+Vec3(0,0,90), 1, 1, f"Radius min: {min_turn_radius}", self.renderer.white())
    #self.renderer.draw_string_3d(car_location+Vec3(0,0,80), 1, 1, f"Radius-: {radius_minus}", self.renderer.white())
    #self.renderer.draw_string_3d(car_location+Vec3(0,0,70), 1, 1, f"Radius+: {radius_plus}", self.renderer.white())
    ##self.renderer.draw_string_3d(car_location+Vec3(0,0,70), 1, 1, f"Radius: {needed_radius}", self.renderer.white())
    #p = car_location.flat() + needed_radius*Vec3(packet.game_cars[self.index].physics.velocity).flat().cross(Vec3(0,0,-1)).normalized()
    #turn_target = offset_ball_location.flat() - (direction_of_approach.flat().dot(offset_ball_location.flat() - p))*direction_of_approach.flat()
    #self.renderer.draw_line_3d(car_location, p, self.renderer.green())
    #self.renderer.draw_line_3d(turn_target, turn_target + needed_radius*direction_of_approach.flat().cross(Vec3(0,0,-1)).normalized(), self.renderer.green())
    #self.renderer.draw_line_3d(car_location, car_location + 200*Vec3(packet.game_cars[self.index].physics.velocity).flat().normalized(), self.renderer.red())
    #self.renderer.draw_line_3d(offset_ball_location, offset_ball_location + 200*direction_of_approach.flat().normalized(), self.renderer.red())
    ##self.renderer.draw_line_3d(car_location, car_location + radius_plus*Vec3(packet.game_cars[self.index].physics.velocity).flat().cross(Vec3(0,0,-1)).normalized(), self.renderer.red())

    controls.steer =  steer_toward_target(packet.game_cars[self.index], final_target)
    #self.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"steer: {controls.steer}", self.renderer.white())


def turn_radius(current_orientation: Vec3, desired_orientation: Vec3, current_location: Vec3, desired_location: Vec3):
    # Calculate the radius of the circle we need to turn in
    # Needs to consider when we cannot possible turn for the ball with the desired oriantation
    radius_direction = current_orientation.cross(Vec3(0,0,-1)).normalized()
    c = desired_location - current_location - (desired_orientation.dot(desired_location) + desired_orientation.dot(current_location))*desired_orientation
    d = radius_direction + (desired_orientation.dot(radius_direction))*desired_orientation
    det = c.dot(d)**2-(d.dot(d)-1)*c.dot(c)
    if det < 0:
        print(det)
        return 0, 0
    radius_plus = (c.dot(d)+sqrt(det))/(d.dot(d)-1)
    radius_minus = (c.dot(d)-sqrt(det))/(d.dot(d)-1)
    #return radius_plus if abs(radius_plus) < abs(radius_minus) else radius_minus
    return radius_plus, radius_minus

def max_speed_given_radius(v):
    # Calculate the max speed we can go in given the radius we need to traverse
    pass