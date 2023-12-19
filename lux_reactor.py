import datetime

def init(cm, sm, m):
    global config_manager
    global state_manager
    global motion
    config_manager = cm
    state_manager = sm
    motion = m


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

    target = config_manager.get_room_config(room, "lux_targets")
    current = state_manager.get_room_lux(room)

    log.debug(f"Butterfly is reacting to lux - C:{current}, T:{target}, R:{room}")

    if target > current * 1.1:
        log.info(f"Butterfly thinks '{room}' is too dark; increasing brightness.")
        change_lights(room, now, is_dimmer=False)

    elif current > target * 1.1:
        log.info(f"Butterfly thinks '{room}' is too bright; decreasing brightness.")
        change_lights(room, now, is_dimmer=True)

    else:
        log.debug(f"Butterfly thinks '{room}' brightness is optimal.")


def change_lights(room, now, is_dimmer=False):
    lights = get_lux_reactive_lights(room)

    to_change = {}
    brightness_map = {}
    for light in lights:
        current_brightness, new_brightness = get_current_and_new_brightness(room, light, is_dimmer)
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


def get_current_and_new_brightness(room, light, is_dimmer=False):
    try:
        current_brightness = int(state.getattr(light)["brightness"])
        max_brightness = config_manager.get_light_config(room, light, "max_brightness", needs_lerp=True)
        min_brightness = 25
        new_brightness = current_brightness * 0.9 if is_dimmer else current_brightness / 0.9
        clamped_brightness = int(max(min(new_brightness, max_brightness), min_brightness))
        if clamped_brightness != current_brightness:
            return (current_brightness, clamped_brightness)
        else:
            return (None, None)
    except:
        return (None, None)


def transition_lights(room, to_change, brightness_map, initial_timestamp):
    transition_time = 30
    step = 6

    i = 0
    while i < transition_time and state_manager.get_room_state(room, initial_timestamp) == "on":
        for target_brightness in to_change.keys():
            lights = to_change[target_brightness]
            new_brightness = (target_brightness - brightness_map[target_brightness]) * ((i := i + step) / transition_time) + brightness_map[target_brightness]
            service.call("light", "turn_on", entity_id=lights, brightness=new_brightness, transition=step-1)
        task.sleep(step)
