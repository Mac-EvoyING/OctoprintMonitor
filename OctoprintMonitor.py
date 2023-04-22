import requests
import pandas as pd
import time
import signal
import sys
import json
import urllib3
import adafruit_ssd1306, busio
from board import SDA, SCL
import adafruit_ssd1306, busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from PIL import Image, ImageDraw, ImageFont
from gpiozero.pins.native import NativeFactory
from gpiozero import Button
global status
global tool0
global bed
global battery
global job

bed = dict()
tool0 = dict()
status = ""
job = {}
battery = 0


def Initialize():
	# Display
	print("Starting I2C Comm...")
	i2c = busio.I2C(1, 0, frequency=1000000)
	print("Initializing display...")
	display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c,reset=None)
	font = ImageFont.truetype('/home/pi/assets/neo_latina_demo_FFP.ttf', 12)
	image = Image.new("1", (128, 64))
	draw = ImageDraw.Draw(image)
	display.contrast(255)
	print("Display initialized.")
	print("Initialiying ADC...")
	ads = ADS.ADS1115(i2c,mode=256, gain=0.6666666666666666)

	print("ADC Initialized")
	return display, ads


def signal_handler(sig, frame):
	sys.exit(0)


def GetStatus():
	global tool0
	global status
	global bed
	global battery
	global job
	try:
		response = s.get(url_status, headers=headers,verify=False, timeout=0.8)
		data = response.json()
		status = data["state"]["text"]
		tool0 = data["temperature"]["history"][0]["tool0"]
		bed = data["temperature"]["history"][0]["bed"]

		if status == "Printing":
			response = s.get(url_job, headers=headers,verify=False, timeout=0.8)
			job = response.json()
	except KeyError:
		tool0 =  {"actual": "-", "target": "-"}
		bed = tool0
		status = "Offline"
	except OSError:
		tool0 =  {"actual": "-", "target": "-"}
		bed = tool0
		status = "Server down"
	except IndexError:
		print(data)
	batt = AnalogIn(ads, ADS.P0)
	battery = batt.voltage
	time.sleep(1)


def RefreshDisplay(display, nozzle=None, bed=None, status=None, battery=None):
	font_numbers = ImageFont.truetype('/home/pi/assets/Bandal.ttf', 20)
	font_numbers_small = ImageFont.truetype('/home/pi/assets/Bandal.ttf', 12)
	font_status = ImageFont.truetype('/home/pi/assets/neo_latina_demo_FFP.ttf', 11)
	font_file = ImageFont.truetype('/home/pi/assets/Bandal.ttf', 12)

	if status != "Printing":
		display_img = Image.open("/home/pi/assets/Display.ppm").convert('1')
		draw.bitmap((0,0),display_img, fill=255)
		draw.text((16, 0), "{}".format(str(status)), fill=255, font=font_status, align="center")
		draw.text((114, 6), "{:>5.1f}".format(battery),fill=255, font=font_numbers_small, align="left", anchor="mm")
		draw.text((33, 44),"{}".format(str(nozzle["actual"])), fill=255, font=font_numbers,align="left", anchor="mm")
		draw.text((25, 60),"{}".format(str(nozzle["target"])), fill=255, font=font_numbers_small, align="left", anchor="mm")
		draw.text((95, 44), "{}".format(str(bed["actual"])), fill=255, font=font_numbers, align="left", anchor="mm")
		draw.text((105, 60), "{}".format(str(bed["target"])), fill=255, font=font_numbers_small, align="left", anchor="mm")

	else:
		try:
			global job
			draw.text((16, 0), "{}".format(str(status)), fill=255, font=font_status, align="center")
			font_numbers_big = ImageFont.truetype('/home/pi/assets/Bandal.ttf', 17)
			display_img = Image.open("/home/pi/assets/Printing.ppm").convert('1')
			draw.bitmap((0,0),display_img, fill=255)

			draw.text((114, 6), "{:>5.1f}".format(battery),fill=255, font=font_numbers_small, align="left", anchor="mm")
			draw.text((64, 20), f"{job['job']['file']['name']}", fill=255, font=font_file,  align="center", anchor="mm")

			if job['progress']['printTimeLeft'] == None:
				draw.text((103, 49), f"--", fill=255, font=font_numbers_big,  align="center", anchor="mm")
			else:
				draw.text((103, 49), f"{job['progress']['printTimeLeft']/3600:.2f}h", fill=255, font=font_numbers_big,  align="center", anchor="mm")

			draw.text((37, 50), "{:>5.1f}%".format(job['progress']['completion']), fill=255, font=font_numbers_big,  align="left", anchor="mm")

			progress_bar = round(0.56*job['progress']['completion'])
			draw.rectangle([(7, 57), (7 + progress_bar, 61)], fill=255)

		except Exception as ex:
			print(ex)
			pass
	display.image(image)
	display.show()



urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

api_key = "08753898CCBA4DCFABF9601019DCA140"
url_status = f"https://22.3.7.12/api/printer?history=true&limit=1"
url_job = f"https://22.3.7.12/api/job"
headers = {
	'Content-Type': 'application/json',
	'X-Api-Key': api_key
}

s = requests.Session()
df = pd.DataFrame()
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
	disp, ads = Initialize()
	font = ImageFont.truetype('/home/pi/assets/neo_latina_demo_FFP.ttf', 12)
	image = Image.new("1", (disp.width, disp.height))
	draw = ImageDraw.Draw(image)
	draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)
	disp.image(image)
	disp.show()

	last_status = ""
	while True:
		GetStatus()
		RefreshDisplay(disp, nozzle=tool0, bed=bed, status=status, battery=battery)
		draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)
		disp.image(image)
		time.sleep(1)




