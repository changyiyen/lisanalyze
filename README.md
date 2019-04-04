# lisanalyze

Simple analyzer suite for hospital laboratory information systems (LIS)

## Overview

This suite (lisanalyze) was written to support physicians whose work involves
monitoring lab values, and performing related actions. It is written in Python 3
and uses SQLite3 (which is part of the Python standard libraries) for local data
storage.

lisanalyze consists of the following components:

* docs
* helper_scripts
* local
* modules
  * analysis
  * correction
* config.ini
* correction_depends.json
* lisanalyze.py
* normal_range.json

### Components

* docs: contains documentation related to the inner workings of lisanalyze,
including how to write analysis modules
* helper_scripts: contains various small scripts that may make writing analysis
modules easier
* local: contains local SQLite3 databases that hold measurement values and
analysis results, among other things
* modules
  * analysis: contains analysis modules; each is named using the relevant ICD-10
  code
  * correction: contains correction algorithms for certain lab values
* config.ini: contains configuration options for each module (analysis and
correction)
* correction_depends.json: contains correction dependencies in the form of
key-value pairs (keys depend on values)
* lisanalyze.py: core program which makes calls to modules; not a daemon
* normal_range.json: contains normal ranges of each measurement; each is named
using the relevant LOINC code

### Dependencies

While effort has been taken to make lisanalyze depend on as few 3rd party
components (i.e., not part of the standard Python libraries) as possible, it
still depends on the following 3rd party components:

* bs4 (for lab data web scraper script)
* SciPy (for statistics)
* numpy (a dependency of SciPy)
* Pint (for unit conversion)

### License

lisanalyze is released under the MIT license.