# Util functions to access all the sensor results
import time
from subprocess import PIPE, Popen, check_output

import ST7735
from pms5003 import ReadTimeoutError, SerialTimeoutError
from enviroplus import gas

# Read values from BME280 and return as dict
def read_bme280(bme280, ltr559):
    # Compensation factor for temperature
    comp_factor = 2.25
    values = {}
    cpu_temp = get_cpu_temperature()
    raw_temp = bme280.get_temperature()  # float
    comp_temp = raw_temp - ((cpu_temp - raw_temp) / comp_factor)
    values["temperature"] = int(comp_temp)
    values["pressure"] = round(
        int(bme280.get_pressure() * 100), -1
    )  # round to nearest 10
    values["humidity"] = int(bme280.get_humidity())
    data = gas.read_all()
    values["oxidised"] = int(data.oxidising / 1000)
    values["reduced"] = int(data.reducing / 1000)
    values["nh3"] = int(data.nh3 / 1000)
    values["lux"] = int(ltr559.get_lux())
    return values

# Read values PMS5003 and return as dict
def read_pms5003(pms5003):
    values = {}
    try:
        pm_values = pms5003.read()  # int
        values["pm1"] = pm_values.pm_ug_per_m3(1)
        values["pm25"] = pm_values.pm_ug_per_m3(2.5)
        values["pm10"] = pm_values.pm_ug_per_m3(10)
    except ReadTimeoutError:
        pms5003.reset()
        pm_values = pms5003.read()
        values["pm1"] = pm_values.pm_ug_per_m3(1)
        values["pm25"] = pm_values.pm_ug_per_m3(2.5)
        values["pm10"] = pm_values.pm_ug_per_m3(10)
    return values

# Get CPU temperature to use for compensation
def get_cpu_temperature():
    process = Popen(
        ["vcgencmd", "measure_temp"], stdout=PIPE, universal_newlines=True
    )
    output, _error = process.communicate()
    return float(output[output.index("=") + 1 : output.rindex("'")])


# Get Raspberry Pi serial number to use as ID
def get_serial_number():
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line[0:6] == "Serial":
                return line.split(":")[1].strip()


