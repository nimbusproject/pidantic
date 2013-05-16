# Copyright 2013 University of Chicago

from pidantic.pidantic_exceptions import PIDanticUsageException
from pidantic.ui import PIDantic, PidanticFactory
import unittest

class BaseUiTest(unittest.TestCase):

    def test_base_ui(self):

        pidant = PIDantic()

        try:
            pidant.is_done()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.poll()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.send_stdin("ssss")
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.get_state()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass

        try:
            pidant.recv_stdout()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.recv_stderr()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass

        try:
            pidant.send_channel("ssss")
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.recv_channel()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.recv_channel()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass


        try:
            pidant.terminate()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass

        try:
            pidant.has_stderr()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.has_stdin()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.has_stdout()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.has_write_channel()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass
        try:
            pidant.has_read_channel()
            self.assertFalse(True, "should have raised an exception")
        except PIDanticUsageException:
            pass


    def test_base_factory(self):
        fact = PidanticFactory()
        fact.get_pidantic()
        fact.stored_instances()

if __name__ == '__main__':
    unittest.main()
