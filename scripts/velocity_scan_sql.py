# Mysql Connectors, and time
import mysql.connector
import time
from datetime import datetime, timezone
import numpy as np

# Multi-threading for controlling
import threading

# LOCK-IN-AMPLIFIER for fast stage
from mossbauer_control.instruments import SRS860

# Fast Stage Function Generator
from mossbauer_control.instruments import DS360

# Camera Trigger 
from mossbauer_control.instruments import bnc555

# CSV Savings
import csv
import os

# Decimal precision for fixed-point Q12
from decimal import Decimal, getcontext, ROUND_HALF_UP
getcontext().prec = 28
_Q12 = Decimal('0.000000000001')

def _q12(x):
    return Decimal(str(x)).quantize(_Q12, rounding=ROUND_HALF_UP)


class sql_writer:
    def __init__(self,
                 host='192.168.2.2',
                 user='writer',
                 password='mossbauer_writer',
                 database='slowcontrol',
                 table='scan'):
        self.table = table
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            autocommit=True,
            connection_timeout=5
        )
        self.cur = self.conn.cursor()

    def insert_snapshot(self, t_dt_utc,
                        A, A_set, phi, f_ref, f_set):
        try:
            self.conn.ping(reconnect=True, attempts=1, delay=0)
        except Exception:
            self.conn.reconnect(attempts=3, delay=1)
            self.cur = self.conn.cursor()

        # NOTE: SQL COLUMNS DO NOT MATCH VALUES COUNT IN THE ORIGINAL
        sql = (f"INSERT INTO `{self.table}` "
               "(`TIME`,`A`,`A_set`,`phi`,`f_ref`,`f_set`) "
               "VALUES (%s,%s,%s,%s,%s,%s)")
        vals = (
            t_dt_utc,
            _q12(A), _q12(A_set), _q12(phi),
            _q12(f_ref), _q12(f_set)
        )

        try:
            self.cur.execute(sql, vals)
        except Exception as e:
            print(f"[WARN] MySQL insert_snapshot failed: {e}")


class csv_writer:
    pass


class fast_stage:
    def __init__(self):
        self.drive = DS360(gpib_address=8)
        self.srs = SRS860(gpib_address=10)
        self.bnc = bnc555(gpib_address=1)

        self.db = sql_writer(table='sc')

        self.fast_amp = 3.5
        self.fast_freq = 40
        self.nbursts = 5

        self.latest_A = 0
        self.latest_phi = 0
        self.latest_f = 0

    def start_srs_latest(self, poll_interval: float = 0.2):
        stop = threading.Event()

        def run():
            while not stop.is_set():
                t0 = time.time()
                try:
                    (R, theta_ref, f_ref) = self.srs.read_all()
                    self.latest_A = R
                    self.latest_phi = theta_ref
                    self.latest_f = f_ref
                except Exception as e:
                    print(f"[WARN] srs latest read failed: {e}")

                if poll_interval > 0:
                    remain = poll_interval - (time.time() - t0)
                    if remain > 0 and stop.wait(remain):
                        break

        threading.Thread(target=run, daemon=True).start()
        return stop

    def setup(self):
        self.drive.experiment_setup(self.fast_freq)
        self.srs.experiment_setup()
        self.srs_stopper = self.start_srs_latest(0.2)
        self.bnc.experiment_setup(self.fast_freq, self.nbursts)

    def fetch(self, interval=1):
        while True:
            t0 = time.time()
            ts = datetime.now(timezone.utc)
            k = 0.118e-6

            A = getattr(self, 'latest_A', -1)
            A_set = getattr(self, 'fast_amp', -1)
            phi = getattr(self, 'latest_phi', -1)
            f_ref = getattr(self, 'latest_f', -1)
            f_set = getattr(self, 'fast_freq', -1)
            v = A * 2 * np.pi * f_ref * k

            print(f"A={A:.6g}  A_set={A_set}  phi={phi:.6g}  "
                  f"f={f_ref:.6g} (set {f_set})")

            self.db.insert_snapshot(ts, A, A_set, phi, f_ref, f_set)

            remain = interval - (time.time() - t0)
            if remain > 0:
                time.sleep(remain)

    def fetch_once(self):
        i=0
        while i<1:
            ts = datetime.now(timezone.utc)
            k = 0.118e-6

            A     = getattr(self, 'latest_A', -1)
            A_set = getattr(self, 'fast_amp', -1)
            phi   = getattr(self, 'latest_phi', -1)
            f_ref = getattr(self, 'latest_f', -1)
            f_set = getattr(self, 'fast_freq', -1)

            print(f"A={A:.6g}  A_set={A_set}  phi={phi:.6g}  "
            f"f={f_ref:.6g} (set {f_set})")

            self.db.insert_snapshot(ts, A, A_set, phi, f_ref, f_set)
            i+=1

    def set_to_v(self, v):
        k = 20e-6/170 # meter per volts
        f = self.fast_freq

        A = v / (2 * np.pi * f * k)
        offset = A / 2

        self.fast_amp =A

        self.drive.set_sine()
        self.drive.set_frequency(f)
        self.drive.set_amplitude(A)
        self.drive.set_offset(offset)
        self.drive.output_on()

    def velocity_scan(self):
        self.setup()
        time.sleep(5)
        velocities = np.linspace(0.001,0.6, 25)*1e-3
        for velocity in velocities:
            self.set_to_v(velocity)
            for i in range(90):
                self.fetch_once()
                time.sleep(1)

    def run(self):
        self.setup()
        time.sleep(5)
        self.fetch_once()

    def stop(self):
        self.drive.output_off()
        #self.bnc.reset()
        self.bnc.close()
        self.srs_stopper.set()


if __name__ == "__main__":
    sc = fast_stage()
    try:
        sc.velocity_scan()
    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt, stopping...")
    finally:
        sc.stop()
