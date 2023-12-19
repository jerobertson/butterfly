import datetime

@pyscript_compile
def init(cm, sm):
    global config_manager
    global state_manager
    config_manager = cm
    state_manager = sm


def is_disabled_by_lock(room):
    locks = config_manager.get_room_config(room, "motion_locks")
    if not locks: 
        return False
    return [lock for lock in locks if state.get(lock) not in ["off", "unavailable"]]


def is_disabled_by_enablers(room):
    enablers = config_manager.get_room_config(room, "motion_enablers")
    if not enablers:
        return False
    return not [enabler for enabler in enablers if state.get(enabler) not in ["off", "unavailable"]]


def is_disabled_by_night_mode(night_mode):
    return night_mode == "deny"


def is_disabled_by_tv(room):
    tv = config_manager.get_tv_config(room, "entity")
    if not tv:
        return False
    return state.get(tv) not in ["off", "unavailable"]


def is_motion_disabled(room, night_mode):
    return is_disabled_by_lock(room) or is_disabled_by_enablers(room) or is_disabled_by_night_mode(night_mode) or is_disabled_by_tv(room)


def is_lux_met(room):
    target = config_manager.get_room_config(room, "lux_targets", needs_lerp=True)
    current = state_manager.get_room_lux(room)
    return current >= target


def turn_lights_on(room, night_mode, initial_timestamp):
    night_mode_brightness = 3
    night_mode_temperature = 2000

    temperature = config_manager.get_room_config(room, "temperature", needs_lerp=True)

    temp_controlled_lights = config_manager.get_temp_controlled_lights(room)
    hs_controlled_lights = config_manager.get_hs_controlled_lights(room)
    motion_activated_lights = config_manager.get_motion_activated_lights(room)

    motion_activated_temp_controlled_lights = [light for light in motion_activated_lights if light in temp_controlled_lights and light not in hs_controlled_lights]
    motion_activated_hs_controlled_lights = [light for light in motion_activated_lights if light in hs_controlled_lights]
    motion_activated_other_lights = [light for light in motion_activated_lights if light not in temp_controlled_lights and light not in hs_controlled_lights]

    too_dark = not is_lux_met(room)

    if night_mode == "dim":
        log.debug(f"Butterfly is setting dim lights in '{room}'; Night Mode is enabled.")
        service.call("light", "turn_on", entity_id=temp_controlled_lights, brightness=night_mode_brightness, kelvin=night_mode_temperature)
        state_manager.invalidate_cache(room)

    elif state_manager.get_room_state(room, initial_timestamp) == "expired" and too_dark:
        log.debug(f"Butterfly hasn't seen any movement in '{room}' for a while; setting default lighting.")
        to_enable = {}
        # temp lights
        for light in motion_activated_temp_controlled_lights:
            brightness = config_manager.get_light_config(room, light, "max_brightness", needs_lerp=True)
            to_enable.setdefault(brightness,[]).append(light)
        for brightness in to_enable.keys():
            service.call("light", "turn_on", entity_id=to_enable[brightness], brightness=brightness, kelvin=temperature, transition=1)
        # hs lights
        for light in motion_activated_hs_controlled_lights:
            brightness = config_manager.get_light_config(room, light, "max_brightness")
            hs = config_manager.get_light_config(room, light, "hs")
            service.call("light", "turn_on", entity_id=light, brightness=brightness, hs_color=hs, transition=1)
        # other lights
        to_enable = {}
        for light in motion_activated_other_lights:
            brightness = config_manager.get_light_config(room, light, "max_brightness", needs_lerp=True)
            to_enable.setdefault(brightness,[]).append(light)
        for brightness in to_enable.keys():
            service.call("light", "turn_on", entity_id=to_enable[brightness], brightness=brightness, transition=1)

    elif state_manager.get_room_state(room, initial_timestamp) in ["off", "dimming"]:
        log.debug(f"Butterfly is restoring the last known lighting in '{room}'.")
        to_restore = state_manager.retrieve_lights(room)
        for brightness in to_restore.keys():
            service.call("light", "turn_on", entity_id=to_restore[brightness], brightness=brightness, transition=1)

    elif not too_dark:
        log.debug(f"Butterfly thinks '{room}' is already bright enough!")

    else:
        log.debug(f"Butterfly has already turned the lights on in '{room}'.")

    if not night_mode == "dim":
        state_manager.put_last_motion_detected(room, initial_timestamp)


def wait_for_no_motion(room, night_mode):
    delay = config_manager.get_room_config(room, "delay")

    log.debug(f"Butterfly is waiting for no motion to be detected in '{room}'.")
    task.wait_until(state_trigger=config_manager.get_wait_conditon(room))
    if not night_mode == "dim":
        state_manager.put_last_motion_detected(room, datetime.datetime.now())

    log.debug(f"Butterfly is waiting {delay}s before dimming the lights in '{room}'.")
    task.sleep(delay+1)


def turn_lights_off(room, night_mode):
    log.debug(f"Butterfly hasn't detected any motion in '{room}' for a while.")

    if is_motion_disabled(room, night_mode):
        log.debug(f"Butterfly won't trigger; '{room}' is disabled.")
        return

    log.debug(f"Butterfly is saving the current scene in '{room}' for later.")
    state_manager.store_lights(room)
    
    log.info(f"Butterfly is dimming the lights in '{room}'.")
    dimming_timestamp = datetime.datetime.now()
    transition_time = config_manager.get_transition_time(room)
    step = 3

    to_dim = state_manager.retrieve_lights(room)

    i = 0
    while i < transition_time and state_manager.get_room_state(room, dimming_timestamp) == "dimming":
        task.unique(f"butterfly_motion_sensor_{room}", kill_me=True)
        for brightness in to_dim.keys():
            lights = to_dim[brightness]
            new_brightness = brightness * (transition_time-i-step)/transition_time
            service.call("light", "turn_on", entity_id=lights, brightness=new_brightness, transition=step-1)
        task.sleep(step)
        i += step

    off_timestamp = datetime.datetime.now()
    
    log.debug(f"Butterfly has finished dimming the lights in '{room}' and will turn them off.")
    if state_manager.get_room_state(room, off_timestamp) != "on":
        task.unique(f"butterfly_motion_sensor_{room}", kill_me=True)
        service.call("light", "turn_off", entity_id=config_manager.get_lights(room), transition=1)


def motion_detected(room):
    initial_timestamp = datetime.datetime.now()
    night_mode = config_manager.get_night_mode(room)
    
    log.info(f"Butterfly detected motion in '{room}'.")

    if is_motion_disabled(room, night_mode):
        log.debug(f"Butterfly won't trigger; '{room}' is disabled.")
        state_manager.put_last_motion_detected(room, initial_timestamp)
        return

    turn_lights_on(room, night_mode, initial_timestamp)
    event.fire(f"BUTTERFLY_MANUAL_LUX_TRIGGER_{room}")
    wait_for_no_motion(room, night_mode)
    turn_lights_off(room, night_mode)

    
def motion_activated(room):
    night_mode = config_manager.get_night_mode(room)
    
    log.info(f"Butterfly has activated motion detection in '{room}'.")

    wait_for_no_motion(room, night_mode)
    turn_lights_off(room, night_mode)
