import logging
from pidantic.pidbase import PIDanticBase
import xmlrpclib
import supervisor.xmlrpc


class PIDanticSupD(PIDanticBase):

    def __init__(self, argv, auto_restart=False, log=logging, use_channel=False, channel_is_stdio=False, **kwargs):
        PIDanticBase.__init__(self, argv, auto_restart=auto_restart, log=log, use_channel=use_channel, channel_is_stdio=channel_is_stdio)

    def starting(self):
        pass

    def restart_fault(self):
        pass

    def started(self):
        pass

    def start_canceled(self):
        pass

    def start_fault(self):
        pass
    
    def exited(self):
        pass

    def stopping(self):
        pass

    def kill(self):
        pass

    def run_fault(self):
        pass

    def stopped(self):
        pass

    def stopping_fault(self):
        pass

    def get_result_code(self):
        return self._rc

    def send_stdin(self, data):
        pass

    def recv_stdout(self, len=None):
        pass

    def recv_stderr(self, len=None):
        pass

    def send_channel(self, data):
        pass

    def recv_channel(self, len=None):
        pass

    def has_read_channel(self):
        pass

    def has_write_channel(self):
        pass

    def has_stdin(self):
        pass

    def has_stdout(self):
        pass

    def has_stderr(self):
        pass