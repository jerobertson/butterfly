import datetime

STATE = {}

def init(cm):
    global STATE
    global config_manager
    config_manager = cm
    STATE = {}
    for room in config_manager.get_rooms():
        invalidate_cache(room)


def invalidate_cache(room):
    STATE[room] = {}
    STATE[room]["last_motion"] = datetime.datetime.fromtimestamp(0)


def get_room_lux(room):
    try:
        sensor = config_manager.get_room_config(room, "lux_sensor")
        return int(state.get(sensor))
    except:
        return 0


def put_last_motion_detected(room, time):
    STATE[room]["last_motion"] = time


def get_last_motion_detected(room):
    return STATE[room]["last_motion"]


def get_room_state(room, now):
    delay = config_manager.get_room_config(room, "delay")
    last_motion = get_last_motion_detected(room)
    
    if now - last_motion > datetime.timedelta(seconds=delay * 2 + 60):
        return "expired"
    elif now - last_motion > datetime.timedelta(seconds=delay + 60):
        return "off"
    elif now - last_motion > datetime.timedelta(seconds=delay):
        return "dimming"
    else:
        return "on"


def store_lights(room):
    to_store = {} # Example: {153: ['light.study_ceiling']}
    for light in [light for light in config_manager.get_lights(room) if state.get(light) == "on"]:
        attr = state.getattr(light)
        brightness = attr["brightness"] if "brightness" in attr else config_manager.get_light_max_brightness(room, light)
        to_store.setdefault(brightness,[]).append(light)
    STATE[room]["lights"] = to_store


def retrieve_lights(room):
    return STATE[room]["lights"]
