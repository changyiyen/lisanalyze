#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import datetime

regex = re.compile('((?P<weeks>[\d.]*?)\s*weeks?)?\s*((?P<days>[\d.]*?)\s*days?)?\s*((?P<hours>[\d.]*?)\s*hours?)?\s*((?P<minutes>[\d.]*?)\s*minutes?)?')

def gettimedelta(n):
	parts = regex.match(n)
	if not parts:
		return None
	t = parts.groupdict()
	params = {}
	for (i,j) in t.iteritems():
		if j:
			params[i] = float(j)
	return datetime.timedelta(**params)