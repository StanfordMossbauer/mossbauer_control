import stepperMotorCtrl
from pexpect import pxssh
import time
import numpy as np

def remote_timed_daq(time_s, velocity, name):
    dataserver_daq_script = '/home/joeyh/daq/dpp-pha/dpp-readout/get_count_rate.py'
    cmd = f'python {dataserver_daq_script} {time_s} {velocity} {name} >> /home/joeyh/daqlog.log'
    try:
        s = pxssh.pxssh(timeout=time_s*2)
        hostname = 'mossbauer-dataserver.stanford.edu'
        username = 'joeyh'
        s.login(hostname, username)
        s.sendline(cmd)  # run a command
        s.prompt()       # match the prompt
        print(s.before)  # print everything before the prompt
        s.logout()
    except pxssh.ExceptionPxssh as e:
        print("pxssh failed on login.")
        print(e)
    return

if __name__=='__main__':
    name = '20221026_0926'
    velocities = np.array([-1.0, -0.4, -0.3, -0.2, -0.159, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 1.0])

    scan = stepperMotorCtrl.ScanController(
        mokuWGChannel=2,
        commandSleepTime=1,
        scanTravelDist=40,
        returnVelocity=5,
        logfileName=name+'.log',
    )

    # Turn on the base high voltage
    scan.moku.setBaseHV(1, 1) # Default to 1kV bias on channel 1
    scan_times = scan.scanTravelDist / np.abs(velocities)
    scan_times[scan_times==np.inf] = 100  # fix v=0 case
    daq_times = (scan_times * 0.9).astype(int)
    print('\nTotal scanning time (s): ', scan_times.sum(), '\n')
    print('\nTotal DAQ time (s): ', daq_times.sum(), '\n')
    for i, vel in enumerate(velocities):
        # if we plan to scan a negative velocity,
        # we want to start scan-distance closer to source
        print(f'initiating scan at {vel} mm/s')
        if vel < 0:
            scan.quickReturn(vel)
        tScan = scan_times[i]
        print(f'scanning for {tScan} seconds')
        start_time = time.time()
        scan.start_step(vel)
        print('sending DAQ command via ssh')
        remote_timed_daq(daq_times[i], vel, name)
        while time.time() < (start_time + tScan):
            time.sleep(1)
        scan.stopMotion()
        # if we just scanned a negative velocity,
        # we want to return
        if vel > 0:
            scan.quickReturn(vel)
    print('\nSCAN COMPLETE\n')
