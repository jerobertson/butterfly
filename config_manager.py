import datetime
import re

r = re.compile(r"\+(\d{2}):(\d{2})")

APP_CONFIG = {}

DEFAULT_LIGHT = {
    "max_brightness": {
        "morning": 180,
        "day": 180,
        "evening": 154,
        "night": 128
    },
    "temp_controlled": {
        "morning": True,
        "day": True,
        "evening": True,
        "night": True
    },
    "motion_activated": {
        "morning": True,
        "day": True,
        "evening": True,
        "night": True
    },
    "hs": {
        "morning": None,
        "day": None,
        "evening": None,
        "night": None
    },
}

DEFAULT_TV = {
    "entity": None,
    "cosy_mode": None,
    "bias": [],
    "ambient": [],
    "ignore": []
}

DEFAULT_ROOM = {
    "lights": {},
    "motion_sensors": [],
    "motion_locks": [],
    "motion_enablers": [],
    "lux_sensor": None,
    "lux_targets": {
        "morning": 70, # sunrise - 30 minutes | 5:10 -> 7:40
        "day": 70,
        "evening": 60,
        "night": 60 # sunset + 30 minutes |  16:20 -> 21:55
    },
    "temperature": {
        "morning": 5500,
        "day": 4000,
        "evening": 3200,
        "night": 2800
    },
    "delay": 300,
    "night_mode": "ignore"
}

DEFAULT_TRANSITION_TIME = 60

def init(config):
    global APP_CONFIG
    APP_CONFIG = config


def lerp_times(now, t1, t2):
    return (now - t1) / (t2 - t1)


def get_time_string():
    now = datetime.datetime.combine(datetime.date.min, datetime.datetime.now().time())

    sunset_str = r.sub(r"+\1\2", state.get("sensor.sun_next_setting"))
    sunset = datetime.datetime.strptime(sunset_str, "%Y-%m-%dT%H:%M:%S%z").time()

    morning = datetime.datetime.combine(datetime.date.min, datetime.time(4))
    day = datetime.datetime.combine(datetime.date.min, datetime.time(10))
    evening = datetime.datetime.combine(datetime.date.min, min(sunset, datetime.time(17)))
    night = datetime.datetime.combine(datetime.date.min, datetime.time(21))

    if now < morning:
        return ("night", "night", 0)
    elif now < day:
        return ("morning", "day", lerp_times(now, morning, day))
    elif now < evening:
        return ("day", "evening", lerp_times(now, day, evening))
    elif now < night:
        return ("evening", "night", lerp_times(now, evening, night))
    else:
        return ("night", "night", 0)


def get_rooms():
    try:
        return [room for room in APP_CONFIG["rooms"]]
    except:
        return []


def get_lights(room):
    try:
        return [light for light in APP_CONFIG["rooms"][room]["lights"]]
    except:
        return []


def get_light_config(room, light, key, needs_lerp=False):
    now, later, lerp = get_time_string()
    
    if not needs_lerp:
        return get_light_config_time(room, light, key, now)

    now_val = get_light_config_time(room, light, key, now)
    later_val = get_light_config_time(room, light, key, later)

    try:
        return int((later_val - now_val) * lerp + now_val)
    except:
        return now_val


def get_light_config_time(room, light, key, time):
    try:
        return APP_CONFIG["rooms"][room]["lights"][light][key][time]
    except:
        try:
            if isinstance(APP_CONFIG["rooms"][room]["lights"][light][key], dict): raise Exception
            return APP_CONFIG["rooms"][room]["lights"][light][key]
        except:
            room_value = get_room_config_time(room, key, time)
            return room_value if room_value != None else DEFAULT_LIGHT[key][time]


def get_room_config(room, key, needs_lerp=False):
    now, later, lerp = get_time_string()
    
    if not needs_lerp:
        return get_room_config_time(room, key, now)

    now_val = get_room_config_time(room, key, now)
    later_val = get_room_config_time(room, key, later)

    try:
        return int((later_val - now_val) * lerp + now_val)
    except:
        return now_val

def get_room_config_time(room, key, time):
    try: 
        return APP_CONFIG["rooms"][room][key][time]
    except:
        try:
            if isinstance(APP_CONFIG["rooms"][room][key], dict): raise Exception
            return APP_CONFIG["rooms"][room][key]
        except:
            try:
                return DEFAULT_ROOM[key][time]
            except:
                try:
                    return DEFAULT_ROOM[key]
                except:
                    return None


def get_temp_controlled_lights(room):
    return [light for light in APP_CONFIG["rooms"][room]["lights"] if get_light_config(room, light, "temp_controlled")]


def get_hs_controlled_lights(room):
    return [light for light in APP_CONFIG["rooms"][room]["lights"] if get_light_config(room, light, "hs") is not None]


def get_motion_activated_lights(room):
    return [light for light in APP_CONFIG["rooms"][room]["lights"] if get_light_config(room, light, "motion_activated")]


def get_tv_config(room, key):
    try:
        return APP_CONFIG["rooms"][room]["tv"][key]
    except:
        return DEFAULT_TV[key]


def get_night_mode(room):
    try:
        return "ignore" if state.get(APP_CONFIG["night_mode"]) == "off" else get_room_config(room, "night_mode")
    except:
        return "ignore"


def get_trigger_condition(room):
    motion_sensors = get_room_config(room, "motion_sensors")
    motion_sensors_condition = " not in ['off', 'unavailable'] or ".join(motion_sensors) + " not in ['off', 'unavailable']" if motion_sensors else "1 == 2"

    return motion_sensors_condition


def get_enablers_condition(room):
    motion_enablers = get_room_config(room, "motion_enablers")
    return " not in ['off', 'unavailable'] or ".join(motion_enablers) + " not in ['off', 'unavailable']" if motion_enablers else "1 == 1"


def get_locks_condition(room):
    motion_locks = get_room_config(room, "motion_locks")
    return " in ['off', 'unavailable'] and ".join(motion_locks) + " in ['off', 'unavailable']" if motion_locks else "1 == 1"


def get_activation_condition(room):
    enablers_condition = get_enablers_condition(room)
    locks_condition = get_locks_condition(room)

    return f"({enablers_condition}) and ({locks_condition})"


def get_wait_conditon(room):
    try:
        return " == 'off' and ".join(get_room_config(room, "motion_sensors")) + " == 'off'"
    except:
        return False


def get_transition_time(room):
    try:
        return APP_CONFIG["rooms"][room]["transition_time"]
    except:
        return DEFAULT_TRANSITION_TIME
