#!/usr/bin/python3
#-*- coding: utf-8 -*-

import sqlite3, datetime, statistics
import helper_scripts.gettimedelta as gettimedelta

# Note: currently this correction function writes the corrected value back into
# the database. Whether this is a better approach than writing to a separate
# database remains to be seen.
def correct(db_file, config_args, queue):
	'''Correction for plasma sodium levels.'''
	# lis_data table structure: (time TEXT, lab_item TEXT, site TEXT, lab_value TEXT, ref_low TEXT, ref_high TEXT, unit TEXT, method TEXT, comment TEXT, corrected INTEGER)
	conn = sqlite3.connect(db_file)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()
	c.execute("SELECT * FROM lis_data WHERE lab_item = 'sodium' AND site = 'plasma' AND corrected = '0'")
	sodium_all = c.fetchall()

	# time: ISO8601 format
	range_before = gettimedelta(config_args["time_range_before"])
	range_after = gettimedelta(config_args["time_range_after"])

	if config_args["auto_unit_conversion"].lower() == "true":
		import pint
		ureg = pint.UnitRegistry()

	# Sodium correction using glucose
	for sodium in sodium_all:
		t = datetime.datetime.strptime(sodium["time"], "%Y-%m-%dT%H:%M:%S")
		t_before = (t - range_before).strftime("%Y-%m-%dT%H:%M:%S")
		t_after = (t + range_after).strftime("%Y-%m-%dT%H:%M:%S")

		# We're forced to use this rather contrived method since Pint doesn't
		# print to the standard abbreviated units we use in our records.
		if config_args["auto_unit_conversion"].lower() == "true":
			# Potentially dangerous as Pint uses eval()...
			factor = ureg.parse_expression(sodium["unit"]).to(config_args["preferred_unit"]).magnitude
			converted_sodium = float(sodium["lab_value"]) * factor
			converted_sodium_ll = float(sodium["ref_low"]) * factor
			converted_sodium_ul = float(sodium["ref_high"]) * factor
		else:
			# using raw values here; here's hoping it's in mmol/l or mEq/l
			non_converted_sodium = float(sodium["lab_value"])

		# No correction needed for glucose itself as mentioned in the Pocket
		# Guide to Diagnostic Tests 6e.
		# Hopefully all relevant glucose measurements have been converted to
		# mg/dl. Uses average of glucose levels measured within time range.
		c.execute("SELECT * FROM lis_data WHERE (time BETWEEN ? AND ?) AND lab_item='glucose' AND site='plasma' AND unit='mg/dl'", (t_before, t_after))
		glucose = statistics.mean([float(i["lab_value"]) for i in c.fetchall()])

		# Where the correction is made. Assuming required correction is linear,
		# and not nonlinear as has been reported.
		if glucose > float(config_args["glucose_normal"]):
			if config_args["auto_unit_conversion"].lower() == "true":
				corrected_sodium = converted_sodium + 1.6 * (glucose - float(config_args["glucose_normal"])) / 100.0
			else:
				corrected_sodium = non_converted_sodium + 1.6 * (glucose - float(config_args["glucose_normal"])) / 100.0
		else:
			if config_args["auto_unit_conversion"].lower() == "true":
				corrected_sodium = converted_sodium
			else:
				corrected_sodium = non_converted_sodium

		# Inserting instead of updating in case someone wants the raw data
		if config_args["auto_unit_conversion"].lower() == "true":
			c.execute("INSERT INTO lis_data VALUES (?,?,?,?,?,?,?,?,?)",
				(sodium["time"], "sodium", "plasma", str(corrected_sodium), str(converted_sodium_ll), str(converted_sodium_ul), config_args["preferred_unit"], sodium["method"], sodium["comment"], 1)
			)
		else:
			c.execute("INSERT INTO lis_data VALUES (?,?,?,?,?,?,?,?,?)",
				(sodium["time"], "sodium", "plasma", str(corrected_sodium), sodium["ref_low"], sodium["ref_high"], sodium["unit"], sodium["method"], sodium["comment"], 1)
			)
		conn.commit()
	queue.add("lisanalyze_na_plasma: %s records processed" % len(sodium_all))
	return False
