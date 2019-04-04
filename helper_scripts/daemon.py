#!/usr/bin/python3
#-*- coding: utf-8 -*-

import time
import signal
import os
import json
#import subprocess
#import sqlite3

if __name__ == '__main__':
	pid = []

	# def fetch():
		# Enumerate patient ID numbers from JSON file
		#global pid
		#pid = json.load(open('pid.json', mode='r'))
		# Fetch data since date of latest result
		# TODO: add option to force refetch (alternatively, force-refetch every so often)
		#os.chdir("local")
		#for x in pid:
		#	conn = sqlite3.connect(x + '.sqlite3')
		#	c = conn.cursor()
		#	c.execute("SELECT time from lis_data ORDER BY time DESC LIMIT 1;")
		#	last_date = c.fetchone()[0]
		#	conn.close()
		#	subprocess.Popen(["/usr/bin/env python3", "import_labs_sqlite.py", "--start", last_date, x])
		#os.chdir("..")

	# Signal handler for SIGHUP (probably not needed as data is always refetched?)
	#def handler(signum, frame):
	#	print("[INFO] SIGHUP caught. Reloading patient ID list and re-fetching data.")
	#	fetch()
	#signal.signal(signal.SIGHUP, handler)

	# Time delay: 30 minutes + random delay of 0-10 minutes
	delay = 30*60 + random.randrange(600)
	#while True:
	#	fetch()
	#	for x in pid:
	#		db = x + ".sqlite3"
	#		subprocess.Popen(["/usr/bin/env python3", "lisanalyze.py", db])
	#	time.sleep(delay)