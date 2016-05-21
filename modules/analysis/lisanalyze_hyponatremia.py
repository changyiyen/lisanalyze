#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sqlite3, json

def analysis(db_file_read, db_file_write, config_args, queue):
	'''Analysis function for hyponatremia.'''
	conn_r = sqlite3.connect(db_file_read)
	conn_r.row_factory = sqlite3.Row
	c_r = conn_r.cursor()

	conn_w = sqlite3.connect(db_file_write)
	conn_w.row_factory = sqlite3.Row
	c_w = conn_w.cursor()

	try:
		normal_ranges = json.load(open("normal_range.json", mode='r'))
	except ValueError:
		raise Exception("Invalid normal_range.json file")

	try:
		sodium_ul = normal_ranges["sodium_plasma_u"]
		sodium_ll = normal_ranges["sodium_plasma_l"]
	except KeyError:
		pass

	fuzzy_range = float(config_args["fuzzy_range"])

	c_r.execute("SELECT * FROM lis_data WHERE lab_item = 'sodium' AND site = 'plasma' AND corrected = '1'")
	sodium_all = c_r.fetchall()
	for record in sodium_all:
		if sodium_ul not in locals():
			sodium_ul = record["ref_high"]
		if sodium_ll not in locals():
			sodium_ll = record["ref_low"]
		# Add some fuzziness
		sodium_ll = sodium_ll - (sodium_ul - sodium_ll) * fuzzy_range
		
		if float(record["lab_value"]) < sodium_ll:
			c_w.execute("INSERT INTO analysis_results (time, result) VALUES (?,?)", (record["time"], "Hyponatremia"))
			conn_w.commit()
	queue.add('lisanalyze_hyponatremia: %s record processed' % len(sodium_all))
	return False