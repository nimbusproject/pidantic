PIDantic
========

This library is an abstraction for communicating with child processes.
The processes can be forked, run via supervisord, or within an ION 
container.  This code should provide a seamless interface to all three
allowing the user to start/stop/monitor processes without the concern
of how the processese were run.

The specifics of communicating with the different types of processes
is handled in PIDantic drivers.  The drivers may implement any blocking
IO with gevent.
