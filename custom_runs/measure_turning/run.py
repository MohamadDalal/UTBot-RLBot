from rlbot.setup_manager import SetupManager
from rlbot.gateway_util import NetworkingRole
from rlbot.parsing.rlbot_config_parser import create_bot_config_layout
from rlbot.parsing.agent_config_parser import load_bot_appearance, create_looks_configurations
from rlbot.utils.structures.start_match_structures import MAX_PLAYERS
from rlbot.utils.python_version_check import check_python_version
from rlbot.matchconfig.match_config import PlayerConfig, MatchConfig, MutatorConfig
from rlbot.utils.structures.bot_input_struct import PlayerInput
from rlbot.utils.game_state_util import GameState, CarState, BallState, Physics, Vector3, Rotator
from pathlib import Path

DEFAULT_LOGGER = 'rlbot'

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
    player_input.throttle = 0.01
    player_input.steer = 1

    manager.game_interface.update_player_input(player_input, 0)
    manager.game_interface.set_game_state(game_state)
    #manager.launch_bot_processes()
    #manager.infinite_loop()  # Runs forever until interrupted

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