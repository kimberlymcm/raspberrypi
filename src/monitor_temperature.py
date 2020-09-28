''' Monitor Temperature of the Raspberry Pi.
   My first Raspberry Pi project '''

from time import sleep, strftime, time

import matplotlib.pyplot as plt
from gpiozero import CPUTemperature

cpu = CPUTemperature()
plt.ion()
x = []
y = []

def write_temp(temp):
    with open("/home/pi/Documents/repos/raspberrypi/cpu_temp.csv", "a") as log:
        log.write("{0}, {1}\n".format(strftime("%Y-%m-%d %H:%M:%S"),str(temp)))

def graph(temp):
    y.append(temp)
    x.append(time())
    plt.clf()
    plt.scatter(x, y)
    plt.draw()


while True:
    temp = cpu.temperature
    write_temp(temp)
    graph(temp)
    plt.pause(30)
