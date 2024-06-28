from GetTrajectory import GetTrajectory
from SendVelocities import SendVelocities
import numpy as np
import time
from RPIServer import RPIServer

class OmniController:
    def __init__(self, port = "/dev/ttyACM0"):
        self.sv = SendVelocities(port = port)
        self.dt = 0
        self.vels = []
            
    def split_message(self, message):
        assert isinstance(message, str), "Message must be a string."       
        x, y, o, dt, t_max = message.split(',')
        x = float(x.split(':')[-1])
        y = float(y.split(':')[-1])
        o = float(o.split(':')[-1])
        dt = float(dt.split(':')[-1])
        t_max = float(t_max.split(':')[-1])
        return x, y, o, dt, t_max

    def update_vels(self, vels):
        self.vels = vels

    def update_dt(self, dt):
        self.dt = dt

    def calculate_vels(self, message:str):
        x, y, o, dt, t_max = self.split_message(message)

        # update dt
        self.update_dt(dt)

        # calculate velocities
        qf = [x, y, o]
        gt = GetTrajectory(qf, t_max, dt = self.dt)
        _, velocities_dt = gt.get_trajectory()
        # update velocities
        self.update_vels(velocities_dt)

    def send_dt(self):
        assert self.dt > 0, "dt must be greater than 0."
        self.sv.send_dt(self.dt)

    def send_velocities(self):
        assert len(self.vels) > 0, "Velocities must be calculated first."
        self.sv.send_velocities(self.vels)

    def send_data(self, data:str):
        if data == "DATA":
            print('Sending velocities to RpiPico')
            self.wait_request("DATA")
            self.send_velocities()
            self.wait_confirmation("OK2")

        elif data == "DT":
            print('Sending dt to RpiPico')
            self.wait_request("DT")
            self.send_dt()
            self.wait_confirmation("OK1")

    def wait_request(self, request_msg:str):
        data = ""
        while request_msg not in data:
            data = self.sv.read()
            time.sleep(0.1)
        return data

    def wait_confirmation(self, confirmation_msg:str):
        data = ""
        while confirmation_msg not in data:
            data = self.sv.read()
            time.sleep(0.1)
        return data

def main():
    server = RPIServer('0.0.0.0', 12345)
    robot = OmniController()
    track_dt = False
    while True:

        if server.client_conn is None:
            print("No client connected. Attempting to accept a new connection...")
            server.accept_connection()
        else:
            
            message = server.receive_message()
            if message:
                print("Received from PC:", message)
                server.send_confirmation()

                robot.calculate_vels(message)
                
                print('-Communication with RpiPico-')
                
                robot.send_data("DT")
                robot.send_data("DATA")
               
                print('-END Communication with RpiPico-')
                server.send_confirmation()
                
        time.sleep(10)
        print("Waiting for next message...")
    robot.sv.close()
    server.close_connection()
    print("Done")

def main_local():
    robot = OmniController(port = "COM6")
    message = "x:0.1,y:0.0,o:0.0,dt:0.1,t_max:1.0"
    robot.calculate_vels(message)
    robot.send_data("DT")
    robot.send_data("DATA")
    print("Done")

try:
    main()
except Exception as e:
    main_local()
finally:
    print("Keyboard Interrupt")
    robot.sv.close()
    server.close_connection()
    print("Done")