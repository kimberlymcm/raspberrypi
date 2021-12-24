#!/usr/bin/env python3

import logging
import time
import argparse
import json
from datetime import date, datetime

from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError, SerialTimeoutError

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

from smbus import SMBus

from aws_utils import configureLogging, configMQTTClient, customCallback
from enviro_utils import read_bme280, read_pms5003


# Read in command-line parameters
#python3 aws-iot-device-sdk-python/samples/basicPubSub/basicPubSub.py -e a3tis9f9gjx3kh-ats.iot.us-west-2.amazonaws.com -r root-CA.crt -c enviro.cert.pem -k enviro.private.key

def main(args):
    host = args.host
    rootCAPath = args.rootCAPath
    certificatePath = args.certificatePath
    privateKeyPath = args.privateKeyPath
    clientId = args.clientId
    topic = args.topic

    if not args.certificatePath or not args.privateKeyPath:
        parser.error("Missing credentials for authentication.")
        exit(2)

    port = 8883

    configureLogging()

    # Init AWSIoTMQTTClient
    myAWSIoTMQTTClient = None
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

    configMQTTClient(myAWSIoTMQTTClient)

    # Connect and subscribe to AWS IoT
    myAWSIoTMQTTClient.connect()
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
    time.sleep(2)

    # Sensor objects
    bus = SMBus(1)
    bme280 = BME280(i2c_dev=bus)
    pms5003 = PMS5003()

    # Publish to the same topic in a loop forever
    loopCount = 0
    while True:
        try:
            message = {}
            message = read_bme280(bme280, ltr559)
            pms_values = read_pms5003(pms5003)
            message.update(pms_values)
            message['device_id'] = 'enviro'
            
            now = datetime.utcnow() # get date and time
            current_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')
            message['time'] = current_time
            messageJson = json.dumps(message)
            myAWSIoTMQTTClient.publish(topic, messageJson, 1)
            print('Published topic %s: %s\n' % (topic, messageJson))
            loopCount += 1
            time.sleep(30) # Twice a minute
        except Exception as e:
            print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--endpoint", action="store", dest="host",
                        help="Your AWS IoT custom endpoint",
                        default="a3tis9f9gjx3kh-ats.iot.us-west-2.amazonaws.com")
    parser.add_argument("-r", "--rootCA", action="store", dest="rootCAPath",
                        help="Root CA file path",
                       default="/home/pi/Documents/root-CA.crt")
    parser.add_argument("-c", "--cert", action="store", dest="certificatePath",
                        help="Certificate file path",
                        default="/home/pi/Documents/enviro.cert.pem")
    parser.add_argument("-k", "--key", action="store", dest="privateKeyPath",
                        help="Private key file path",
                        default="/home/pi/Documents/enviro.private.key")
    parser.add_argument("-id", "--clientId", action="store", dest="clientId",
                        help="Targeted client id", default="basicPubSub")
    parser.add_argument("-t", "--topic", action="store", dest="topic",
                        help="Targeted topic", default="sdk/test/Python")

    args = parser.parse_args()
    main(args)
