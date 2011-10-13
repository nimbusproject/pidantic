import logging
from pidantic.pidfork import PIDanticFork

def get_pidantic(driver_name, argv, auto_restart=False, log=logging, use_channel=False, channel_is_stdio=False):

    pidantic = None
    if driver_name == "fork":
        pidantic = PIDanticFork(argv, auto_restart=auto_restart, log=log, use_channel=use_channel, channel_is_stdio=channel_is_stdio)

    return pidantic