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
    "lights": [],
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


def get_time_string():
    now = int(datetime.datetime.now().strftime("%H"))
    sunset_str = r.sub(r"+\1\2", state.get("sensor.sun_next_setting"))
    sunset = int(datetime.datetime.strptime(sunset_str, "%Y-%m-%dT%H:%M:%S%z").strftime("%H")) + 1
    if now < 4: 
        return "night"
    elif now < 10:
        return "morning"
    elif now < min(sunset, 17):
        return "day"
    elif now < 21:
        return "evening"
    else:
        return "night"


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


def get_light_config(room, light, key):
    time = get_time_string()
    try:
        return APP_CONFIG["rooms"][room]["lights"][light][key][time]
    except:
        try:
            if isinstance(APP_CONFIG["rooms"][room]["lights"][light][key], dict): raise Exception
            return APP_CONFIG["rooms"][room]["lights"][light][key]
        except:
            try: 
                return APP_CONFIG["rooms"][room][key][time]
            except:
                try:
                    if isinstance(APP_CONFIG["rooms"][room][key], dict): raise Exception
                    return APP_CONFIG["rooms"][room][key]
                except:
                    return DEFAULT_LIGHT[key][time]


def get_temp_controlled_lights(room):
    return [light for light in APP_CONFIG["rooms"][room]["lights"] if get_light_config(room, light, "temp_controlled")]


def get_hs_controlled_lights(room):
    return [light for light in APP_CONFIG["rooms"][room]["lights"] if get_light_config(room, light, "hs") is not None]


def get_motion_activated_lights(room):
    return [light for light in APP_CONFIG["rooms"][room]["lights"] if get_light_config(room, light, "motion_activated")]


def get_light_max_brightness(room, light):
    try:
        return int(APP_CONFIG["rooms"][room]["lights"][light]["max_brightness"][get_time_string()])
    except:
        pass

    try:
        return int(APP_CONFIG["rooms"][room]["lights"][light]["max_brightness"])
    except:
        pass

    return int(DEFAULT_LIGHT["max_brightness"][get_time_string()])


def get_room_temperature(room):
    try:
        return int(APP_CONFIG["rooms"][room]["temperature"][get_time_string()])
    except:
        pass

    try:
        return int(APP_CONFIG["rooms"][room]["temperature"])
    except:
        pass

    return int(DEFAULT_ROOM["temperature"][get_time_string()])


def get_room_config(room, key):
    try:
        return APP_CONFIG["rooms"][room][key]
    except:
        return DEFAULT_ROOM[key]


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


def get_lux_target(room, time):
    try:
        return APP_CONFIG["rooms"][room]["lux_targets"][time]
    except:
        return DEFAULT_ROOM["lux_targets"][time]