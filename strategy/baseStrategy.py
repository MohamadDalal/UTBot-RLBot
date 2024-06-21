from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.structures.ball_prediction_struct import BallPrediction

class BaseStrategy():

    def __init__(self, botIndex: int, bot: BaseAgent):
        self.botIndex = botIndex
        self.bot = bot

    def isViable(self, packet: GameTickPacket):
        return False

    def execute(self, packet: GameTickPacket, bot: BaseAgent) -> SimpleControllerState:
        return SimpleControllerState()