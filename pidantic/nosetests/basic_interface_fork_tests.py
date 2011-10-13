import gevent
from pidantic.pidbase import pidantic_factory


__author__ = 'bresnaha'

import unittest

class BasicForkInterfaceTests(unittest.TestCase):
    def test_basic_run(self):
        pidant = pidantic_factory("fork", "/bin/true")
        pidant.start()
        out = pidant.recv_stdout()
        while not pidant.is_done():
            gevent.sleep(0.1)
        rc = pidant.get_result_code()
        self.assertEqual(rc, 0)

    def test_basic_fail(self):
        pidant = pidantic_factory("fork", "/bin/false")
        pidant.start()
        out = pidant.recv_stdout()
        while not pidant.is_done():
            gevent.sleep(0.1)
        rc = pidant.get_result_code()
        self.assertNotEqual(rc, 0)

    def test_terminate(self):
        pidant = pidantic_factory("fork", "/bin/sleep 10")
        pidant.start()
        gevent.sleep(0.1)
        pidant.terminate()
        while not pidant.is_done():
            gevent.sleep(0.1)
        rc = pidant.get_result_code()
        self.assertNotEqual(rc, 0)

    def test_terminate_after_done(self):
        pidant = pidantic_factory("fork", "/bin/true")
        pidant.start()
        while not pidant.is_done():
            gevent.sleep(0.1)
        pidant.terminate()
        rc = pidant.get_result_code()
        self.assertNotEqual(rc, 0)



if __name__ == '__main__':
    unittest.main()
