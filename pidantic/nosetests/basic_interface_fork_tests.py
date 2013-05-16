# Copyright 2013 University of Chicago

#import gevent
#from pidantic.fork import ForkPidanticFactory
#from pidantic.pidantic_exceptions import PIDanticStateException
#
#
#import unittest
#
#class BasicForkInterfaceTests(unittest.TestCase):
#
#    def setUp(self):
#        self.factory = ForkPidanticFactory()
#
#    def get_stored_tests(self):
#        l = self.factory.stored_instances()
#        self.assertEqual(0, len(l))
#
#    def test_basic_run(self):
#        pidant = self.factory.get_pidantic(argv="/bin/true")
#        out = pidant.recv_stdout()
#        while not pidant.is_done():
#            gevent.sleep(0.1)
#        rc = pidant.get_result_code()
#        self.assertEqual(rc, 0)
#
#    def test_basic_fail(self):
#        pidant = self.factory.get_pidantic(argv="/bin/false")
#        out = pidant.recv_stdout()
#        while not pidant.is_done():
#            gevent.sleep(0.1)
#        rc = pidant.get_result_code()
#        self.assertNotEqual(rc, 0)
#
#    def test_terminate(self):
#        pidant = self.factory.get_pidantic(argv="/bin/sleep 10")
#        gevent.sleep(0.1)
#        pidant.terminate()
#        while not pidant.is_done():
#            gevent.sleep(0.1)
#        rc = pidant.get_result_code()
#        self.assertNotEqual(rc, 0)
#
#    def test_terminate_after_done(self):
#        pidant = self.factory.get_pidantic(argv="/bin/true")
#        while not pidant.is_done():
#            gevent.sleep(0.1)
#        try:
#            pidant.terminate()
#            self.assertFalse(True, "should have thrown an exception")
#        except PIDanticStateException:
#            pass
#        rc = pidant.get_result_code()
#        self.assertEqual(rc, 0)
#
#
#
#if __name__ == '__main__':
#    unittest.main()
