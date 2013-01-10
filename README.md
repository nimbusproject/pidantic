PIDantic
========

This library is an abstraction for communicating with child processes.
The processes can run via supervisord or within an ION 
container.  This code should provide a seamless interface to both
allowing the user to start/stop/monitor processes without the concern
of how the processes were run.

The specifics of communicating with the different types of processes
is handled in PIDantic drivers.  The drivers may implement any blocking
IO with gevent.

Using PIDantic
--------------

To use PIDantic, you must create a PIDantic factory, and then you can 
use this factory to start processes.

### SupervisorD

An example of how to start an interact with a process:

    from pidantic.supd.pidsupd import SupDPidanticFactory


    # Create our factory
    persistence_directory = "/tmp"
    persistence_name = "pidantic_test"

    factory = SupDPidanticFactory(directory=persistence_directory, 
            name=persistence_name)


    # Start a process
    cmd = "sleep 100"
    name = "sleeper"
    dir = persistence_directory

    pid = self.factory.get_pidantic(command=cmd, process_name=name,
            directory=dir)
    pid.start()

    
    # Check process status
    processes = factory.reload_instances()
    factory.poll()

    # Print status of each process
    for name, process in processes.iteritems():
        print "Process %s has status %s" % (name, process.get_status())


    # Terminate all processes
    for name, process in processes.iteritems():
        process.cleanup()

    
    # Shut down the factory
    factory.terminate()
