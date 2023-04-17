#!/bin/bash

import requests
import pandas as pd
import time
import signal
import sys
import json
import urllib3
import adafruit_ssd1306, busio
from board import SDA, SCL

i2c = busio.I2C(SCL, SDA)
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

api_key = "<YOUR OCTOPRINT API KEY>"
url_status = f"https://<YOUR 3D PRINTER IP ADDRESS>/api/printer?history=true&limit=1"
headers = {
	'Content-Type': 'application/json',
         'X-Api-Key': api_key
}

s = requests.Session()
df = pd.DataFrame()
bed = []
tool0 = []
time_data = []

def signal_handler(sig, frame):
	df["Bed"] = bed
	df["tool0"] = tool0
	df["Time"] = time_data
	df.to_csv("OctoPrintData.csv")
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


def GetStatus():
	response = s.get(url, headers=headers,verify=False)
	data = response.json()
	for i in data["temperature"]["history"]:
		try:
			bed.append(i["bed"]["actual"])	
			tool0.append(i["tool0"]["actual"])
			time_data.append(i["time"])
			print(data)
			display.fill(0)
			display.show()
			display.text(x=0,y=0,color="white",string="Nozzle: {}\nBed: {}".format(i["tool0"]["actual"], i["bed"]["actual"]))
			display.show()
		except:
			continue


while(True):

	GetStatus()
	print('\rBed:{}ºC tool0:{}ºC time:{}s state:{}'.format(i["bed"]["actual"], i["tool0"]["actual"], i["time"],data["state"]["text"]), end='', flush=True)
	
	time.sleep(1)



