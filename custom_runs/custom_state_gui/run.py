from rlbot.setup_manager import SetupManager
from rlbot.parsing.rlbot_config_parser import create_bot_config_layout
from rlbot.utils.structures.start_match_structures import MAX_PLAYERS
from rlbot.utils.python_version_check import check_python_version
from pathlib import Path

from rlbot_gui.type_translation.set_state_translation import dict_to_game_state, dict_to_physics, dict_to_vec, dict_to_rot

# WIP

DEFAULT_LOGGER = 'rlbot'

def main():

    print("starting")
    check_python_version()
    config = create_bot_config_layout()
    config.parse_file(Path(__file__).parent / "rlbot.cfg", max_index=MAX_PLAYERS)
    manager = SetupManager()
    manager.load_config(framework_config=config)
    manager.connect_to_game()
    manager.launch_early_start_bot_processes()
    manager.start_match()
    manager.launch_bot_processes()
    # Maybe call this in a thread instead, and then use it to control stuff.
    manager.infinite_loop()  # Runs forever until interrupted

if __name__ == '__main__':
    try:
        from rlbot.utils import logging_utils
        logger = logging_utils.get_logger(DEFAULT_LOGGER)
    except Exception as e:
        print("Encountered exception: ", e)
        print("Press enter to close.")
        input()
    #print(__file__)
    main()