import tempfile
from pidantic.pidantic_exceptions import PIDanticStateException
from pidantic.supd.pidsupd import SupDPidanticFactory

__author__ = 'bresnaha'

import unittest

class PIDSupBasicTest(unittest.TestCase):

    def simple_api_walk_through_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 1", process_name="sleep", directory=tempdir)
        state = pidantic.get_state()
        while not pidantic.is_done():
            factory.poll()
        factory.terminate()

    def simple_cleanup_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 1", process_name="sleep", directory=tempdir)
        state = pidantic.get_state()
        while not pidantic.is_done():
            factory.poll()
        pidantic.cleanup()
        factory.terminate()

    def simple_return_code_success_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/true", process_name="true", directory=tempdir)
        while not pidantic.is_done():
            factory.poll()
        rc = pidantic.get_result_code()
        self.assertEqual(rc, 0)
        factory.terminate()

    def simple_return_code_success_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/false", process_name="false", directory=tempdir)
        while not pidantic.is_done():
            factory.poll()
        rc = pidantic.get_result_code()
        self.assertNotEqual(rc, 0)
        factory.terminate()

    def two_processes_one_sup_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        true_pid = factory.get_pidantic(command="/bin/true", process_name="true", directory=tempdir)
        false_pid = factory.get_pidantic(command="/bin/false", process_name="false", directory=tempdir)
        while not false_pid.is_done() or not true_pid.is_done():
            factory.poll()
        rc = false_pid.get_result_code()
        self.assertNotEqual(rc, 0)
        rc = true_pid.get_result_code()
        self.assertEqual(rc, 0)
        factory.terminate()

    def simple_terminate_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/cat", process_name="cat", directory=tempdir)
        factory.poll()
        pidantic.terminate()
        while not pidantic.is_done():
            factory.poll()
        rc = pidantic.get_result_code()
        self.assertNotEqual(rc, 0)
        factory.terminate()

    def simple_double_terminate_kill_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/cat", process_name="cat", directory=tempdir)
        factory.poll()
        pidantic.terminate()
        pidantic.terminate()
        while not pidantic.is_done():
            factory.poll()
        rc = pidantic.get_result_code()
        self.assertNotEqual(rc, 0)
        factory.terminate()

    def simple_get_state_start_test(self):
        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/cat", process_name="cat", directory=tempdir)
        state = pidantic.get_state()
        self.assertEquals(state, "STATE_STARTING")
        factory.terminate()

    def simple_get_state_exit_test(self):
        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 1", process_name="sleep", directory=tempdir)
        while not pidantic.is_done():
            factory.poll()
        state = pidantic.get_state()
        self.assertEquals(state, "STATE_EXITED")
        factory.terminate()


    def imediately_terminate_facorty_with_running_pgm_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/cat", process_name="cat", directory=tempdir)
        factory.terminate()


    def terminate_done_test(self):
        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 1", process_name="sleep", directory=tempdir)
        while not pidantic.is_done():
            factory.poll()
        try:
            pidantic.terminate()
            self.assertFalse(True, "should not get here")
        except PIDanticStateException:
            pass
        factory.terminate()

        
if __name__ == '__main__':
    unittest.main()
