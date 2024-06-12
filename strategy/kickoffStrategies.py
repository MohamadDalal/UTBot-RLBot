from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from strategy.baseStrategy import BaseStrategy
from time import perf_counter
from util.vec import Vec3
from rlbot.utils.structures.ball_prediction_struct import BallPrediction
from util.sequence import Sequence, ControlStep
from util.drive import steer_toward_target
from util.basic_moves import begin_front_flip

class KickoffStrategy(BaseStrategy):

    def __init__(self, botIndex: int):
        super().__init__(botIndex)
        self.strategies = {"WaveDash": WaveDashKickoff(botIndex)}
        self.last_call = perf_counter()
        self.kickoff_type = 0

    def __str__(self):
        return "KickoffStrategy"

    def isViable(self, packet: GameTickPacket):
        return packet.game_info.is_kickoff_pause

    def execute(self, packet: GameTickPacket, bot: BaseAgent):
        #car_velocity = Vec3(packet.game_cars[bot.index].physics.velocity)
        
        if perf_counter() - self.last_call > 5:
            car_location = Vec3(packet.game_cars[bot.index].physics.location)
            ball_location = Vec3(packet.game_ball.physics.location)
            dist_to_ball = Vec3.dist(car_location, ball_location)
            print("Updating Kickoff type")
            if dist_to_ball < 3500:
                self.kickoff_type = 0
            elif dist_to_ball > 4400:
                self.kickoff_type = 2
            else:
                self.kickoff_type = 1
            print(self.kickoff_type, dist_to_ball)
        self.last_call = perf_counter()
        car_location = Vec3(packet.game_cars[bot.index].physics.location)
        bot.renderer.draw_string_3d(car_location+Vec3(0,0,60), 1, 1, f"Kickoff Type: {self.kickoff_type}", bot.renderer.white())
        # Use ball prediction model to decide how to hit.
        return self.strategies["WaveDash"].execute(packet, bot, self.kickoff_type)

class WaveDashKickoff(BaseStrategy):


    def __init__(self, botIndex: int):
        super().__init__(botIndex)

    def begin_wave_dash(self, bot: BaseAgent, packet: GameTickPacket, wait_duration = None):
        if wait_duration is None:
            bot.active_sequence = Sequence([
                ControlStep(duration=0.01, controls=SimpleControllerState(jump=True, boost=True)),
                ControlStep(duration=0.15, controls=SimpleControllerState(pitch=-1, boost=True)),
                ControlStep(duration=0.05, controls=SimpleControllerState(boost=True)),
                ControlStep(duration=0.43, controls=SimpleControllerState(pitch=1, boost=True)),
                ControlStep(duration=0.2, controls=SimpleControllerState(jump=True, pitch=-1, boost=True)),
            ])
        else:
            bot.active_sequence = Sequence([
                ControlStep(duration=0.01, controls=SimpleControllerState(jump=True, boost=True)),
                ControlStep(duration=0.15, controls=SimpleControllerState(pitch=-1, boost=True)),
                ControlStep(duration=0.05, controls=SimpleControllerState(boost=True)),
                ControlStep(duration=0.43, controls=SimpleControllerState(pitch=1, boost=True)),
                ControlStep(duration=wait_duration, controls=SimpleControllerState(boost=True)),
                ControlStep(duration=0.2, controls=SimpleControllerState(jump=True, pitch=-1, boost=True)),
            ])
        controls = bot.active_sequence.tick(packet)
        if controls is not None:
            return controls

    def execute(self, packet: GameTickPacket, bot: BaseAgent, kickoff_type: int):
        controls = SimpleControllerState()

        car_velocity = Vec3(packet.game_cars[bot.index].physics.velocity)
        car_location = Vec3(packet.game_cars[bot.index].physics.location)
        ball_location = Vec3(packet.game_ball.physics.location)
        dist_to_ball = Vec3.dist(car_location, ball_location)

        # We'll do a wave dash if the car is moving at a certain speed depending on kickoff type.
        if kickoff_type == 0:
            if 1000 < car_velocity.length() < 1050:
                return self.begin_wave_dash(bot, packet)
            elif dist_to_ball < 400:
                return begin_front_flip(bot, packet)
        elif kickoff_type == 1:
            if 1500 < car_velocity.length() < 1550:
                return self.begin_wave_dash(bot, packet, wait_duration=0.1)
            elif dist_to_ball < 400:
                return begin_front_flip(bot, packet)
        else:
            if 1500 < car_velocity.length() < 1550:
                return self.begin_wave_dash(bot, packet)
            elif dist_to_ball < 400:
                return begin_front_flip(bot, packet)
        controls.steer = steer_toward_target(packet.game_cars[bot.index], ball_location)
        controls.throttle = 1.0
        controls.boost = True        
        return controls