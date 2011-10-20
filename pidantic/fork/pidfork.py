import logging
import subprocess
import fcntl
from gevent import Greenlet
import gevent
import os
from pidantic.pidbase import PIDanticStateMachineBase

def _make_nonblocking(filelike):
    fd = filelike.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)


def _poller(pidfork):

    while not pidfork.is_done():
        pidfork.poll()
        gevent.sleep(1)

def read_nonblocking(fd, size):
    try:
        data = os.read(fd, size)
    except OSError, osex:
        if osex.errno != 11:
            raise
        data = None
    return data

def read_green(filelike, length):
    fd = filelike.fileno()
    buffer_size = 1024 * 4
    done = False
    data = ''
    while not done:
        if length != None and buffer_size > length:
            buffer_size = length
        d = read_nonblocking(fd, buffer_size)
        if d is None:
            gevent.sleep(1)
            continue

        if d == '':
            done = True
        else:
            if length is not None:
                length -= len(d)
                if length == 0:
                    done = True
            data = data + d
            
    return data


def read_bocking(filelike, length):
    g = Greenlet(read_green, filelike, length)
    g.start()
    g.join()
    if g.exception:
        raise g.exception
    return g.value


def write_nonblocking(fd, data):
    try:
        rc = os.write(fd, data)
    except IOError, osex:
        if osex.errno != 11:
            raise
        rc = 0
    return rc


def write_green(filelike, data):

    fd = filelike.fileno()

    remaining = len(data)
    done = False
    # give it a go first without an index
    length = write_nonblocking(fd, data)
    remaining = remaining - length
    while remaining > 0:
        data = data[length:]
        length = write_nonblocking(fd, data)
        remaining = remaining - length


def write_blocking(filelike, data):
    g = Greenlet(write_green, filelike, data)
    g.start()
    g.join()
    if g.exception:
        raise g.exception
    return g.value


class PIDanticFork(PIDanticStateMachineBase):

    WRITE_PIPE_ENV = "PIDANTIC_WRITE_PIPE_FD"
    READ_PIPE_ENV = "PIDANTIC_READ_PIPE_FD"

    def __init__(self, event_callback=None, log=logging, use_channel=False, channel_is_stdio=False, **kwargs):
        PIDanticStateMachineBase.__init__(self, event_callback=event_callback, log=log, use_channel=use_channel, channel_is_stdio=channel_is_stdio, **kwargs)
        self._argv = kwargs['argv']

    def starting(self):
        self._p = None
        self._rc = None
        self._stdin = None
        self._stdout = None
        self._stderr = None
        self._read_channel = None
        self._write_channel = None
        self._greenlet = None

        try:
            self._start()
            event = "EVENT_RUNNING"
            self._send_event(event)
        except Exception, ex:
            # log it
            event = "EVENT_FAULT"
            raise

    def restart_fault(self):
        pass

    def started(self):
        # not much to do here
        self._log.log(logging.INFO, "Successfully started")

    def start_canceled(self):
        if self._p:
            self._p.terminate()

    def start_fault(self):
        self._log.log(logging.INFO, "An error occured while starting")

    def exited(self):
        self._log.log(logging.INFO, "The program successfully ended")
        self._greenlet.join()

    def stopping(self):
        self._p.terminate()

    def kill(self):
        self._p.kill()

    def run_fault(self):
        self._log.log(logging.INFO, "An error occured while running")

    def stopped(self):
        self._log.log(logging.INFO, "The program successfully stopped")

    def stopping_fault(self):
        self._log.log(logging.INFO, "An error occured while stopping")

    def _start(self):
        child_env = os.environ.copy()

        if self._use_channel and not self._channel_is_stdio:
            (parent_read_pipe, child_write_pipe) = os.pipe()
            (child_read_pipe, parent_write_pipe) = os.pipe()
            child_env[self.WRITE_PIPE_ENV] = child_write_pipe
            child_env[self.READ_PIPE_ENV] = child_read_pipe
            self._log.log(logging.INFO, "Using a channel pipe.  FDs %d %d" % (child_write_pipe, child_read_pipe))

            self._write_channel = os.fdopen(parent_read_pipe)
            self._read_channel = os.fdopen(parent_write_pipe)

            _make_nonblocking(self._write_channel)
            _make_nonblocking(self._read_channel)

        self._log.log(logging.INFO, "starting the command %s." % str(self._argv))
        self._p = subprocess.Popen(self._argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=False, shell=True, cwd=None, env=child_env)
        self._stdin = self._p.stdin
        self._stdout = self._p.stdout
        self._stderr = self._p.stderr

        _make_nonblocking(self._stdin)
        _make_nonblocking(self._stdout)
        _make_nonblocking(self._stderr)

        if self._channel_is_stdio:
            self._write_channel = self._stdout
            self._read_channel = self._stdin

        self._greenlet = Greenlet(_poller, self)
        self._greenlet.start()


    def poll(self):
        if not self._p:
            return False

        rc = self._p.poll()
        if rc is None:
            return
        self._rc = rc
        event = "EVENT_EXITED"
        self._send_event(event)

        return True


    def get_result_code(self):
        return self._rc


    def send_stdin(self, data):
        if not self.has_stdin():
            return None
        return write_blocking(self._stdin, data)

    def recv_stdout(self, len=None):
        if not self.has_stdout():
            return None
        return read_bocking(self._stdout, len)

    def recv_stderr(self, len=None):
        if not self.has_stderr():
            return None
        return read_bocking(self._stderr, len)

    def send_channel(self, data):
        if not self.has_read_channel():
            return None
        return write_blocking(self._read_channel, data)

    def recv_channel(self, len=None):
        if not self.has_write_channel():
            return None
        return read_bocking(self._write_channel, len)

    def has_read_channel(self):
        return self._read_channel is not None

    def has_write_channel(self):
        return self._write_channel is not None

    def has_stdin(self):
        return self._stdin is not None

    def has_stdout(self):
        return self._stdout is not None

    def has_stderr(self):
        return self._stderr is not None