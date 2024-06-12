from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.sequence import Sequence, ControlStep

def begin_front_flip(self: BaseAgent, packet: GameTickPacket):
    # Send some quickchat just for fun
    self.send_quick_chat(team_only=False, quick_chat=QuickChatSelection.Information_IGotIt)

    # Do a front flip. We will be committed to this for a few seconds and the bot will ignore other
    # logic during that time because we are setting the active_sequence.
    self.active_sequence = Sequence([
        ControlStep(duration=0.05, controls=SimpleControllerState(jump=True)),
        ControlStep(duration=0.02, controls=SimpleControllerState(jump=False)),
        ControlStep(duration=0.2, controls=SimpleControllerState(jump=True, pitch=-1)),
        ControlStep(duration=0.8, controls=SimpleControllerState()),
    ])

    # Return the controls associated with the beginning of the sequence so we can start right away.
    return self.active_sequence.tick(packet)

def begin_wave_dash(self: BaseAgent, packet: GameTickPacket, wait_duration = None):
    # Need to make this less hardcoded
    # Send some quickchat just for fun
    self.send_quick_chat(team_only=False, quick_chat=QuickChatSelection.Information_IGotIt)

    if wait_duration is None:
        self.active_sequence = Sequence([
            ControlStep(duration=0.01, controls=SimpleControllerState(jump=True, boost=True)),
            #ControlStep(duration=0.02, controls=SimpleControllerState(jump=False, boost=True)),
            ControlStep(duration=0.15, controls=SimpleControllerState(pitch=-1, boost=True)),
            ControlStep(duration=0.05, controls=SimpleControllerState(boost=True)),
            ControlStep(duration=0.43, controls=SimpleControllerState(pitch=1, boost=True)),
            ControlStep(duration=0.2, controls=SimpleControllerState(jump=True, pitch=-1, boost=True)),
        ])
    else:
        self.active_sequence = Sequence([
            ControlStep(duration=0.01, controls=SimpleControllerState(jump=True, boost=True)),
            #ControlStep(duration=0.02, controls=SimpleControllerState(jump=False, boost=True)),
            ControlStep(duration=0.15, controls=SimpleControllerState(pitch=-1, boost=True)),
            ControlStep(duration=0.05, controls=SimpleControllerState(boost=True)),
            ControlStep(duration=0.43, controls=SimpleControllerState(pitch=1, boost=True)),
            ControlStep(duration=wait_duration, controls=SimpleControllerState(boost=True)),
            ControlStep(duration=0.2, controls=SimpleControllerState(jump=True, pitch=-1, boost=True)),
        ])
