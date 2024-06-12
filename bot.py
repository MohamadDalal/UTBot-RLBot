from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.boost_pad_tracker import BoostPadTracker
from util.sequence import Sequence

from strategy.attackStrategies import AttackStrategy
from strategy.kickoffStrategies import KickoffStrategy

# First class that implements BaseAgent is loaded by RLBot

class MyBot(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.active_sequence: Sequence = None
        self.boost_pad_tracker = BoostPadTracker()
        self.kickoff_strategy = KickoffStrategy(index)
        self.defence_strategy = None
        self.attack_strategy = AttackStrategy(index)
        self.current_strategy = self.kickoff_strategy

    def initialize_agent(self):
        # Set up information about the boost pads now that the game is active and the info is available
        self.field_info = self.get_field_info()
        self.boost_pad_tracker.initialize_boosts(self.field_info)

    def choose_strategy(self, packet: GameTickPacket):
        if self.kickoff_strategy.isViable(packet):
            self.current_strategy = self.kickoff_strategy
        elif self.attack_strategy.isViable(packet):
            self.current_strategy = self.attack_strategy
        elif self.defence_strategy.isViable(packet):
            self.current_strategy = self.defence_strategy

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        """
        This function will be called by the framework many times per second. This is where you can
        see the motion of the ball, etc. and return controls to drive your car.
        """
        #controls = SimpleControllerState()

        # Keep our boost pad info updated with which pads are currently active
        self.boost_pad_tracker.update_boost_status(packet)

        # This is good to keep at the beginning of get_output. It will allow you to continue
        # any sequences that you may have started during a previous call to get_output.
        if self.active_sequence is not None and not self.active_sequence.done:
            controls = self.active_sequence.tick(packet)
            if controls is not None:
                return controls
        
        self.choose_strategy(packet)
        self.renderer.draw_string_2d(10, 20*(self.index+1), 1, 1, f"Current strategy{self.index}: {self.current_strategy}", self.renderer.white())
        controls = self.current_strategy.execute(packet, self)

        return controls
