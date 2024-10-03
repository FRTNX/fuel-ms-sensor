# from pymodbus.client import ModbusTcpClient

# client = ModbusTcpClient('device.lan')
# client.connect()
# client.write_coil(1, True)
# result = client.read_coils(1, 1)
# print(result.bits(0))
# client.close()
import requests
import time
import threading
import random

from typing import List
from typing_extensions import TypedDict

import time
import fastapi

from fastapi import Request

from starlette.middleware.cors import CORSMiddleware


app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

ACTIVE_SIMULATIONS = False;

class Vehicle(TypedDict):
    sensorId: str
    capacity: int
    fuel: float

class Sensor:
    """"""
    def __init__(self, sensor_id, capacity=50, fuel=random.randint(30, 50)):
        self._sensor_id = sensor_id
        self._capacity = capacity
        self._fuel = fuel
        self._fuel_percentage = fuel / capacity
        self._update_value = 0.02
        self._threshold = 0.6
        self._refill_target = 0.7
        self._directive = 'burn'
        
    def send_readings(self):
        self._update()
        self._print('directive: ', self._directive)
        data = { 'fuel': self._fuel, 'sensorId': self._sensor_id }
        try:
            requests.post('https://fuel-ms-server.onrender.com/api/v0/sensor', json=data)
            requests.get('https://fuel-ms-server.onrender.com/api/v0/vehicle/consumption')
            # requests.post('http://localhost:2222/api/v0/sensor', json=data)
            # requests.get('http://localhost:2222/api/v0/vehicle/consumption')
        except Exception as e:
            print(e)
        
    def _update(self):
        self._print('fuel percentage:', self._fuel_percentage)
        self._print('fuel:', self._fuel)
        self._print('capacity:', self._capacity)
        if self._directive == 'burn':
            val = random.randint(1, 100)
            random_anomaly = True if val < 10 else False
            if random_anomaly:
                print('>>>>>>>ANOMALY<<<<<<<<')
                change_in_fuel = self._capacity * random.randint(20, 30) * 0.01
            else:
                change_in_fuel = random.randint(int(self._capacity * 0.005), int(self._capacity * 0.04))
        else:
            change_in_fuel = int(self._capacity * 0.18)
        
        if self._directive == 'refill':
            target_fill = self._capacity * self._refill_target
            self._print('target fill:', target_fill)
            self._print('change in fuel:', change_in_fuel)
            if self._fuel < target_fill:
                self._print('adding more fuel')
                self._fuel += change_in_fuel
            else:
                self._directive = 'burn'
                self._fuel -= random.randint(int(self._capacity * 0.001), int(self._capacity * 0.02))
        else:          
            if self._fuel_percentage > 0.55:
                self._fuel -= change_in_fuel 
            else:
                value = random.randint(1, 100)
                if value < 40 or self._fuel_percentage < 0.1:
                    self._directive = 'refill'
                    self._fuel += change_in_fuel
                else:
                    self._fuel -= change_in_fuel
        self._fuel_percentage = self._fuel / self._capacity
                    
    def _print(self, *text):
        print(self._sensor_id, ':', text)


def simulate_sensors(sensors):
    global ACTIVE_SIMULATIONS
    for i in range(100):
        for sensor in sensors:
            sensor.send_readings()
        time.sleep(2)
    
    time.sleep(15)
    ACTIVE_SIMULATIONS = False


@app.put('/sensors')
async def init_sensors(request: Request):
    """"""
    global ACTIVE_SIMULATIONS
    data = await request.json()
    try:
        if ACTIVE_SIMULATIONS:
            print('simulators active. skipping initialisation')
            return { 'result': 'SUCCESS' }
        print('got vehicles:', data)
        ACTIVE_SIMULATIONS = True
        sensors = []
        for vehicle in data:
            sensor = Sensor(vehicle['sensorId'], vehicle['capacity'], vehicle['fuel'])
            sensors.append(sensor)
        
        print('working with sensors:', sensors)
        simulate_sensors(sensors)
       
        return { 'result': 'SUCCESS' }
    except Exception as e:
        print(e)
        return { 'error': str(e) }

    