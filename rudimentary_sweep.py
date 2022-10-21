import stepperMotorCtrl
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
    name = '20221021_1412_co57'
    #velocities = np.array([-0.4, -0.3, -0.2, -0.159, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4])
    #velocities = np.array([-1.0, 1.0, -1.0, 1.0, -1.0, 1.0])
    velocities = np.array([-0.2])
    scan = stepperMotorCtrl.ScanController(
        mokuWGChannel=2,
        commandSleepTime=1,
        scanTravelDist=40,
        returnVelocity=5
    )

    # Turn on the base high voltage
    scan.moku.setBaseHV(1, 1) # Default to 1kV bias on channel 1

    scan_times = scan.scanTravelDist / np.abs(velocities)
    scan_times[scan_times==np.inf] = scan_times.min()
    print('\nTotal scanning time (s): ', scan_times.sum(), '\n')

    time_s = int(0.9 * scan.scanTravelDist / np.max(np.abs(velocities)))
    print('\n\n\nDAQ time (s): ', time_s, '\n\n')
    for i, vel in enumerate(velocities):
        print(f'initiating scan at {vel} mm/s')
        tScan = scan_times[i]
        print(f'scanning for {tScan} seconds')
        start_time = time.time()
        scan.start_step(vel)
        print('sending DAQ command via ssh')
        # TODO: move to subprocess
        remote_timed_daq(time_s, vel, name)
        while time.time() < (start_time + tScan):
            time.sleep(1)
        scan.stopMotion()
        tReturn = self.scanTravelDist/self.returnVelocity
        scan.step(
            -1 * self.returnVelocity * np.sign(vel),
            self.scanTravelDist, 
            2
        )
    print('scan done')
