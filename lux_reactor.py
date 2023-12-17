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

    time = config_manager.get_time_string()
    target = config_manager.get_lux_target(room, time)
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
    for light in lights:
        new_brightness = get_new_brightness(room, light, is_dimmer)
        if new_brightness:
            to_change.setdefault(new_brightness,[]).append(light)

    log.debug(f"Butterfly is transitioning the following lights in '{room}': {to_change}")
    transition_lights(room, to_change, now)


def get_lux_reactive_lights(room):
    temp_controlled_lights = config_manager.get_temp_controlled_lights(room)
    hs_controlled_lights = config_manager.get_hs_controlled_lights(room)
    motion_activated_lights = config_manager.get_motion_activated_lights(room)
    return [light for light in motion_activated_lights if light in temp_controlled_lights and light not in hs_controlled_lights]


def get_new_brightness(room, light, is_dimmer=False):
    try:
        current_brightness = int(state.getattr(light)["brightness"])
        max_brightness = config_manager.get_light_max_brightness(room, light)
        min_brightness = 25
        new_brightness = current_brightness * 0.9 if is_dimmer else current_brightness / 0.9
        clamped_brightness = int(max(min(new_brightness, max_brightness), min_brightness))
        if clamped_brightness != current_brightness:
            return clamped_brightness
    except:
        return None


def transition_lights(room, to_change, initial_timestamp):
    transition_time = 60
    step = 3

    i = 0
    while i < transition_time and state_manager.get_room_state(room, initial_timestamp) == "on":
        for brightness in to_change.keys():
            lights = to_change[brightness]
            new_brightness = brightness * (transition_time-i-step)/transition_time
            # service.call("light", "turn_on", entity_id=lights, brightness=new_brightness, transition=step-1)
        task.sleep(step)
        i += step
