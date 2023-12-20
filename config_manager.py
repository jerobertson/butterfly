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

# TODO: Make this configurable
DEFAULT_TIME = {
    "morning": 4,
    "day": 10,
    "evening": 17,
    "night": 21
}

def init(config):
    global APP_CONFIG
    global SUNSET
    global MORNING
    global DAY
    global EVENING
    global NIGHT
    APP_CONFIG = config
    SUNSET = datetime.datetime.strptime(r.sub(r"+\1\2", state.get("sensor.sun_next_setting")), "%Y-%m-%dT%H:%M:%S%z").time()
    MORNING = build_datetime(datetime.time(DEFAULT_TIME["morning"]))
    DAY = build_datetime(datetime.time(DEFAULT_TIME["day"]))
    EVENING = build_datetime(min(SUNSET, datetime.time(DEFAULT_TIME["evening"])))
    NIGHT = build_datetime(datetime.time(DEFAULT_TIME["night"]))


@pyscript_compile
def build_datetime(time):
    return datetime.datetime.combine(datetime.date.min, time)


@pyscript_compile
def ease_in_out_quad(x):
    # https://easings.net/#easeInOutQuad
    return 2 * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 2) / 2


@pyscript_compile
def lerp_times(now, t1, t2):
    return ease_in_out_quad((now - t1) / (t2 - t1))


@pyscript_compile
def get_time_string():
    now = build_datetime(datetime.datetime.now().time())

    if now < MORNING:
        return ("night", "night", 0)
    elif now < DAY:
        return ("morning", "day", lerp_times(now, MORNING, DAY))
    elif now < EVENING:
        return ("day", "evening", lerp_times(now, DAY, EVENING))
    elif now < NIGHT:
        return ("evening", "night", lerp_times(now, EVENING, NIGHT))
    else:
        return ("night", "night", 0)


@pyscript_compile
def get_rooms():
    try:
        return [room for room in APP_CONFIG["rooms"]]
    except:
        return []


@pyscript_compile
def get_lights(room):
    try:
        return [light for light in APP_CONFIG["rooms"][room]["lights"]]
    except:
        return []


@pyscript_compile
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


@pyscript_compile
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


@pyscript_compile
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


@pyscript_compile
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


@pyscript_compile
def get_temp_controlled_lights(room):
    return [light for light in APP_CONFIG["rooms"][room]["lights"] if get_light_config(room, light, "temp_controlled")]


@pyscript_compile
def get_hs_controlled_lights(room):
    return [light for light in APP_CONFIG["rooms"][room]["lights"] if get_light_config(room, light, "hs") is not None]


@pyscript_compile
def get_motion_activated_lights(room):
    return [light for light in APP_CONFIG["rooms"][room]["lights"] if get_light_config(room, light, "motion_activated")]


@pyscript_compile
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


@pyscript_compile
def get_trigger_condition(room):
    motion_sensors = get_room_config(room, "motion_sensors")
    motion_sensors_condition = " not in ['off', 'unavailable'] or ".join(motion_sensors) + " not in ['off', 'unavailable']" if motion_sensors else "1 == 2"

    return motion_sensors_condition


@pyscript_compile
def get_enablers_condition(room):
    motion_enablers = get_room_config(room, "motion_enablers")
    return " not in ['off', 'unavailable'] or ".join(motion_enablers) + " not in ['off', 'unavailable']" if motion_enablers else "1 == 1"


@pyscript_compile
def get_locks_condition(room):
    motion_locks = get_room_config(room, "motion_locks")
    return " in ['off', 'unavailable'] and ".join(motion_locks) + " in ['off', 'unavailable']" if motion_locks else "1 == 1"


@pyscript_compile
def get_activation_condition(room):
    enablers_condition = get_enablers_condition(room)
    locks_condition = get_locks_condition(room)

    return f"({enablers_condition}) and ({locks_condition})"


@pyscript_compile
def get_wait_conditon(room):
    try:
        return " == 'off' and ".join(get_room_config(room, "motion_sensors")) + " == 'off'"
    except:
        return False


@pyscript_compile
def get_transition_time(room):
    try:
        return APP_CONFIG["rooms"][room]["transition_time"]
    except:
        return DEFAULT_TRANSITION_TIME
