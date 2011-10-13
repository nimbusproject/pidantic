import socket
import subprocess
import fcntl
import os

p = subprocess.Popen("/bin/cat", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

fdin = p.stdin.fileno()
fl = fcntl.fcntl(fdin, fcntl.F_GETFL)
fcntl.fcntl(fdin, fcntl.F_SETFL, fl | os.O_NONBLOCK)

fdout = p.stdout.fileno()
fl = fcntl.fcntl(fdout, fcntl.F_GETFL)
fcntl.fcntl(fdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)


rc = p.poll()
while rc is None:
    try:
        x = os.write(fdin, "hi")
  #      y = os.read(fdout, 1024)
        #print x
        
        #x = sock.recv(1024)

    except Exception, ex:
        pass
    rc = p.poll()
