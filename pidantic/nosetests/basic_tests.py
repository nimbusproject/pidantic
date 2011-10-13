import uuid
from pidantic import get_pidantic
import unittest
from pidantic.pidfork import PIDanticFork

class BasicTestFork(unittest.TestCase):

    def test_simple_true(self):
        pidant = PIDanticFork("/bin/true")
        pidant.start()
        while not pidant.is_done():
            pidant.poll()
        state = pidant.get_state()
        self.assertEqual(state, "STATE_EXITED")
        rc = pidant.get_result_code()
        self.assertEqual(rc, 0)

    def test_simple_false(self):
        pidant = PIDanticFork("/bin/false")
        pidant.start()
        while not pidant.is_done():
            pidant.poll()
        rc = pidant.get_result_code()
        self.assertNotEqual(rc, 0)

    def test_terminate(self):
        pidant = PIDanticFork("/bin/sleep 100")
        pidant.start()
        pidant.terminate()
        while not pidant.is_done():
            pidant.poll()
        rc = pidant.get_result_code()
        self.assertNotEqual(rc, 0)

    def test_restart(self):
        pidant = PIDanticFork("/bin/sleep 1")
        pidant.start()
        pidant.poll()
        pidant.restart()
        while not pidant.is_done():
            pidant.poll()
        rc = pidant.get_result_code()
        self.assertEqual(rc, 0)

    def test_larger_stdout(self):
        pidant = PIDanticFork("/bin/cat /etc/group")
        pidant.start()
        data = ""
        while not pidant.is_done():
            pidant.poll()
            d = pidant.recv_stdout(len=5)
            if d:
                data = data + d
        # read to eof:
        d = pidant.recv_stderr()
        if d:
            data = data + d
        print data
        rc = pidant.get_result_code()
        self.assertEqual(rc, 0)


    def test_basic_stdout(self):
        message = str(uuid.uuid4()) + "Helloeworld"
        pidant = PIDanticFork("/bin/echo %s" % (message))
        pidant.start()
        data = ""
        while not pidant.is_done():
            pidant.poll()
            d = pidant.recv_stdout(len=5)
            if d:
                data = data + d
        # read to eof:
        d = pidant.recv_stdout()
        if d:
            data = data + d

        self.assertEqual(message, data.strip())
        rc = pidant.get_result_code()
        self.assertEqual(rc, 0)

    def test_basic_stderr(self):
        message = str(uuid.uuid4()) + "Hello stderr"
        pidant = PIDanticFork("/bin/echo %s >&2" % (message))
        pidant.start()
        data = ""
        while not pidant.is_done():
            pidant.poll()
            d = pidant.recv_stderr(len=5)
            if d:
                data = data + d

        # read to eof:
        d = pidant.recv_stderr(len=None)
        if d:
            data = data + d

        self.assertEqual(message, data.strip())
        rc = pidant.get_result_code()
        self.assertEqual(rc, 0)

    def test_basic_stdin_terminate(self):
        message = str(uuid.uuid4()) + "Hello stderr"
        pidant = PIDanticFork("/bin/cat")
        pidant.start()
        pidant.send_stdin(message)
        pidant.poll()
        pidant.terminate()                

    def test_terminate_kill(self):
        pidant = PIDanticFork("/bin/cat")
        pidant.start()
        pidant.poll()
        pidant.terminate()
        pidant.terminate()


if __name__ == '__main__':
    unittest.main()
