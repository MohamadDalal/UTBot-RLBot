from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.ball_prediction_analysis import find_slice_at_time
from util.boost_pad_tracker import BoostPadTracker
from util.drive import steer_toward_target
from util.sequence import Sequence, ControlStep
from util.vec import Vec3
from util.orientation import Orientation, relative_location

from kickoff import handle_kickoff
from targeting import chaseGoal

from math import sin,cos

class MyBot(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.active_sequence: Sequence = None
        self.boost_pad_tracker = BoostPadTracker()

    def initialize_agent(self):
        # Set up information about the boost pads now that the game is active and the info is available
        self.field_info = self.get_field_info()
        self.boost_pad_tracker.initialize_boosts(self.field_info)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """
        This function will be called by the framework many times per second. This is where you can
        see the motion of the ball, etc. and return controls to drive your car.
        """
        controls = SimpleControllerState()

        # Keep our boost pad info updated with which pads are currently active
        self.boost_pad_tracker.update_boost_status(packet)

        # This is good to keep at the beginning of get_output. It will allow you to continue
        # any sequences that you may have started during a previous call to get_output.
        if self.active_sequence is not None and not self.active_sequence.done:
            controls = self.active_sequence.tick(packet)
            if controls is not None:
                return controls

        # Gather some information about our car and the ball
        my_car = packet.game_cars[self.index]
        car_location = Vec3(my_car.physics.location)
        car_velocity = Vec3(my_car.physics.velocity)
        car_rotation = Vec3(my_car.physics.rotation.pitch, my_car.physics.rotation.yaw, my_car.physics.rotation.roll)
        ball_location = Vec3(packet.game_ball.physics.location)
        car_oriantation = Orientation(my_car.physics.rotation)
        #self.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f"Dist to Ball: {Vec3.dist(car_location, ball_location):.0f}", self.renderer.white())

        # By default we will chase the ball, but target_location can be changed later
        target_location = ball_location

        if True: #car_location.dist(ball_location) > 1500:
            # We're far away from the ball, let's try to lead it a little bit
            ball_prediction = self.get_ball_prediction_struct()  # This can predict bounces, etc
            #self.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f'Dist to ball: {car_location.dist(ball_location):.1f}', self.renderer.white())
            predict_time = min(2, car_location.dist(ball_location)/1000)
            #self.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f'Predict time: {predict_time:.1f}', self.renderer.white())
            ball_in_future = find_slice_at_time(ball_prediction, packet.game_info.seconds_elapsed + predict_time)

            # ball_in_future might be None if we don't have an adequate ball prediction right now, like during
            # replays, so check it to avoid errors.
            if ball_in_future is not None:
                target_location = Vec3(ball_in_future.physics.location)
                self.renderer.draw_line_3d(ball_location, target_location, self.renderer.cyan())

        # Draw some things to help understand what the bot is thinking
        self.renderer.draw_line_3d(car_location, target_location, self.renderer.white())
        self.renderer.draw_string_3d(car_location, 1, 1, f'Speed: {car_velocity.length():.1f}', self.renderer.white())
        self.renderer.draw_rect_3d(target_location, 8, 8, True, self.renderer.cyan(), centered=True)

        car_yaw_vector = Vec3(cos(car_rotation[1]), sin(car_rotation[1]),0)
        ball_behind = Vec3.dot(car_yaw_vector, target_location-car_location)<0

        if packet.game_info.is_kickoff_pause:
            handle_kickoff(self, packet, controls)
            return controls

        
        #self.renderer.draw_line_3d(car_location, car_location+300*car_yaw_vector, self.renderer.green())
        #self.renderer.draw_rect_3d(Vec3(0,0,0), 50, 50, True, self.renderer.red(), centered=True)
        #self.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f"({car_yaw_vector[0]:.3f},{car_yaw_vector[1]:.3f})", self.renderer.white())

        #controls.steer = steer_toward_target(my_car, target_location)
        #controls.steer = chaseGoal(self, packet, self.field_info)
        chaseGoal(self, packet, self.field_info, controls, ball_location=target_location)
        #self.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, str(Vec3.dot(car_yaw_vector, target_location-car_location) > 0), self.renderer.white())
        #controls.throttle = -1.0 if ball_behind else 1.0
        ball_relative_to_car = relative_location(car_location, car_oriantation, ball_location).normalized()
        controls.throttle = 1.0 # if ball_relative_to_car[0] > -0.95 else -1.0
        if abs(ball_relative_to_car[1]) < 0.1 and controls.throttle > 0.8: controls.boost = True
        else: controls.boost = False
        #controls.boost = True if abs(ball_relative_to_car[1]) < 0.1 else False 
        # You can set more controls if you want, like controls.boost.
        #self.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f"({ball_relative_to_car})", self.renderer.white())
        #self.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"index: {self.index}", self.renderer.white())

        return controls
