#!/usr/bin/python3
#-*- coding: utf-8 -*-import sqlite3, json, datetime

def analyze(db_file, config_args, queue):
	'''Analysis function for arterial blood gas.'''
	conn_r = sqlite3.connect(db_file)
	conn_r.row_factory = sqlite3.Row
	c_r = conn_r.cursor()

	conn_w = sqlite3.connect(db_file)
	conn_w.row_factory = sqlite3.Row
	c_w = conn_w.cursor()

	try:
		normal_ranges = json.load(open("normal_range.json", mode='r'))
	except ValueError:
		raise Exception("Invalid normal_range.json file")

	try:
		# Get relevant range values (for pCO2, HCO3-)
	except KeyError:
		pass

	fuzzy_range = float(config_args["fuzzy_range"])

	c_r.execute("SELECT DISTINCT time FROM lis_data WHERE lab_item = '血液氣體分析及POCT檢驗報告' AND lab_test_name = 'pH';")
	abg_all = c_r.fetchall()
	for abg_time in abg_all:
		pH = c_r.execute("SELECT lab_value FROM lis_data WHERE lab_item = '血液氣體分析及POCT檢驗報告' AND  lab_test_name= 'pH' AND time = (?)", (abg_time))
	queue.put('lisanalyze_arterial_blood_gas: %s records processed' % len(abg_all))
	return False