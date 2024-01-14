import datetime

@pyscript_compile
def init(cm, sm, m):
    global config_manager
    global state_manager
    global motion
    config_manager = cm
    state_manager = sm
    motion = m


@pyscript_compile
def base_round(x, base=10):
    return base * round(x/base)


def react(room):
    log.debug(f"Butterfly is checking lux targets in '{room}'.")

    task.sleep(5)

    now = datetime.datetime.now()
    night_mode = config_manager.get_night_mode(room)
    is_motion_disabled = motion.is_motion_disabled(room, night_mode)
    is_room_occupied = state_manager.get_room_state(room, now) == "on"

    if is_motion_disabled:
        log.debug(f"Butterfly won't adjust light levels; '{room}' is disabled.")
        return

    if not is_room_occupied:
        log.debug(f"Butterfly won't adjust light levels; '{room}' is not occupied.")
        return

    target = config_manager.get_room_config(room, "lux_targets", needs_lerp=True)
    current = state_manager.get_room_lux(room)

    log.debug(f"Butterfly is reacting to lux - C:{current}, T:{target}, R:{room}")

    if target > current * 1.1:
        log.info(f"Butterfly thinks '{room}' is too dark; increasing brightness.")
        change_lights(room, now, delta="inc")

    elif current > target * 1.1:
        log.info(f"Butterfly thinks '{room}' is too bright; decreasing brightness.")
        change_lights(room, now, delta="dec")

    else:
        log.debug(f"Butterfly thinks '{room}' brightness is optimal.")
        change_lights(room, now)


def change_lights(room, now, delta=None):
    lights = get_lux_reactive_lights(room)

    to_change = {}
    brightness_map = {}
    # TODO: Only change lights if they have a kelvin value, otherwise leave them alone
    for light in lights:
        current_brightness, new_brightness = get_current_and_new_brightness(room, light, delta)

        if new_brightness:
            to_change.setdefault(new_brightness,[]).append(light)
            brightness_map[new_brightness] = current_brightness

    log.debug(f"Butterfly is transitioning the following lights in '{room}': {to_change}")
    transition_lights(room, to_change, brightness_map, now)


def get_lux_reactive_lights(room):
    temp_controlled_lights = config_manager.get_temp_controlled_lights(room)
    hs_controlled_lights = config_manager.get_hs_controlled_lights(room)
    motion_activated_lights = config_manager.get_motion_activated_lights(room)
    return [light for light in motion_activated_lights if light in temp_controlled_lights and light not in hs_controlled_lights]


def get_current_and_new_brightness(room, light, delta=None):
    # TODO: Make these global variables / configurable
    trim = 6
    min_change = 12
    max_change = 24
    pct_change = 0.8
    
    try:
        current_brightness = int(state.getattr(light)["brightness"]) if state.get(light) == "on" else 0
        max_brightness = config_manager.get_light_config(room, light, "max_brightness", needs_lerp=True)
        min_brightness = config_manager.get_light_config(room, light, "min_brightness", needs_lerp=True)

        new_brightness = current_brightness
        if delta == "dec":
            min_dec = current_brightness - min_change
            max_dec = current_brightness - max_change
            pct_dec = current_brightness * pct_change
            new_brightness = int(min(min_brightness, max(max_dec, min(min_dec, pct_dec))))
        elif delta == "inc":
            min_inc = current_brightness + min_change
            max_inc = current_brightness + max_change
            pct_inc = current_brightness / pct_change
            new_brightness = int(min(max_brightness, max(min_inc, min(max_inc, pct_inc))))

        clamped_brightness = base_round(new_brightness, base=trim)

        return (current_brightness, clamped_brightness)
    except:
        return (None, None)


def transition_lights(room, to_change, brightness_map, initial_timestamp):
    transition_time = 30
    step = 6

    temperature = config_manager.get_room_config(room, "temperature", needs_lerp=True)

    i = 0
    while i < transition_time and state_manager.get_room_state(room, initial_timestamp) == "on":
        for target_brightness in to_change.keys():
            lights = to_change[target_brightness]
            new_brightness = (target_brightness - brightness_map[target_brightness]) * ((i := i + step) / transition_time) + brightness_map[target_brightness]
            service.call("light", "turn_on", entity_id=lights, brightness=new_brightness, kelvin=temperature, transition=step-1)
        task.sleep(step)
