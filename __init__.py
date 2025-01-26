import datetime

from . import config_manager
from . import state_manager
from . import motion
from . import lux_reactor
from . import tv

# Butterfly: Beautiful lighting, seamless transitions

TRIGGERS = {}

@time_trigger('startup')
def butterfly():
    log.info("Butterfly is starting up...")
    
    config_manager.init(pyscript.app_config)
    state_manager.init(config_manager)

    motion.init(config_manager, state_manager)
    tv.init(config_manager, state_manager)
    lux_reactor.init(config_manager, state_manager, motion)

    for room in config_manager.get_rooms():
        detected_trigger = motion_detected_factory(room)
        activated_trigger = motion_activated_factory(room)
        tv_trigger = tv_factory(room)
        lux_trigger = lux_reactor_factory(room)
        TRIGGERS[room] = (detected_trigger, activated_trigger, tv_trigger, lux_trigger)

    log.info("Butterfly is ready!")


def motion_detected_factory(room):
    if not config_manager.get_room_config(room, "motion_sensors"):
        log.warning(f"Butterfly doesn't have any motion sensors available for '{room}'.")
        return

    log.info(f"Butterfly is creating a room trigger for '{room}'.")

    @state_trigger(config_manager.get_trigger_condition(room))
    @event_trigger(f"BUTTERFLY_MANUAL_MOTION_TRIGGER_{room}")
    @task_unique(f"butterfly_motion_sensor_{room}")
    def motion_detected():
        motion.motion_detected(room)
        
    return motion_detected


def motion_activated_factory(room):
    trigger = config_manager.get_activation_condition(room)
    if trigger == "(1 == 1) and (1 == 1)":
        log.warning(f"Butterfly doesn't have any motion activators available for '{room}'.")
        return

    log.info(f"Butterfly is creating an activation trigger for '{room}'.")

    @state_trigger(trigger)
    @task_unique(f"butterfly_motion_sensor_{room}", kill_me=True)
    def motion_activated():
        motion.motion_activated(room)
        
    return motion_activated


def tv_factory(room):
    tv_entity = config_manager.get_tv_config(room, "entity")
    if not tv_entity:
        log.warning(f"Butterfly doesn't have a TV entity configured for '{room}'.")
        return

    log.info(f"Butterfly is creating a TV trigger for '{room}'.")

    @state_trigger(tv_entity)
    @task_unique(f"butterfly_tv_{room}")
    def tv_changed(trigger_type=None, var_name=None, value=None, old_value=None):
        if value in ["off", "unavailable"] and old_value not in ["off", "unavailable"]:
            tv.tv_off(room)
        elif value not in ["off", "unavailable"] and old_value in ["off", "unavailable"]:
            tv.tv_on(room)

    return tv_changed


def lux_reactor_factory(room):
    lux_sensor = config_manager.get_room_config(room, "lux_sensor")
    if not lux_sensor:
        log.warning(f"Butterfly doesn't have a lux sensor available for '{room}'.")
        return

    log.info(f"Butterfly is powering up the lux reactor for '{room}'.")

    @time_trigger("period(now + 90s, 90s)")
    @state_trigger(lux_sensor)
    @event_trigger(f"BUTTERFLY_MANUAL_LUX_TRIGGER_{room}")
    @task_unique(f"butterfly_lux_reactor_{room}")
    def lux_react():
        lux_reactor.react(room)

    return lux_react


@service
def butterfly_reset_lighting(room):
    log.info(f"Butterfly is manually resetting the lighting for '{room}'.")

    state_manager.invalidate_cache(room)
    event.fire(f"BUTTERFLY_MANUAL_MOTION_TRIGGER_{room}")
