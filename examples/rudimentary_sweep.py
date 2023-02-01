import stepperMotorCtrl
from pexpect import pxssh
import time
import numpy as np
import random

def remote_timed_daq(time_s, velocity, name, high_e=False):
    dataserver_daq_script = '/home/joeyh/daq/dpp-pha/dpp-readout/get_count_rate.py'
    line = {True: '122', False: ''}[high_e]
    cmd = f'python {dataserver_daq_script} {time_s} {velocity} {name} {line} >> /home/joeyh/daqlog.log'
    print(cmd)
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
    name = '20221215_1611_alpha'
    high_e = False  # set True for 122 keV config
    iterate = True
    velocities = np.array([-1.0, -0.8, -0.6, -0.5, -0.4, -0.3, -0.2, -0.159, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0])
    velocities = np.empty((30,))
    velval = 3.0
    velocities[::2] = velval
    velocities[1::2] = -1*velval
    velocities = np.array([-0.5, -0.2, -0.1, -0.159, 0.0, 0.1, 0.2])
    #velocities = np.linspace(-5, 5, 101)
    #velocities = np.array([-1.0, -0.8, -0.6, -0.5, -0.4, -0.3, -0.2, -0.159, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0])
    print(velocities)


    scan = stepperMotorCtrl.ScanController(
        mokuWGChannel=2,
        commandSleepTime=0,
        scanTravelDist=40,
        returnVelocity=5,
        logfileName=name+'.log',
    )

    # Turn on the base high voltage
    # TODO: check HV instead of setting it?
    scan.moku.setBaseHV(1, 1) # Default to 1kV bias on channel 1
    scan.resetZeroPosition(currentPosition=60)
    scan_times = scan.scanTravelDist / np.abs(velocities)
    scan_times[scan_times==np.inf] = 100  # fix v=0 case
    daq_times = (scan_times * 0.9).astype(int)
    print('\nTotal scanning time (s): ', scan_times.sum(), '\n')
    print('\nTotal DAQ time (s): ', daq_times.sum(), '\n')
    if iterate:
        iterations_per_velocity = np.asarray(np.round(1.0/(scan_times/scan_times.max())), dtype=int)
    else:
        iterations_per_velocity = np.ones(len(scan_times), dtype=int)
    vel_iter_map = {velocities[i]: iterations_per_velocity[i] for i in range(len(velocities))}
    random.shuffle(velocities)
    scan_times = scan.scanTravelDist / np.abs(velocities)
    scan_times[scan_times==np.inf] = 100  # fix v=0 case
    daq_times = (scan_times * 0.9).astype(int)
    print(velocities)
    print(scan_times)
    full_scan_start = time.time()
    hours_elapsed = 0
    for i, vel in enumerate(velocities):
        for j in range(vel_iter_map[vel]):
            # if we plan to scan a negative velocity,
            # we want to start scan-distance closer to source
            print(f'initiating scan at {vel} mm/s')
            if vel < 0:
                scan.quickReturn(vel)
            tScan = scan_times[i]
            print(f'scanning for {tScan} seconds')
            scan.start_step(vel)
            start_time = time.time()
            print('sending DAQ command via ssh')
            remote_timed_daq(daq_times[i], vel, name, high_e)
            while time.time() < (start_time + tScan):
                time.sleep(0.001)
            scan.stopMotion()
            # if we just scanned a positive velocity,
            # we want to return
            if vel > 0:
                scan.quickReturn(vel)
        if int((time.time() - full_scan_start)/3600) > hours_elapsed:
            scan.resetZeroPosition(currentPosition=60)
            hours_elapsed += 1
            print('RESETTING POSITION, HOURS ELAPSED:', hours_elapsed)
    print('\nSCAN COMPLETE\n')
