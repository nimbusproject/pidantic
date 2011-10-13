import logging
from pidantic.pidfork import PIDanticFork


_pidantic_classes = {}
_pidantic_classes['fork'] = PIDanticFork


def pidantic_factory(pid_string, event_callback, log=logging, use_channel=False, channel_is_stdio=False, **kwargs):
    """
    Create an object with the PIDantic interface.  The specific type of object created will depend on the pid_string
    argument.

    Parameters
    pid_string:
        The pid string has the following format:
        <driver name>:<driver specific string>
        In the case of the fork driver an example string were the program "/bin/true" is run would be:
        fork:/bin/true
        the keywords are driver specific as well.

    event_callback:
        This is a function with the signature callback(PIDantic, PIDanticEvents).  It is called whenever events o

    log:
        A python logging object for recording events specific to the operation of this library.  It does not record
         events in the process being run

    use_channel:
        Establish a special communication channel between this object and the child process that ill be run.  How
        the channel is created is driver specific.  In the fork driver it is a pipe to the child process.  In
        XXXX supervisord it will use a file, or a header on the stdio output.  TBD

    channel_is_stdio
        A boolean that determines if the channel will be the exact same thing as stdout/stdin.  There are times when
        a child process may be willing to use special handling code for messaging with its supervisor and times when
        it may not.  This features allows the channel messaging to code to operate in the same way for the parent
        process when dealing with a channel aware process and a process that will just go through stdio.

    Keyword Arguments:
        These are determined by the driver.  supD will likely need arguments to determine if a new sup must be start
        or the unix domain socket to an existing supD etc.
    """


    ndx = pid_string.find(":")
    if ndx < 0:
        return None

    driver_name = pid_string[:ndx]
    argv = pid_string[ndx + 1:]

    global _pidantic_classes
    PIDClass = _pidantic_classes[driver_name]
    if not PIDClass:
        return None

    pidantic = PIDClass(argv, event_callback, log=log, use_channel=use_channel, channel_is_stdio=channel_is_stdio)

    return pidantic
