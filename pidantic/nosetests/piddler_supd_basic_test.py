import tempfile
from pidantic.pidantic_exceptions import PIDanticStateException
from pidantic.supd.pidsupd import SupDPidanticFactory
import uuid
from pidantic.state_machine import PIDanticState

import unittest

class PIDSupBasicTest(unittest.TestCase):

    def simple_api_walk_through_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 1", process_name="sleep", directory=tempdir)
        pidantic.start()
        state = pidantic.get_state()
        while not pidantic.is_done():
            factory.poll()
        factory.terminate()

    def simple_cleanup_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 1", process_name="sleep", directory=tempdir)
        pidantic.start()
        state = pidantic.get_state()
        while not pidantic.is_done():
            factory.poll()
        pidantic.cleanup()
        factory.terminate()

    def simple_return_code_success_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/true", process_name="true", directory=tempdir)
        pidantic.start()
        while not pidantic.is_done():
            factory.poll()
        rc = pidantic.get_result_code()
        self.assertEqual(rc, 0)
        factory.terminate()

    def simple_return_code_success_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/false", process_name="false", directory=tempdir)
        pidantic.start()
        while not pidantic.is_done():
            factory.poll()
        rc = pidantic.get_result_code()
        self.assertNotEqual(rc, 0)
        factory.terminate()

    def two_processes_one_sup_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        true_pid = factory.get_pidantic(command="/bin/true", process_name="true", directory=tempdir)
        true_pid.start()
        false_pid = factory.get_pidantic(command="/bin/false", process_name="false", directory=tempdir)
        false_pid.start()
        while not false_pid.is_done() or not true_pid.is_done():
            factory.poll()
        rc = false_pid.get_result_code()
        self.assertNotEqual(rc, 0)
        rc = true_pid.get_result_code()
        self.assertEqual(rc, 0)
        factory.terminate()

    def simple_terminate_test(self):

        process_name = str(uuid.uuid4()).split("-")[0]
        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 5000", process_name=process_name, directory=tempdir)
        pidantic.start()
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
        pidantic = factory.get_pidantic(command="/bin/sleep 5000", process_name="longnap", directory=tempdir)
        pidantic.start()
        factory.poll()
        pidantic.terminate()
        try:
            pidantic.terminate()
            self.fail("The terminate call should raise an error")
        except:
            pass
        while not pidantic.is_done():
            factory.poll()
        rc = pidantic.get_result_code()
        self.assertNotEqual(rc, 0)
        factory.terminate()

    def simple_get_state_start_test(self):
        name = "cat" + str(uuid.uuid4()).split("-")[0]
        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/cat", process_name=name, directory=tempdir)
        pidantic.start()
        state = pidantic.get_state()
        self.assertEquals(state, PIDanticState.STATE_STARTING)
        factory.terminate()

    def simple_get_state_exit_test(self):
        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 1", process_name="sleep", directory=tempdir)
        pidantic.start()
        while not pidantic.is_done():
            factory.poll()
        state = pidantic.get_state()
        self.assertEquals(state, PIDanticState.STATE_EXITED)
        factory.terminate()


    def simple_get_cancel_test(self):
        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 1", process_name="sleep", directory=tempdir)
        state = pidantic.get_state()
        self.assertEquals(state, PIDanticState.STATE_PENDING)
        pidantic.cancel_request()


    def imediately_terminate_facorty_with_running_pgm_test(self):

        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/cat", process_name="cat", directory=tempdir)
        pidantic.start()
        factory.terminate()


    def terminate_done_test(self):
        tempdir = tempfile.mkdtemp()
        factory = SupDPidanticFactory(directory=tempdir, name="tester")
        pidantic = factory.get_pidantic(command="/bin/sleep 1", process_name="sleep", directory=tempdir)
        pidantic.start()
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
