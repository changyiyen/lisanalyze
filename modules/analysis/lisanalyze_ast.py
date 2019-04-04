#!/usr/bin/python3
#-*- coding: utf-8 -*-import sqlite3, json, datetime

def analyze(db_file, config_args, queue):
	'''Analysis function for AST.'''
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


	fuzzy_range = float(config_args["fuzzy_range"])

	c_r.execute("SELECT time, lab_value FROM lis_data WHERE lab_item = '血液' AND lab_test_name = 'AST';")
	ast_all = c_r.fetchall()
	# T = (t log2) / (log y - log x), where T: half life, t: elapsed time, y: old value, x: new value

	queue.put('lisanalyze_ast: %s records processed' % len(ast_all))
	conn_r.close()
	conn_w.close()
	return False