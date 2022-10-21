from stepperMotorCtrl_moku import *
from pexpect import pxssh
import time

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
    name = '20221020_1548_co57'
    velocities = np.array([-0.4, -0.3, -0.2, -0.159, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4])
    velocities = np.array([-1.0, 1.0, -1.0, 1.0, -1.0, 1.0])

    moku = mokuGO('192.168.73.1')
    # Turn on the base high voltage
    moku.BaseHVon(1, 1) # Default to 1kV bias on channel 1

    scan_times = D_TRAVEL / np.abs(velocities)
    scan_times[scan_times==np.inf] = scan_times.min()
    print('\nTotal scanning time (s): ', scan_times.sum(), '\n')

    ctrl = DFR1507A()
    ctrl.AWoff()
    ctrl.setDirection('CCW')
    ctrl.setResolution(1)
    time_s = int(0.9 * D_TRAVEL / np.max(np.abs(velocities)))
    print('\n\n\nDAQ time (s): ', time_s, '\n\n')
    for i, vel in enumerate(velocities):
        print(f'initiating scan at {vel} mm/s')
        if vel<0:
            returnVel = V_RETURN
        else:
            returnVel = -V_RETURN
        #tScan = D_TRAVEL/np.abs(vel) # seconds to scan
        tScan = scan_times[i]
        print(f'scanning for {tScan} seconds')
        tReturn = D_TRAVEL/V_RETURN
        if vel==0:
            tReturn = 0
        ctrl.setVelocity(vel)
        # funcGen.setFreq(ctrl.fStep)
        moku.PWMon(ctrl.fStep, 2) # Defaults to use channel 2
        start_time = time.time()
        ctrl.AWon()
        time.sleep(1)
        print('sending DAQ command via ssh')
        # TODO: move to subprocess
        remote_timed_daq(time_s, vel, name)
        while time.time() < (start_time + tScan):
            time.sleep(1)
        ctrl.AWoff()
        moku.PWMoff(2)
        if tReturn:
            # And then go back to where we started.
            ctrl.setResolution(2)
            ctrl.setVelocity(returnVel)
            moku.PWMon(ctrl.fStep,2)
            ctrl.AWon()
            time.sleep(1)
            time.sleep(tReturn)
            ctrl.AWoff()
            moku.PWMoff()
            time.sleep(1)
            ctrl.setResolution(1) # Reset to the fine scan...
    print('scan done')
