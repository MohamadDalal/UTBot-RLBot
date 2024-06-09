from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.drive import steer_toward_target
from util.vec import Vec3
from basic_moves import begin_front_flip, begin_wave_dash

kickoff_type = 0
last_call = 0


def handle_kickoff(self: BaseAgent, packet: GameTickPacket, controls:SimpleControllerState):
    global kickoff_type, last_call
    # Kickoff strats
    car_velocity = Vec3(packet.game_cars[self.index].physics.velocity)
    car_location = Vec3(packet.game_cars[self.index].physics.location)
    ball_location = Vec3(packet.game_ball.physics.location)
    dist_to_ball = Vec3.dist(car_location, ball_location)
    if packet.game_info.frame_num - last_call > 600:
        print("Updating Kickoff type")
        if dist_to_ball < 4000:
             kickoff_type = 0
        elif dist_to_ball > 4400:
            kickoff_type = 2
        else:
            kickoff_type = 1
    #print(packet.game_info.frame_num - last_call)
    last_call = packet.game_info.frame_num
    self.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"Kickoff Type: {kickoff_type}", self.renderer.white())

    if kickoff_type == 0:
        if 1000 < car_velocity.length() < 1050: # and not ball_behind:
            # We'll do a front flip if the car is moving at a certain speed.
            controls.boost = True
            return begin_wave_dash(self, packet)

            #if self.index == 0:
            #    controls.boost = True
            #    return begin_wave_dash(self, packet)
            #else:
            #    return begin_front_flip(self, packet)
        elif dist_to_ball < 400:
            return begin_front_flip(self, packet)
        else:
            controls.steer = steer_toward_target(packet.game_cars[self.index], ball_location)
            controls.throttle = 1.0
            controls.boost = True
    elif kickoff_type == 1:
        if 1500 < car_velocity.length() < 1550: # and not ball_behind:
            # We'll do a front flip if the car is moving at a certain speed.
            controls.boost = True
            return begin_wave_dash(self, packet, wait_duration=0.1)

            #if self.index == 0:
            #    controls.boost = True
            #    return begin_wave_dash(self, packet)
            #else:
            #    return begin_front_flip(self, packet)
        elif dist_to_ball < 400:
            return begin_front_flip(self, packet)
        else:
            controls.steer = steer_toward_target(packet.game_cars[self.index], ball_location)
            controls.throttle = 1.0
            controls.boost = True
    else:
        if 1500 < car_velocity.length() < 1550: # and not ball_behind:
            # We'll do a front flip if the car is moving at a certain speed.
            controls.boost = True
            return begin_wave_dash(self, packet)

            #if self.index == 0:
            #    controls.boost = True
            #    return begin_wave_dash(self, packet)
            #else:
            #    return begin_front_flip(self, packet)
        elif dist_to_ball < 400:
            return begin_front_flip(self, packet)
        else:
            controls.steer = steer_toward_target(packet.game_cars[self.index], ball_location)
            controls.throttle = 1.0
            controls.boost = True
    