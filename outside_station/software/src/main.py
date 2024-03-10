"""
A simple script that reads the temperature from a thermistor and publishes it to an MQTT topic.
"""

import network
import time
import math
from umqtt.simple import MQTTClient
import machine
import uota

# Import the config file
import config

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
while wlan.isconnected() == False:
    print('Waiting for connection...')
    time.sleep(1)
print("Connected to WiFi")

# OTA update
print('Starting OTA update')
if uota.check_for_updates():
      uota.install_new_firmware()
      machine.reset()


# Topic where the data will be published to
mqtt_publish_topic_t1 = 'sensors/temperature_int'
mqtt_publish_topic_t2 = 'sensors/temperature_ext'

# Initialize our MQTTClient and connect to the MQTT server
mqtt_client = MQTTClient(
    client_id = config.MQTT_CLIENT_ID,
    server = config.MQTT_BROKER,
    port = config.MQTT_PORT
    )

mqtt_client.connect()

# Initialize the LED
pin = machine.Pin("LED", machine.Pin.OUT)
#initialize onboard temperature sensor
adcpin_int = 4
sensor_int = machine.ADC(adcpin_int)

adcpin_ext = 26
sensor_ext = machine.ADC(adcpin_ext)

# constants (thermistor)
# Voltage Divider
Vin = 3.3
Ro = 10000  # 10k Resistor

# Steinhart Constants
A = 0.001129148
B = 0.000234125
C = 0.0000000876741
fix = 5 # offset

def ReadTemperature_int():
    # Read temperature
    adc_value = sensor_int.read_u16()
    volt = (3.3/65535)*adc_value
    temperature = 27 - (volt - 0.706)/0.001721
    return round(temperature, 1)

def ReadTemperature_ext():
    # Read temperature
    adc_value = sensor_ext.read_u16()
    volt = (3.3/65535)*adc_value

    # Calculate Resistance
    Rt = (volt * Ro) / (Vin - volt)
    # Rt = 10000  # Used for Testing. Setting Rt=10k should give TempC=25

    # Steinhart - Hart Equation
    TempK = 1 / (A + (B * math.log(Rt)) + C * math.pow(math.log(Rt), 3))

    # Convert from Kelvin to Celsius
    TempC = TempK - 273.15 - fix
    return round(TempC, 1)

# Publish a data point to the topic every XX seconds
try:
    while True:
        # Toggle the LED
        # pin.toggle()

        temperature_int = ReadTemperature_int()
        temperature_ext = ReadTemperature_ext()

        # Publish the data to the topic!
        print(f'Publish {temperature_int:.2f}')
        mqtt_client.publish(mqtt_publish_topic_t1, str(temperature_int))

        print(f'Publish {temperature_ext:.2f}')
        mqtt_client.publish(mqtt_publish_topic_t2, str(temperature_ext))

        # Delay a bit to avoid hitting the rate limit
        time.sleep(30)
except Exception as e:
    print(f'Failed to publish message: {e}')
finally:
    mqtt_client.disconnect()
    pin.off()