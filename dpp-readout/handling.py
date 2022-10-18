import sys, os
import subprocess 
import pexpect


cmd = 'dpp-readout unamplified_config'

child = pexpect.spawn(cmd)
child.expect('\r')

print(child.after.decode('ascii'), end='')
