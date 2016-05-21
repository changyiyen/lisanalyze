#!/usr/bin/python3
#-*- coding: utf-8 -*-

##### Import modules #####
# Built-in modules
## Note that the pwd and grp modules only exist on Unix.
import os, sys
import argparse, configparser, json
import multiprocessing
import inspect, re

if os.name == "posix":
	import pwd, grp
# Third-party modules
import toposort

# Plugins
import modules
from modules.correction import *
from modules.analysis import *

import helper_scripts
##########################

if __name__ == '__main__':

	##### Security precautions #####
	# Try to drop root privileges first if applicable. Note that os.getuid() only
	# exists on Unix.
	if os.name == "posix":
		if os.getuid() == 0:
			print("[Warning] Root privileges found. Attempting to drop them.", file=sys.stderr)
			target_gid = grp.getgrnam('nogroup').gr_gid
			target_uid = pwd.getpwnam('nobody').pw_uid

			try:
				os.setgroups([])
				os.setgid(target_gid)
				os.setuid(target_uid)
				
			except OSError:
				print("[Error] Couldn't drop privileges. Aborting.")
				exit(1)
	################################

	##### Main program #####
	# Build argument parser
	import argparse

	parser = argparse.ArgumentParser(description="Automated analysis of lab data",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('db-file-read', help="Database file to read from")
	parser.add_argument('--db-file-write', help="Database file to write to; defaults to local_data/PID_local.sqlite3, where PID is the root name of the database file to read from.")
	#parser.add_argument('--db-username', help="Username to access database")
	#parser.add_argument('--db-password', help="Password to access database")
	#parser.add_argument('--db-private-key', help="PGP private key for decoding data")
	parser.add_argument('--debug', help="Print debug info")
	#parser.add_argument('--logfile', help="Path to logfile")
	#parser.add_argument('--no-convert', help="Disable automatic unit conversion using Pint")
	parser.add_argument('--version', action='version', version='%(prog)s 0.2 "White snow"')
	args_main = parser.parse_args()

	if not getattr(args_main, 'db_file_write'):
		d = vars(args_main)
		d['db_file_write'] = "local_data" + os.sep + os.path.splitext(args_main.db_file_read)[0] + '_local.sqlite3'

	# Read config file ('config.ini'). Configuration for both correction and
	# analysis modules are placed here.
	config = configparser.ConfigParser()
	config.read('config.ini')

	# Enumerate loaded lisanalyze modules. Names of correction modules should
	# be of the form "lisanalyze_ITEMNAME_SITE"; names of analysis modules
	# should be of the form "lisanalyze_DISEASENAME" (diseases should be in
	# camelcase if it is longer than one word).
	plugin_list_correction = [
		name for name,obj in inspect.getmembers(sys.modules[__name__])
		if (
			re.match('^lisanalyze_[a-zA-Z0-9]+_[a-z]+$', str(name)) and
			inspect.ismodule(obj)
		)
	]
	plugin_list_analysis = [
		name for name,obj in inspect.getmembers(sys.modules[__name__])
		if (
			re.match('lisanalyze_[a-zA-A0-9]+$', str(name)) and
			inspect.ismodule(obj)
		)
	]
	if args_main.debug:
		print("[Debug] List of loaded lisanalyze modules: ")
		print("Correction modules: ", plugin_list_correction)
		print("Analysis modules: ", plugin_list_analysis)

	# Resolve dependencies by using toposort. Entries in the correction
	# dependency file must be of the form "lisanalyze_ITEMNAME_SITE". Note the
	# lack of the file extension (i.e., ".py"). For example:
	# "lisanalyze_na_plasma".
	try:
		deps = json.load(open("correction_depends.json", mode='r'))
	except ValueError:
		raise Exception("Invalid correction_depends.json file")
	correction_deps_sorted = list(toposort({i:set(deps[i]) for i in deps}))
	correction_deps_entries = []
	for i in deps_sorted:
		correction_deps_entries.extend(list(i))

	# Assume modules not listed in the dependency file are independent,
	# and place them first in the list.
	correction_deps_sorted.insert(0, set([i for i in plugin_list_correction if i not in correction_deps_entries]))

	# *Correction Section*
	# Divide work among multiple processes.
	# Each module takes these arguments:
	# 1. database to read from
	# 2. database to write to
	# 3. relevant arguments
	# 4. queue to which results are sent (e.g., number of records
	#    processed, ...)
	# Each module may optionally provide a return value for debugging.
	for correction_jobs in correction_deps_sorted:
		if args_main.debug:
			print("[Debug] Current correction jobs: ", correction_jobs)

		with multiprocessing.pool.Pool() as pool:
			m = multiprocessing.Manager()
			q = m.Queue()
			results = [
				# It really sucks that I have to use eval()
				# here (and ast.literal_eval() can only produce
				# literals), but at least code injection via a
				# malicious module name isn't straightforward
				# (or so I hope). Really, an attacker could just
				# insert a module with a valid name that
				# contains a malicious correct() function and
				# trash everything...
				pool.apply_async(getattr(eval(job), "correct"), [args_main.db_file_read, config[job], q])
				for job in correction_jobs
			]
			pool.close()

			# Since get() blocks, we can assume the queue has been
			# used by every process after we call get() on every
			# AsyncResult object.
			retvals = [i.get() for i in results]

			if args_main.debug:
				print("[Debug] Return values for correction jobs: ", correction_jobs)
				for i in retvals:
					print(i)

			while not q.empty():
				print(q.get())

	# *Analysis Section*
	# Divide work among multiple processes.
	# Each module takes these arguments:
	# 1. database to use
	# 2. relevant arguments
	# 3. queue to which results are sent (e.g., number of records
	#    processed, ...)
	# Each module may optionally provide a return value for debugging.

	# Here we're assuming that diagnoses are independent of each other;
	# hence we simply iterate over the items in no particular order
	if args_main.debug:
		print("[Debug] Current analysis jobs: ", plugin_list_analysis)

	with multiprocessing.pool.Pool() as pool:
		m = multiprocessing.Manager()
		q = m.Queue()
		results = [
			pool.apply_async(getattr(eval(job), "analyze"), [args_main.db_file_read, args_main.db_file_write, config[job], q])
			for job in plugin_list_analysis
		]
		pool.close()

		# Since get() blocks, we can assume the queue has been
		# used by every process after we call get() on every
		# AsyncResult object.
		retvals = [i.get() for i in results]

		if args_main.debug:
			print("[Debug] Return values for analysis jobs: ", plugin_list_analysis)
			for i in retvals:
				print(i)

		while not q.empty():
			print(q.get())