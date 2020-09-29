import sys
sys.path.insert(0, "~/thunderborg")
import time

import visionmodule as vim
import controller as ctrl
import planner as plnr
from shared_resource import SharedResource
import user_measurements as usr_msr
import threading


class Robot(threading.Thread):
    def __init__(self, simulate=False, verbose_level=-1, vrb=None, threaded=False):
        """ Class for the entire robot, i.e. camera and Thunderborg

            Init params:
                simulate (bool): Use simulated images
                verbose_level (int): Level for printing information
                vrb (dict): Verbose levels for subsystems as kwargs

            If simulation is set True, the class uses dummy images as
            input when getting the next line points and does not set
            any controls, only saves the state. Otherwise, the
            class uses the picamera stream and controls the robot via
            Thunderborg.

            NOTE: We must implement the class as a thread to allow fast UI

        """
        # NOTE: Python doesn't like dicts in optional args:
        vrb = {} if vrb is None else vrb
        self.verblvl = verbose_level
        self.simulate = simulate
        self.sim_idx = None
        self.running = False
        # ------------------------- SHARED RESOURCES ------------------------
        self.shared_points = SharedResource(None) # Set of points
        self.shared_motor_powers = SharedResource([0.0, 0.0])  # power_L, power_R
        # self.shared_offsets = SharedResource([0.0, 0.0, False])  # offset1, offset2, line_found
        # ---------------------------- SUBSYSTEMS ---------------------------
        self.controller = ctrl.Controller(
            # shared_offsets=self.shared_offsets,
            shared_points=self.shared_points,
            shared_mtr_pwrs=self.shared_motor_powers,
            verbose_level=vrb.get('ctrl', -1)
        )

        # Measurements:
        self.measurements = usr_msr.MEASUREMENTS

        #self.planner = plnr.Planner(
        #    shared_points=self.shared_points,
        #    shared_offsets=self.shared_offsets,
        #    verbose_level=vrb.get('plnr', -1)
        #)

        # Initiate camera and Thunderborg if we are not simulating:
        if not simulate:
            import cameramodule as cm
            self.cam = cm.CameraModule(
                shared_points=self.shared_points,
                verbose_level=vrb.get('cam', -1)
            )
            self.vim = self.cam.stream.vision
            self._init_thunderborg()
        else:
            self.vim = vim.VisionModule()
        # HACK: Set the visionmodule verbose:
        self.vim.verblvl = vrb.get('vis', -1)
        self.threaded = threaded
        if threaded:
            super(Robot, self).__init__()
            self.terminated = threading.Event()
            self.daemon =True  # Assure kill with ctrl+c

    def set_verbose_levels(self, vrb):
        self.vim.verblvl = vrb.get('vis', self.vim.verblvl)
        self.cam.verblvl = vrb.get('cam', self.cam.verblvl)
        self.controller.verblvl = vrb.get('ctrl', self.controller.verblvl)
        #self.planner.verblvl = vrb.get('plnr', self.planner.verblvl)

    def run(self):
        """ Run the robot.

            Loop imaging, control and measurements until stopped
        """
        self.running = True
        if self.threaded:
            self.terminated.clear()
        if self.measurements is not None:
            self.measurements.start_measuring()
        print("[ROBOT] starting to run. Simulating:", self.simulate)
        try:
            while self.running:
                if self.threaded and self.terminated.is_set():
                    self.running = False
                    if self.verblvl > 3: print("[ROBOT] Breaking")
                    break
                if self.simulate:
                    # -------------------------- VISION -------------------------
                    # NOTE: simulation does not use threaded submodules
                    # Find points from dummy images using visionmodule:
                    points = self.vim.get_dummy_line_points(img_idx=self.sim_idx)
                    # --------------------------- PLAN --------------------------
                    # Find offsets using planner:
                    # line_found = True if points is not None else False
                    #os1, os2 = self.planner.get_offsets(points, line_found)
                    # -------------------------- CONTROL ------------------------
                    # Get the motor powers using controller:
                    self.controller.controllerLoop(points)  #, line_found)
                    # NOTE: consider returning these in Controller.controllerLoop
                    pwr1, pwr2 =  self.controller.mtr_pwrs
                    # Delay in simulation:
                    time.sleep(1)
                    if self.verblvl > 3: print("[SIMULATION]: next step")
                else:
                    # In real situation, subsystems run separately
                    # We just use the most recent values:
                    pwr1, pwr2 = self.shared_motor_powers.use_resource()
                self.set_motor_powers(pwr1, pwr2)

                # ------------------------ MEASUREMENTS -------------------------
                # TODO: implement measurements

                # ----------------------- STATUS PRINTS -------------------------
                if self.verblvl > 0: print(self._status_string())
                #if self.verblvl > 2: print("[ROB] OS1", offset1, "OS2", offset2)
                #if verbose_main > 3: print("[MAIN] Setpoint", segment[0])
        except KeyboardInterrupt:
            # CTRL+C exit, disable all drives
            print("\n[ROB] User shutdown")
            self.deactivate()
        except Exception as err:
            print("\n[ROB] Unexpected error, shutting down!")
            print("[PYTHONERR]:")
            self.deactivate()
            raise err

        # FInish the run:
        self.stop()
        # TODO: only stops the robot, does not halt the threads!
        if self.verblvl > 0: print("[ROB] Finished running")

    def deactivate(self):
        """ Stop the Thunderborg controls, destroy resources """
        self.running = False
        if self.threaded:
            self.terminated.set()
        self.shared_points.delete_resource()
        #self.shared_points.release()
        # self.shared_offsets.delete_resource()
        #self.shared_offsets.release()
        self.shared_motor_powers.delete_resource()
        #self.shared_motor_powers.release()
        # self.planner.close()
        self.controller.close()
        if self.measurements is not None:
            self.measurements.destroy_measurements()
        if self.simulate:
            print("[ROBOT] Deactivated simulated")
            return
        self.TB.MotorsOff()
        self.TB.SetLedShowBattery(False)
        self.TB.SetLeds(0, 0, 0)
        self.cam.close()

    def stop(self):
        """ Quick stop of the motors """
        self.running = False
        if self.threaded:
            self.terminated.set()
        if self.measurements is not None:
            self.measurements.stop_measuring()
        if self.simulate:
            return
        self.TB.SetMotor1(0.0)  # right motors
        self.TB.SetMotor2(0.0)  # left motors

    def close(self):
        self.terminated.set()
        self.running = False
        self.join()

    def set_motor_powers(self, pw1, pw2):
        """ Set the motor speeds of the Thunderborg

            params:
                pw1 (float): power for motor 1 (left) [-1,1]
                pw2 (float): power for motor 2 (right) [-1,1]

            return (None):
                Nothing
        """
        if self.simulate:
            return
        self.TB.SetMotor1(pw1)  # right motors
        self.TB.SetMotor2(pw2)  # left motors

    def get_line_points(self, dummy=False, dummy_idx=None):
        """ Take latest image, process it and return as points array

            params:
                dummy (bool): Use dummy images
                dummy_idx (int): Index for a specific dummy image

            return (numpy.array):
                Array of points, processed from the obtained image
        """

        if dummy:
            return self.vim.get_dummy_line_points(dummy_idx)
        else:
            return self.cam.stream.points

    def get_status(self):
        """ Get the current status of Thunderborg board

            params:
                -
            Return (tuple):
                A tuple of three, containing the power of first motor,
                power of second motor, and the battery voltage.

        """
        if self.simulate:
            return (*self.controller.mtr_pwrs, -1)
        if self.verblvl > 3: print("[CONTROLLER] status:")
        if self.verblvl > 3: print("    left:", self.TB.GetMotor1())
        if self.verblvl > 3: print("   right:", self.TB.GetMotor2())
        if self.verblvl > 3: print("    Volt:", self.TB.GetBatteryReading())
        return (
            self.TB.GetMotor1(),
            self.TB.GetMotor2(),
            self.TB.GetBatteryReading()
        )

    def get_battery_level(self):

        """ Return voltage from ThunderBorg
        """
        if self.simulate:
            return -1
        else:
            return self.TB.GetBatteryReading()

    def _init_thunderborg(self):
        import ThunderBorg3 as ThunderBorg
        # Init the Thunderborg connection:
        self.TB = ThunderBorg.ThunderBorg()
        self.TB.Init()
        self.TB.MotorsOff()
        self.TB.SetLedShowBattery(True)

        # Setup the ThunderBorg
        if not self.TB.foundChip:
            boards = ThunderBorg.ScanForThunderBorg()
            if len(boards) == 0:
                print(
                    "[CONTROLLER] No ThunderBorg found,"
                    " check you are attached :)")
            else:
                print(
                    "[CONTROLLER] No ThunderBorg at address"
                    " %02X, but we did find boards:" % (self.TB.i2cAddress)
                )
                for board in boards:
                    print("    %02X (%d)" % (board, board))
                print(
                    "[CONTROLLER] If you need to change the I�C address"
                    " change the setup line so it is correct, e.g."
                )
                print("[CONTROLLER] TB.i2cAddress = 0x%02X" % (boards[0]))

    def _status_string(self):
        """ Form a string representation of robot status

            Used for debugging and cmd interface
            Prints status on the current direction, motor powers and
            controller state.
        """
        if self.simulate:
            dir_raw = self.vim.direction
        else:
            dir_raw = self.cam.get_processed_direction()
        dir_str = '{:+.3f}'.format(float(dir_raw)) if dir_raw is not None else '------'
        mtr1, mtr2, _ = self.get_status()
        state = self.controller.get_status()
        # Form the status string:
        s_str = "[STATUS] DIR: {} | ".format(dir_str)
        s_str += "STEER: {:+.3f} | ".format(self.controller.steering) # dir_str)
        s_str += "MTR_L: {:+.3f}, MTR_R {:+.3f}, | ".format(mtr1, mtr2)
        s_str += "STATE: {}".format(state)
        return s_str
