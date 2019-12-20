#!/usr/bin/python3
#-*- coding: utf-8 -*-

##### Import modules #####
# Built-in modules
## Note that the pwd and grp modules only exist on Unix.
import os, sys
import argparse, configparser, json
import multiprocessing.pool
import inspect, re

if os.name == "posix":
	import pwd, grp
# Third-party modules

# Plugins
from modules.correction import *
from modules.analysis import *

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
				print("[Info] Dropped privileges.")
			except OSError:
				print("[Error] Couldn't drop privileges. Aborting.")
				exit(1)
	################################

	##### Main program #####
	# Build argument parser
	parser = argparse.ArgumentParser(description="Automated analysis of lab data",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('db_file', help="SQLite database file to use")
	#parser.add_argument('--db-username', help="Username to access database")
	#parser.add_argument('--db-host', help="Database host")
	#parser.add_argument('--db-password', help="Password to access database")
	#parser.add_argument('--db-private-key', help="PGP private key for decoding data")
	parser.add_argument('--debug', action='store_true', help="Print debug info")
	#parser.add_argument('--logfile', help="Path to logfile")
	#parser.add_argument('--no-convert', help="Disable automatic unit conversion using Pint")
	parser.add_argument('--version', action='version', version='%(prog)s 0.2.0 "White snow"')
	args_main = parser.parse_args()

	# Read config file ('config.ini'). Configuration for both correction and
	# analysis modules are placed here.
	config = configparser.ConfigParser()
	config.read('config.ini')

	# Enumerate loaded lisanalyze modules. Names of correction modules should
	# be of the form "lisanalyze_LOINCCODE"; names of analysis modules
	# should be of the form "lisanalyze_ICD10CODE". ICD-10-CM is used here.
	# ICD-10-CM validation regex original source: https://gist.github.com/jakebathman/c18cc117caaf9bb28e7f60e002fb174d
	# (modified the dot used in ICD-10-CM to a dash because it interferes with package naming)
	# LOINC result codes taken from spreadsheet published by Mayo Medical Labs (December 2018).

	plugin_list_correction = [
		name for name,obj in inspect.getmembers(sys.modules[__name__])
		if (
			re.match('^lisanalyze_[0-9]+[-][0-9]+$', str(name)) and
			inspect.ismodule(obj)
		)
	]
	plugin_list_analysis = [
		name for name,obj in inspect.getmembers(sys.modules[__name__])
		if (
			re.match('lisanalyze_[A-TV-Z][0-9][A-Z0-9](_?[A-Z0-9]{0,4})?$', str(name)) and
			inspect.ismodule(obj)
		)
	]
	if args_main.debug:
		print("[Debug] List of loaded lisanalyze modules: ")
		print("Correction modules: ", plugin_list_correction)
		print("Analysis modules: ", plugin_list_analysis)

	# Resolve dependencies by using topological sort.
	try:
		deps = json.load(open("correction_depends.json", mode='r'))
	except ValueError:
		raise Exception("Invalid correction_depends.json file")
	# Toposort
	correction_deps_entries = [] # final list
	x = dict() # nodes dict
	for k,v in deps.items():
		x[k]=0
		for i in v:
			x[i]=0
	def visit(n):
		# visit marks: 1 for permanent, 2 for temporary
		if x[n]==1:
			return True
		if x[n]==2:
			print("Error: loop detected", n)
			return True
		if n not in deps.keys(): # leaf node
			x[n]=1
			correction_deps_entries.append(n)
			return True
		x[n]=2
		for i in deps[n]:
			visit(i)
		x[n]=1
		correction_deps_entries.append(n)
	while 0 in x.values():
		i = filter(lambda u: x[u]==0, x.keys())
		t = i.__next__()
		if t:
			visit(t)

	# *Correction Section*
	# Divide work among multiple processes.
	# Each module takes these arguments:
	# 1. database to read from
	# 2. database to write to
	# 3. relevant arguments
	# 4. queue to which results are sent (e.g., number of records
	#    processed, ...)
	# Each module may optionally provide a return value for debugging.
	for correction_jobs in correction_deps_entries:
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
				pool.apply_async(getattr(eval(job), "correct"), [args_main.db_file, config[job], q])
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
	# 1. database to read from
	# 2. database to write to
	# 3. relevant arguments
	# 4. queue to which results are sent (e.g., number of records
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
			pool.apply_async(getattr(eval(job), "analyze"), [args_main.db_file, config[job], q])
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