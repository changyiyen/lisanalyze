#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sqlite3, json, datetime

def analyze(db_file, config_args, queue):
	'''Analysis function for acute kidney failure, unspecified (N17.9).'''
	conn_r = sqlite3.connect(db_file)
	conn_r.row_factory = sqlite3.Row
	c_r = conn_r.cursor()

	conn_w = sqlite3.connect(db_file)
	conn_w.row_factory = sqlite3.Row
	c_w = conn_w.cursor()

	trigger_count = 0

	try:
		normal_ranges = json.load(open("normal_range.json", mode='r'))
	except ValueError:
		raise Exception("Invalid normal_range.json file")

	c_r.execute("""
		SELECT DISTINCT time
		FROM lis_data
		WHERE lab_test_name = 'CREA' AND site = '血液'
		AND ( lab_value -
		    ( SELECT x.lab_value FROM lis_data x
		      WHERE x.lab_test_name='CREA' AND site = '血液'
		      AND x.time < lis_data.time ORDER BY x.time DESC LIMIT 1
		    )
		) /
		( time -
			( SELECT x.time FROM lis_data x
				WHERE x.lab_test_name='CREA' AND site = '血液'
				AND x.time < lis_data.time ORDER BY x.time DESC LIMIT 1
			)
  		) > (0.6 / (2*24*60*60));""")

	aki_time = c_r.fetchall()
	for t in aki_time:
		#c_w.execute("REPLACE INTO analysis_results (time, result, analysis_time) VALUES (?,?,?)", (record["time"], "Hyponatremia", datetime.datetime.now().isoformat()))
		c_w.execute("REPLACE INTO analysis_results (time, result) VALUES (?,?)", (t, "Acute kidney injury"))
		conn_w.commit()
		trigger_count += 1
	queue.put('Acute kidney injury module: %d records processed, triggered %d times' % (len(aki_time), trigger_count))
	conn_r.close()
	conn_w.close()
	return False