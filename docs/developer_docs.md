# Documentation for lisanalyze developers (version 0.2.0)

## Introduction

This file contains notes on the design of the lisanalyze software package,
meant for developers who wish to extend its capabilities by writing analysis
modules and developing the core code.
 
## Database table schema

lisanalyze uses an SQL database for its operations. It was developed using
SQLite (more specifically the sqlite3 module provided by the Python 3 standard
library), but aims to be as database-agnostic as possible by following the
SQL92 standard (which, again, is followed by the Python 3 sqlite3 module).

The database schema is as follows:

* Table "analysis_results" contains 2 columns, "time" (TEXT) and "result"
(TEXT). "time" contains the time of the latest event for which triggering of
the analysis result is sufficient (expressed in ISO 8601 time, with timezone
set to local and with minute accuracy), while "result" is a human-readable text
description of the analysis result.

* Table "db_info" contains 2 columns, "key" (TEXT) and "value" (TEXT). It is
used as a simple key-value store for metadata.
  * metadata contained within this table include:
    * last_access_time
    * time_range_start
    * time_range_end
    * lisanalyze_version
    * schema_version

* Table "lis_data" contains 11 columns:
  * time
  * lab_item
  * site
  * lab_test_name
  * lab_value
  * ref_low
  * ref_high
  * unit
  * method
  * comment
  * corrected

## Writing new modules for lisanalyze

Writing modules for lisanalyze is a relatively straightforward process; the
provided modules can serve as code examples.

Things to be aware of when writing new modules:

1. Modules must be placed in the "modules/analysis" directory and have the
filename form "lisanalyze_ICD10CODE.py", where ICD10CODE is the ICD-10-CM code
for your diagnosis, but with the period replaced with an underscore (for
example, "E87.1", which is the code for hyponatremia, becomes "E87_1"; thus the
filename is "lisanalyze_E87_1.py"). The reason for this is because of Python's
module loading mechanism.

2. Every module should implement a function named "analyze", which takes 3
arguments: db_file (the path of the SQLite3 database file to load), config_args
(a dictionary containing configuration options, as contained in config.ini),
and queue (a multiprocessing.Queue object to send return messages to).

3. Once your module is complete, remember to put the name of your module into
"modules/analysis/__init__.py" so Python can load it. Also note that,
regardless of whether your module needs configuration options, there must be an
entry in config.ini for your module (which can be blank).

## Future directions

The lisanalyze database can be easily extended to include other parameters such
as vital signs, allowing for automated calculations of clinical scores and
other determinants, such as absolute neutrophil count.
