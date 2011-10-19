import tempfile
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


        
if __name__ == '__main__':
    unittest.main()
