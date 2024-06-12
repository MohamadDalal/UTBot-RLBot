from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction

from strategy.baseStrategy import BaseStrategy
from util.vec import Vec3
from util.orientation import Orientation, relative_location
from strategy.attack_utils.targeting import chaseGoal
from util.ball_prediction_analysis import find_slice_at_time

class AttackStrategy(BaseStrategy):

    def __init__(self, botIndex: int):
        super().__init__(botIndex)
        self.strategies = {"ShootAtNet": ShootAtNet(botIndex)}

    def __str__(self):
        return "AttackStrategy"

    def isViable(self, packet: GameTickPacket):
        return True

    def execute(self, packet: GameTickPacket, bot: BaseAgent):
        # Use ball prediction model to decide how to hit.
        return self.strategies["ShootAtNet"].execute(packet, bot, bot.get_ball_prediction_struct())

class ShootAtNet(BaseStrategy):

    def __init__(self, botIndex: int):
        super().__init__(botIndex)

    def isViable(self, packet: GameTickPacket):
        # Find a way to determine if the bot is in a position to shoot at the net:
        # - Can reach the ball with an angle towards net
        # - Can reach the ball with good speed (If large turns are needed, or drifting is needed, or there is boost for extra speed, etc.)
        # - Can reach the ball before the opponent (Very hard to evaluate due to opponent skill and intentions)

        pass

    def execute(self, packet: GameTickPacket, bot: BaseAgent, ball_prediction: BallPrediction):
        # Use ball prediction model to decide how to hit.
        controls = SimpleControllerState()

        my_car = packet.game_cars[bot.index]
        car_location = Vec3(my_car.physics.location)
        car_velocity = Vec3(my_car.physics.velocity)
        car_rotation = Vec3(my_car.physics.rotation.pitch, my_car.physics.rotation.yaw, my_car.physics.rotation.roll)
        ball_location = Vec3(packet.game_ball.physics.location)
        car_oriantation = Orientation(my_car.physics.rotation)
        target_location = ball_location

        #bot.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f'Dist to ball: {car_location.dist(ball_location):.1f}', bot.renderer.white())
        predict_time = min(2, car_location.dist(ball_location)/1000)
        #bot.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f'Predict time: {predict_time:.1f}', bot.renderer.white())
        ball_in_future = find_slice_at_time(ball_prediction, packet.game_info.seconds_elapsed + predict_time)

        # ball_in_future might be None if we don't have an adequate ball prediction right now, like during
        # replays, so check it to avoid errors.
        if ball_in_future is not None:
            target_location = Vec3(ball_in_future.physics.location)
            bot.renderer.draw_line_3d(ball_location, target_location, bot.renderer.cyan())

        # Draw some things to help understand what the bot is thinking
        bot.renderer.draw_line_3d(car_location, target_location, bot.renderer.white())
        bot.renderer.draw_string_3d(car_location, 1, 1, f'Speed: {car_velocity.length():.1f}', bot.renderer.white())
        bot.renderer.draw_rect_3d(target_location, 8, 8, True, bot.renderer.cyan(), centered=True)

        #controls.steer = steer_toward_target(my_car, target_location)
        chaseGoal(bot, packet, bot.field_info, controls, ball_location=target_location)
        ball_relative_to_car = relative_location(car_location, car_oriantation, ball_location).normalized()
        controls.throttle = 1.0 # if ball_relative_to_car[0] > -0.95 else -1.0
        if abs(ball_relative_to_car[1]) < 0.1 and controls.throttle > 0.8: controls.boost = True
        else: controls.boost = False
        #controls.boost = True if abs(ball_relative_to_car[1]) < 0.1 else False 
        # You can set more controls if you want, like controls.boost.
        #bot.renderer.draw_string_3d(car_location+Vec3(0,0,50), 1, 1, f"({ball_relative_to_car})", bot.renderer.white())
        #bot.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"index: {bot.index}", bot.renderer.white())

        return controls