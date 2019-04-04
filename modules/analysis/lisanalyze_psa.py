#!/usr/bin/python3
#-*- coding: utf-8 -*-
import sqlite3, json, time
#import scipy.stats

def analyze(db_file, config_args, queue):
	'''Analysis function for PSA.'''
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

	c_r.execute("SELECT time, lab_value FROM lis_data WHERE site = '血液' AND lab_test_name = 'PSA';")
	psa_all = c_r.fetchall()

	# Assuming psa_all looks something like [('2010-01-01 11:11:11', 0.5), ('2011-01-01 11:11:11', 1.5), ('2012-01-01 11:11:11', 2.5), ...]
	# Here we're calculating the PSA rate simply by doing a linear regression on all values and looking at the slope (which is itself questionable)
	#slope, intercept, rvalue, pvalue, stderr = scipy.stats.linregress([time.mktime(time.strptime(i[0],'%Y-%m-%d %H:%M:%S')) for i in psa_all], [float(i[1]) for i in psa_all])
	# Not sure if time should be time of analysis (i.e. current time) or something else...
	# Also, the slope should be user-definable (i.e. placed in config_args)
	#if slope > 3.1709791983764586e-08: # rate of 1.0/year (in other words, 1.0/(365*24*60*60))
	#	c_w.execute("REPLACE INTO analysis_results (time, result) VALUES (?,?)", (datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'), "[WARNING] PSA module: PSA rate too fast (%f per year)" % (slope * 365*24*60*60))

	queue.put('lisanalyze_psa: %s records processed' % len(psa_all))
	conn_r.close()
	conn_w.close()
	return False