def spawn_car_in_showroom(loadout_config: LoadoutConfig, team: int, showcase_type: str, map_name: str,
                          launcher_prefs: RocketLeagueLauncherPreference):
    match_config = MatchConfig()
    match_config.game_mode = 'Soccer'
    match_config.game_map = map_name
    match_config.instant_start = True
    match_config.existing_match_behavior = 'Continue And Spawn'
    match_config.networking_role = NetworkingRole.none
    match_config.enable_state_setting = True
    match_config.skip_replays = True

    bot_config = PlayerConfig()
    bot_config.bot = True
    bot_config.rlbot_controlled = True
    bot_config.team = team
    bot_config.name = "Showroom"
    bot_config.loadout_config = loadout_config

    match_config.player_configs = [bot_config]
    match_config.mutators = MutatorConfig()
    match_config.mutators.boost_amount = 'Unlimited'
    match_config.mutators.match_length = 'Unlimited'

    global sm
    if sm is None:
        sm = SetupManager()
    sm.connect_to_game(launcher_preference=launcher_prefs)
    sm.load_match_config(match_config)
    sm.start_match()

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
    player_input = PlayerInput()
    team_sign = -1 if team == 0 else 1

    if showcase_type == "boost":
        player_input.boost = True
        player_input.steer = 1
        game_state.cars[0].physics.location.y = -1140
        game_state.cars[0].physics.velocity.x = 2300
        game_state.cars[0].physics.angular_velocity.z = 3.5

    elif showcase_type == "throttle":
        player_input.throttle = 1
        player_input.steer = 0.56
        game_state.cars[0].physics.location.y = -1140
        game_state.cars[0].physics.velocity.x = 1410
        game_state.cars[0].physics.angular_velocity.z = 1.5

    elif showcase_type == "back-center-kickoff":
        game_state.cars[0].physics.location.y = 4608 * team_sign
        game_state.cars[0].physics.rotation.yaw = -0.5 * pi * team_sign

    elif showcase_type == "goal-explosion":
        game_state.cars[0].physics.location.y = -2000 * team_sign
        game_state.cars[0].physics.rotation.yaw = -0.5 * pi * team_sign
        game_state.cars[0].physics.velocity.y = -2300 * team_sign
        game_state.ball.physics.location = Vector3(0, -3500 * team_sign, 93)

    sm.game_interface.update_player_input(player_input, 0)
    sm.game_interface.set_game_state(game_state)