import datetime

def init(cm, sm):
    global config_manager
    global state_manager
    config_manager = cm
    state_manager = sm


def is_cosy(room):
    cosy_entity = config_manager.get_tv_config(room, "cosy_mode")
    return state.get(cosy_entity) == "on" if cosy_entity else False


def tv_on(room):
    log.info(f"Butterfly is watching TV in '{room}' at {datetime.datetime.now()}")

    bias = config_manager.get_tv_config(room, "bias")
    ambient = config_manager.get_tv_config(room, "ambient")
    ignore = config_manager.get_tv_config(room, "ignore")
    to_dim = [light for light in config_manager.get_lights(room) if light not in ignore and light not in ambient and light not in bias]

    temperature = config_manager.get_room_config(room, "temperature", needs_lerp=True)
    transition = 5

    temp_controlled_lights = config_manager.get_temp_controlled_lights(room)
    hs_controlled_lights = config_manager.get_hs_controlled_lights(room)

    temp_controlled_ambient_lights = [light for light in temp_controlled_lights if light in ambient] if temp_controlled_lights else []
    hs_controlled_ambient_lights = [light for light in hs_controlled_lights if light in ambient] if hs_controlled_lights else []

    # TODO check cosy mode

    # Turn bias on
    to_enable = {}
    for light in bias:
        brightness = config_manager.get_light_config(room, light, "max_brightness")
        to_enable.setdefault(brightness,[]).append(light)
    for brightness in to_enable.keys():
        service.call("light", "turn_on", entity_id=to_enable[brightness], brightness=brightness, kelvin=6500, transition=transition)

    # Turn ambient on
    # temp lights
    to_enable = {}
    for light in temp_controlled_ambient_lights:
        brightness = config_manager.get_light_config(room, light, "max_brightness", needs_lerp=True)
        to_enable.setdefault(brightness,[]).append(light)
    for brightness in to_enable.keys():
        service.call("light", "turn_on", entity_id=to_enable[brightness], brightness=brightness, kelvin=temperature, transition=transition)
    # hs lights
    for light in hs_controlled_ambient_lights:
        brightness = config_manager.get_light_config(room, light, "max_brightness")
        hs = config_manager.get_light_config(room, light, "hs")
        service.call("light", "turn_on", entity_id=light, brightness=brightness, hs_color=hs, transition=transition)

    task.sleep(transition)

    # Turn others off
    service.call("light", "turn_off", entity_id=to_dim, transition=1)


def tv_off(room):
    log.info(f"Butterfly stopped watching TV in '{room}' at {datetime.datetime.now()}")

    bias = config_manager.get_tv_config(room, "bias")

    service.call("pyscript", "butterfly_reset_lighting", room=room)
    service.call("light", "turn_off", entity_id=bias, transition=10)