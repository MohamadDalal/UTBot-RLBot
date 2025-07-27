from collections.abc import Callable
from typing import Any, Iterable, Mapping
from rlbot.setup_manager import SetupManager
from rlbot.gateway_util import NetworkingRole
from rlbot.parsing.rlbot_config_parser import create_bot_config_layout
from rlbot.parsing.agent_config_parser import load_bot_appearance, create_looks_configurations
from rlbot.utils.structures.start_match_structures import MAX_PLAYERS
from rlbot.utils.python_version_check import check_python_version
from rlbot.matchconfig.match_config import PlayerConfig, MatchConfig, MutatorConfig
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.game_state_util import GameState, CarState, BallState, Physics, Vector3, Rotator
from rlbot.utils.structures.game_data_struct import GameTickPacket
from pathlib import Path
from threading import Thread
from time import sleep, perf_counter
import numpy as np
import pickle

DEFAULT_LOGGER = 'rlbot'

def pickleWrite(obj, filename):
    with open(filename, "wb") as f:
        pickle.dump(obj, f)

def pickleRead(filename):
    with open(filename, "rb") as f:
        obj = pickle.load(f)
    return obj


class RunThread(Thread):

    def __init__(self, manager: SetupManager, desired_speed = 850):
        super().__init__()
        self.packet = GameTickPacket()
        self.manager = manager
        self.running = True
        self.player_input = PlayerInput()
        self.desired_speed = min(desired_speed, 1235.85)  # Max turning speed without boost is 1235.85
        self.epsilon = 1
        self.throttle = 0.02

    def run(self):
        while self.running:
            self.manager.game_interface.update_live_data_packet(self.packet)
            car = self.packet.game_cars[0]
            velocity = np.array((car.physics.velocity.x, car.physics.velocity.y, car.physics.velocity.z))
            current_speed = np.linalg.norm(velocity)
            #print(type(velocity))
            if abs(current_speed - self.desired_speed) > self.epsilon:
                self.throttle += (self.desired_speed - current_speed)/100
                self.throttle = max(min(1, self.throttle), 0)
                self.player_input.throttle = self.throttle
                self.player_input.steer = 1
                #self.player_input.handbrake = False
                self.manager.game_interface.update_player_input(self.player_input, 0)
                print(abs(current_speed - self.desired_speed))
            else:
                self.player_input.throttle = self.throttle
                self.player_input.steer = 1
                self.player_input.handbrake = True
                self.manager.game_interface.update_player_input(self.player_input, 0)
            #print(current_speed, self.throttle)
            print(car.physics.angular_velocity.z, self.player_input.handbrake)
            sleep(0.1)

    def close(self):
        self.running = False

class MeasureConstantSpeedThread(Thread):

    def __init__(self, manager: SetupManager):
        super().__init__()
        self.packet = GameTickPacket()
        self.manager = manager
        self.running = True
        self.player_input = PlayerInput()
        self.desired_speed = 0
        self.epsilon = 1
        self.throttle = 0.02

    def run(self):
        # [0.88, 0.75, 0.64, 0.54]
        desired_speeds = [1200 - 50*i for i in range(25)]
        desired_throttle = [0.88, 0.75]
        ds_index = 2
        self.desired_speed = desired_speeds[ds_index]
        last_adjustment = perf_counter()
        while self.running and ds_index < 24:
            self.manager.game_interface.update_live_data_packet(self.packet)
            car = self.packet.game_cars[0]
            velocity = np.array((car.physics.velocity.x, car.physics.velocity.y, car.physics.velocity.z))
            current_speed = np.linalg.norm(velocity)
            if abs(current_speed - self.desired_speed) > self.epsilon:
                self.throttle += (self.desired_speed - current_speed)/100
                self.throttle = max(min(1, self.throttle), 0)
                self.player_input.throttle = self.throttle
                self.player_input.steer = 1
                #self.player_input.handbrake = False
                self.manager.game_interface.update_player_input(self.player_input, 0)
                sleep(0.5)
                last_adjustment = perf_counter()
                print(self.desired_speed - current_speed)
            elif (perf_counter() - last_adjustment) > 5:
                print(ds_index)
                desired_throttle.append(self.throttle)
                ds_index += 1
                self.desired_speed = desired_speeds[ds_index]
            #else:
            #    print(perf_counter() - last_adjustment)
        print(desired_speeds)
        print(desired_throttle)
        self.close()

    def close(self):
        self.running = False

class MeasureSpeedFromThrottleThread(Thread):

    def __init__(self, manager: SetupManager):
        super().__init__()
        self.packet = GameTickPacket()
        self.manager = manager
        self.running = True
        self.player_input = PlayerInput()
        self.desired_speed = 0
        self.epsilon = 1
        self.throttle = 0.0

    def run(self):
        # Thr:  [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5,  0.55, 0.6,  0.65, 0.7,  0.75, 0.8,  0.85, 0.9,  0.95, 1]
        # Mean: [0, 320,  521, 608,  679, 753,  811, 866,  929, 983,  1027, 1055, 1080, 1108, 1130, 1150, 1171, 1188, 1204, 1221, 1235]
        # Std:  [0, 24,   3.7, 1,    0.7, 0.6,  0.5, 0.6,  0.8, 1,    0.12, 0.07, 0.06, 0.06, 0.04, 0.03, 0.03, 0.03, 0.02, 0.02, 0.02]
        throttle_vals = [0.05*i for i in range(21)]
        speed_vals = [[] for _ in range(len(throttle_vals))]
        speed_means = []
        speed_stddiv = []
        t_index = 0
        record_time = 10
        game_state = GameState(
            cars={0: CarState(physics=Physics(
                location=Vector3(0, 0, 20),
                velocity=Vector3(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, 0, 0)
            ))},
            ball=BallState(physics=Physics(
                location=Vector3(0, 0, -100),
                velocity=Vector3(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0)
            ))
        )
        self.manager.game_interface.set_game_state(game_state)
        self.throttle = throttle_vals[t_index]
        self.player_input.throttle = self.throttle
        self.player_input.steer = 1
        self.manager.game_interface.update_player_input(self.player_input, 0)
        last_adjustment = perf_counter()
        while self.running and t_index < 20:
            if (perf_counter() - last_adjustment) > record_time:
                print(t_index)
                t_index += 1
                self.throttle = throttle_vals[t_index]
                self.player_input.throttle = self.throttle
                self.player_input.steer = 1
                self.manager.game_interface.update_player_input(self.player_input, 0)
                last_adjustment = perf_counter()
            else:
                self.manager.game_interface.update_live_data_packet(self.packet)
                car = self.packet.game_cars[0]
                velocity = np.array((car.physics.velocity.x, car.physics.velocity.y, car.physics.velocity.z))
                current_speed = np.linalg.norm(velocity)
                speed_vals[t_index].append(current_speed)
                sleep(0.1)
        for i in speed_vals:
            speed_means.append(np.array(i)[len(i)//2:].mean())
            speed_stddiv.append(np.array(i)[len(i)//2:].std())
        print(throttle_vals)
        print(speed_means)
        print(speed_stddiv)
        pickleWrite(speed_vals, "custom_runs\measure_turning\MeasureSpeedFromThrottleTest.pickle")
        self.close()

    def close(self):
        self.running = False


def main():

    print("starting")
    check_python_version()
    #config = create_bot_config_layout()
    #config.parse_file(Path(__file__).parent / "rlbot.cfg", max_index=1)
    #print(config)
    match_config = MatchConfig()
    match_config.game_mode = 'Soccer'
    match_config.game_map = "Mannfield"
    match_config.instant_start = True
    match_config.existing_match_behavior = 'Continue And Spawn'
    match_config.networking_role = NetworkingRole.none
    match_config.enable_state_setting = True
    match_config.skip_replays = True

    bot_config = PlayerConfig()
    bot_config.bot = True
    bot_config.rlbot_controlled = True
    bot_config.team = 0
    bot_config.name = "UTBot"
    bot_config.loadout_config = load_bot_appearance(create_looks_configurations().parse_file(Path(__file__).parent / "appearance.cfg"), 0)

    match_config.player_configs = [bot_config]
    match_config.mutators = MutatorConfig()
    match_config.mutators.boost_amount = 'Unlimited'
    match_config.mutators.match_length = 'Unlimited'

    manager = SetupManager()
    manager.connect_to_game()
    manager.load_match_config(match_config)
    #manager.launch_early_start_bot_processes()
    manager.start_match()
    start_velocity = 1440

    game_state = GameState(
        cars={0: CarState(physics=Physics(
            location=Vector3(0, 0, 20),
            velocity=Vector3(start_velocity, 0, 0),
            angular_velocity=Vector3(0, 0, 0),
            rotation=Rotator(0, 0, 0)
        ))},
        ball=BallState(physics=Physics(
            location=Vector3(0, 0, -100),
            velocity=Vector3(0, 0, 0),
            angular_velocity=Vector3(0, 0, 0)
        ))
    )
    player_input = PlayerInput()
    player_input.throttle = 0.02
    #player_input.boost = True
    player_input.steer = 1

    manager.game_interface.update_player_input(player_input, 0)
    manager.game_interface.set_game_state(game_state)
    #runThread = RunThread(manager, start_velocity)
    runThread = MeasureSpeedFromThrottleThread(manager)

    #manager.launch_bot_processes()
    runThread.start()
    manager.infinite_loop()  # Runs forever until interrupted
    runThread.close()
    runThread.join()
    print("Joined thread. Finished running.")

if __name__ == '__main__':
    #try:
    #    from rlbot.utils import logging_utils
    #    logger = logging_utils.get_logger(DEFAULT_LOGGER)
    #except Exception as e:
    #    print("Encountered exception: ", e)
    #    print("Press enter to close.")
    #    input()
    #print(__file__)
    main()