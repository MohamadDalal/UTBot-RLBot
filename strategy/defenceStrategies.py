from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction

from strategy.baseStrategy import BaseStrategy
from util.vec import Vec3
from util.orientation import Orientation, relative_location
from strategy.attack_utils.targeting import chaseGoal
from util.ball_prediction_analysis import find_slice_at_time, predict_future_goal
from util.drive import steer_toward_target
from util.turning import inverse_curvature, desired_curvature

def calc_time_to_ball(car_location: Vec3, car_velocity: Vec3, ball_location: Vec3, ball_velocity: Vec3, ball_prediction: BallPrediction = None, max_iter = 10, epsilon = 0.1):
    car_to_ball = ball_location - car_location
    car_to_ball_dir = car_to_ball.normalized()
    car_dir = car_velocity.normalized()
    ## Placeholder function
    time_to_ball = ((car_to_ball).length() + (1 - car_to_ball_dir.dot(car_dir))**3 * 300)/car_velocity.length()
    if ball_prediction is None:
        return time_to_ball
    old_time_to_ball = 0
    iter = 0
    while abs(time_to_ball - old_time_to_ball) > epsilon or iter < max_iter:
        old_time_to_ball = time_to_ball
        ball_in_future = find_slice_at_time(ball_prediction, time_to_ball)
        if ball_in_future is not None:
            ball_location = Vec3(ball_in_future.physics.location)
            ball_velocity = Vec3(ball_in_future.physics.velocity)
            car_to_ball = ball_location - car_location
            time_to_ball = ((car_to_ball).length() + (1 - car_to_ball.normalized().dot(car_velocity.normalized()))**3 * 300)/car_velocity.length()
            iter += 1
        else:
            break
    return time_to_ball

class DefenceStrategy(BaseStrategy):

    def __init__(self, botIndex: int, bot: BaseAgent):
        super().__init__(botIndex, bot)
        self.strategies = {"getBoost": GetBoost(botIndex, bot),
                           "defendGoal": DefendGoal(botIndex, bot)}
        self.current_strategy = self.strategies["getBoost"]

    def __str__(self):
        return str(self.current_strategy)

    def isViable(self, packet: GameTickPacket):
        ball_location = Vec3(packet.game_ball.physics.location)
        ball_velocity = Vec3(packet.game_ball.physics.velocity)
        car_location = Vec3(packet.game_cars[self.botIndex].physics.location)
        car_velocity = Vec3(packet.game_cars[self.botIndex].physics.velocity)
        opponent_location = Vec3(packet.game_cars[(self.botIndex + 1) % 2].physics.location)
        opponent_velocity = Vec3(packet.game_cars[(self.botIndex + 1) % 2].physics.velocity)
        ball_prediction = self.bot.get_ball_prediction_struct()
        boost_empty =  packet.game_cars[self.botIndex].boost < 60
        my_time_to_ball = calc_time_to_ball(car_location, car_velocity, ball_location, ball_velocity, ball_prediction)
        opp_time_to_ball = calc_time_to_ball(opponent_location, opponent_velocity, ball_location, ball_velocity, ball_prediction)
        can_make_ball = my_time_to_ball < opp_time_to_ball
        self.bot.renderer.draw_string_2d(10, 80+20*(self.botIndex+1), 1, 1, f"Time to ball {self.botIndex}: {my_time_to_ball}", self.bot.renderer.white())
        # TODO: defend if ball is heading to own net
        is_goal = predict_future_goal(ball_prediction, self.bot.team) is not None
        # TODO: Implement a way to know if opponent is dribbling or shooting. So we rush if they are dribbling.
        #       This is based on 3 facts:
        #       - Opponent last hit the ball
        #       - Speed of ball is low despite it being hit recently
        #       - Opponent is very close to ball (within 500 units)
        return boost_empty and not can_make_ball or is_goal

    def execute(self, packet: GameTickPacket, bot: BaseAgent):
        #print("Executing DefenceStrategy")
        # Use ball prediction model to decide how to hit.
        for i in self.strategies:
            if self.strategies[i].isViable(packet, bot.get_ball_prediction_struct()):
                self.current_strategy = self.strategies[i]
                break
        return self.current_strategy.execute(packet, bot, bot.get_ball_prediction_struct())

class GetBoost(BaseStrategy):

    def __init__(self, botIndex: int, bot):
        super().__init__(botIndex, bot)

    def __str__(self):
        return "Defence: GetBoost"

    def isViable(self, packet: GameTickPacket, ball_prediction: BallPrediction):
        # Get boost if:
        # - Boost is available (Almost always true)
        # - Car is not at full boost
        # - Ball is not going to net
        # - There is not a high chance of opponent shooting at net (advanced and optional)
        is_goal = predict_future_goal(ball_prediction, self.bot.team)
        if is_goal is None:
            return packet.game_cars[self.botIndex].boost < 80
        else:
            return packet.game_cars[self.botIndex].boost < 80
        

    def execute(self, packet: GameTickPacket, bot: BaseAgent, ball_prediction: BallPrediction):
        # Use ball prediction model to decide how to hit.
        controls = SimpleControllerState()

        my_car = packet.game_cars[bot.index]
        car_location = Vec3(my_car.physics.location)
        car_velocity = Vec3(my_car.physics.velocity)
        car_speed = car_velocity.length()
        car_orientation = Orientation(my_car.physics.rotation)
        #car_rotation = Vec3(my_car.physics.rotation.pitch, my_car.physics.rotation.yaw, my_car.physics.rotation.roll)
        min_dist = 10000
        # THIS MIGHT BE WRONG
        curvature = inverse_curvature(car_speed)
        target_location = Vec3(bot.field_info.goals[bot.team].location)
        #for i in bot.boost_pad_tracker.get_full_boosts():
        for i in bot.boost_pad_tracker.boost_pads:
            dist = (i.location - car_location).length()
            dist = calc_time_to_ball(car_location, car_velocity, i.location, Vec3(0,0,0))
            if i.is_active and dist < min_dist and curvature < desired_curvature(car_location, i.location, car_orientation.forward):
                min_dist = dist
                target_location = i.location
        #dir_to_target = (target_location - car_location).normalized()
        #car_dir = car_velocity.normalized()

        bot.renderer.draw_line_3d(car_location, target_location, bot.renderer.white())
        bot.renderer.draw_string_3d(car_location, 1, 1, f'Speed: {car_velocity.length():.1f}', bot.renderer.white())
        bot.renderer.draw_rect_3d(target_location, 8, 8, True, bot.renderer.cyan(), centered=True)

        controls.steer = steer_toward_target(my_car, target_location)
        controls.throttle = 1.0
        if (inverse_curvature(2300) < desired_curvature(car_location, target_location, car_orientation.forward)
            and controls.throttle > 0.8 and not my_car.is_super_sonic):
            controls.boost = True
        else: controls.boost = False
        #controls.boost = True if abs(ball_relative_to_car[1]) < 0.1 else False 

        return controls

class DefendGoal(BaseStrategy):

    def __init__(self, botIndex: int, bot: BaseAgent):
        super().__init__(botIndex, bot)

    def __str__(self):
        return "Defence: DefendGoal"
    
    def isViable(self, packet: GameTickPacket, ball_prediction: BallPrediction):
        is_goal = predict_future_goal(ball_prediction, self.bot.team)
        # is_goal is a ball slice which has a physics packet and the time in game seconds it happens
        # TODO: Make it compare seconds with current game seconds to see if goal happens within a certain time
        return is_goal is not None
    
    def execute(self, packet: GameTickPacket, bot: BaseAgent, BallPrediction: BallPrediction):
        return self.bot.attack_strategy.execute(packet, bot)
