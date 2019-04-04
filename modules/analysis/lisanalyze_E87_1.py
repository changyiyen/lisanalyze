#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sqlite3, json, datetime

def analyze(db_file, config_args, queue):
	'''Analysis function for hyponatremia (E87.1).'''
	conn_r = sqlite3.connect(db_file)
	conn_r.row_factory = sqlite3.Row
	c_r = conn_r.cursor()

	conn_w = sqlite3.connect(db_file)
	conn_w.row_factory = sqlite3.Row
	c_w = conn_w.cursor()

	hyponatremia_trigger_count = 0
	correction_trigger_count = 0

	try:
		normal_ranges = json.load(open("normal_range.json", mode='r'))
	except ValueError:
		raise Exception("Invalid normal_range.json file")

	try:
		sodium_ul = float(normal_ranges["sodium_plasma_u"])
		sodium_ll = float(normal_ranges["sodium_plasma_l"])
	except KeyError:
		pass

	fuzzy_range = float(config_args["fuzzy_range"])

	#c_r.execute("SELECT * FROM lis_data WHERE lab_item = 'sodium' AND site = 'plasma' AND corrected = '1'")
	c_r.execute("SELECT * FROM lis_data WHERE lab_test_name = 'NA' AND site = '血液'")
	sodium_all = c_r.fetchall()
	for record in sodium_all:
		if sodium_ul not in locals():
			sodium_ul = float(record["ref_high"])
		if sodium_ll not in locals():
			sodium_ll = float(record["ref_low"])
		# Add some fuzziness
		sodium_ll = sodium_ll - (sodium_ul - sodium_ll) * fuzzy_range
		if float(record["lab_value"]) < sodium_ll:
			#c_w.execute("REPLACE INTO analysis_results (time, result, analysis_time) VALUES (?,?,?)", (record["time"], "Hyponatremia", datetime.datetime.now().isoformat()))
			c_w.execute("REPLACE INTO analysis_results (time, result) VALUES (?,?)", (record["time"], 'Hyponatremia'))
			conn_w.commit()
			hyponatremia_trigger_count += 1
	# Warn if correction of hyponatremia is too rapid
	#for i in range(1, len(sodium_all)):
	#	rate = (float(sodium_all[i]["lab_value"])-float(sodium_all[i-1]["lab_value"])) / (datetime.datetime.strptime(sodium_all[i]["time"])-datetime.datetime.strptime(sodium_all[i-1]["time"])).total_seconds()
	#	if rate > (float(config_args["max_correction_rate"])/86400):
	#		c_w.execute("REPLACE INTO analysis_results (time, result) VALUES (?,?)", (sodium_all[i]["time"], "[WARNING] Hyponatremia module: over-rapid correction of hyponatremia, rate %f mEq/L/day by linear extrapolation" % (rate * 86400)))
	#		conn_w.commit()
	#		correction_trigger_count += 1
	queue.put("Hyponatremia module: %d records processed; hyponatremia triggered %d times" % (len(sodium_all), hyponatremia_trigger_count))
	#queue.put("Hyponatremia module: %d records processed; hyponatremia triggered %d times, over-rapid correction triggered %d times" % (len(sodium_all), hyponatremia_trigger_count, correction_trigger_count))
	conn_r.close()
	conn_w.close()
	return False