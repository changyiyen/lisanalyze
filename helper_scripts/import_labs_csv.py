#!/usr/bin/python
# -*- coding: utf-8 -*-

# Imports lab values from the EMR server and writes the data to a CSV file
# using the patient's ID number in the filename.
# Original code written by Dr. Tsai Mu-Hung for Python 2.
# Rewritten for Python 3.

VERSION = "0.1.1-20190713"

# Changelog:
# 0.1.0: initial release
# 0.1.1: can now use file of PIDs as input

import argparse
#import csv
import datetime
import re
import sys
import urllib.request

import unicodecsv as csv
import bs4

def build_soap_menu(pid, start, end):
	'''Creates SOAP envelope for the menu containing lab tests ordered'''
	s_head='<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://www.w3.org/2005/08/addressing"><s:Header><a:Action s:mustUnderstand="1">http://tempuri.org/IEmrService/EMRQueryReportRecord</a:Action><a:MessageID>urn:uuid:713986fa-2887-494b-a008-6d696ad019d1</a:MessageID><a:ReplyTo><a:Address>http://www.w3.org/2005/08/addressing/anonymous</a:Address></a:ReplyTo><a:To s:mustUnderstand="1">http://hisweb.hosp.ncku/HISService/OPD/nckuHisWeb/EmrService.svc</a:To></s:Header><s:Body><EMRQueryReportRecord xmlns="http://tempuri.org/"><ChartNO><xs:schema id="NewDataSet" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata"><xs:element name="NewDataSet" msdata:IsDataSet="true" msdata:UseCurrentLocale="true"><xs:complexType><xs:choice minOccurs="0" maxOccurs="unbounded"><xs:element name="Table1"><xs:complexType><xs:sequence><xs:element name="source" type="xs:string" minOccurs="0"/><xs:element name="source1" type="xs:string" minOccurs="0"/><xs:element name="source2" type="xs:string" minOccurs="0"/><xs:element name="source3" type="xs:string" minOccurs="0"/><xs:element name="Chart_No" type="xs:string" minOccurs="0"/><xs:element name="dept_Code" type="xs:string" minOccurs="0"/><xs:element name="start_time" type="xs:string" minOccurs="0"/><xs:element name="end_time" type="xs:string" minOccurs="0"/><xs:element name="Doctor_Code" type="xs:string" minOccurs="0"/><xs:element name="specimen_Id" type="xs:string" minOccurs="0"/><xs:element name="Body_Site_Code" type="xs:string" minOccurs="0"/><xs:element name="request_no" type="xs:string" minOccurs="0"/><xs:element name="report_class" type="xs:string" minOccurs="0"/></xs:sequence></xs:complexType></xs:element><xs:element name="EMR_Query_Log"><xs:complexType><xs:sequence><xs:element name="Query_Time" type="xs:string"/><xs:element name="Employee_Code" type="xs:string" minOccurs="0"/><xs:element name="Employee_Name" type="xs:string" minOccurs="0"/><xs:element name="Query_Item_Id" type="xs:string" minOccurs="0"/><xs:element name="Login_System_Id" type="xs:string" minOccurs="0"/><xs:element name="Query_Content" type="xs:string" minOccurs="0"/><xs:element name="Action_Type" type="xs:string" minOccurs="0"/><xs:element name="Output_Count" type="xs:string" minOccurs="0"/><xs:element name="Output_Device" type="xs:string" minOccurs="0"/></xs:sequence></xs:complexType></xs:element></xs:choice></xs:complexType><xs:unique name="Constraint1" msdata:PrimaryKey="true"><xs:selector xpath=".//EMR_Query_Log"/><xs:field xpath="Query_Time"/></xs:unique></xs:element></xs:schema><diffgr:diffgram xmlns:diffgr="urn:schemas-microsoft-com:xml-diffgram-v1" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata"><NewDataSet xmlns=""><Table1 diffgr:id="Table11" msdata:rowOrder="0" diffgr:hasChanges="inserted"><source/><Chart_No>'
	s_body = pid + '</Chart_No><dept_Code>0000</dept_Code><start_time>' + start + '</start_time><end_time>' + end
	s_end='</end_time><Doctor_Code/><specimen_Id/><Body_Site_Code/><report_class/></Table1></NewDataSet></diffgr:diffgram></ChartNO></EMRQueryReportRecord></s:Body></s:Envelope>'
	return s_head + s_body + s_end

def build_soap_item(pid, serialno):
	s_part1='<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://www.w3.org/2005/08/addressing"><s:Header><a:Action s:mustUnderstand="1">http://tempuri.org/IEmrService/EMRGetExamineReport</a:Action><a:MessageID>urn:uuid:1c90d277-c568-4e8a-a265-4d4556038660</a:MessageID><a:ReplyTo><a:Address>http://www.w3.org/2005/08/addressing/anonymous</a:Address></a:ReplyTo><a:To s:mustUnderstand="1">http://hisweb.hosp.ncku/HISService/OPD/nckuHisWeb/EmrService.svc</a:To></s:Header><s:Body><EMRGetExamineReport xmlns="http://tempuri.org/"><requestNo xmlns:b="http://schemas.microsoft.com/2003/10/Serialization/Arrays" xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><b:string>'
	s_part2 = serialno + '</b:string></requestNo><Chart_No>' + pid
	s_part3='</Chart_No><ds><xs:schema id="NewDataSet" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata"><xs:element name="NewDataSet" msdata:IsDataSet="true" msdata:UseCurrentLocale="true"><xs:complexType><xs:choice minOccurs="0" maxOccurs="unbounded"><xs:element name="EMR_Query_Log"><xs:complexType><xs:sequence><xs:element name="Query_Time" type="xs:string"/><xs:element name="Employee_Code" type="xs:string" minOccurs="0"/><xs:element name="Employee_Name" type="xs:string" minOccurs="0"/><xs:element name="Query_Item_Id" type="xs:string" minOccurs="0"/><xs:element name="Login_System_Id" type="xs:string" minOccurs="0"/><xs:element name="Query_Content" type="xs:string" minOccurs="0"/><xs:element name="Action_Type" type="xs:string" minOccurs="0"/><xs:element name="Output_Count" type="xs:string" minOccurs="0"/><xs:element name="Output_Device" type="xs:string" minOccurs="0"/></xs:sequence></xs:complexType></xs:element></xs:choice></xs:complexType><xs:unique name="Constraint1" msdata:PrimaryKey="true"><xs:selector xpath=".//EMR_Query_Log"/><xs:field xpath="Query_Time"/></xs:unique></xs:element></xs:schema><diffgr:diffgram xmlns:diffgr="urn:schemas-microsoft-com:xml-diffgram-v1" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata"><NewDataSet xmlns=""><EMR_Query_Log diffgr:id="EMR_Query_Log1" msdata:rowOrder="0" diffgr:hasChanges="inserted"><Query_Time></Query_Time><Employee_Code></Employee_Code><Employee_Name></Employee_Name><Query_Item_Id></Query_Item_Id><Login_System_Id>EMR</Login_System_Id><Query_Content></Query_Content><Action_Type></Action_Type><Output_Count></Output_Count><Output_Device></Output_Device></EMR_Query_Log></NewDataSet></diffgr:diffgram></ds></EMRGetExamineReport></s:Body></s:Envelope>'
	return s_part1 + s_part2 + s_part3

def write_item(pid, lab_request_no, sample_site, csv_writer):
	'''Requests results and write them to CSV file'''
	if args.debug:
		print("[DEBUG] Currently in function write_item()...")
		print("[DEBUG] Building SOAP item request for request no. %s..." % lab_request_no)
	soap_env = build_soap_item(pid, lab_request_no)
	if args.debug:
		print("[DEBUG] Creating request URL...")
	url = urllib.request.Request(emrservice, bytes(soap_env, 'utf-8'), header_data)
	if args.debug:
		print("[DEBUG] Requesting data...")
	response = urllib.request.urlopen(url)
	if args.raw and args.debug:
		print('[DEBUG] Raw output from write_item(): ', response, file=sys.stderr)
	# Throws an UnicodeEncodeError because some genius used <選> as a tag, we will replace it with <gibberish>
	response_utf8 = response.read().decode('utf-8').replace(u'\u9078', 'gibberish')
	if args.debug:
		print("[DEBUG] Parsing response data as XML...")
	soup = bs4.BeautifulSoup(response_utf8, 'xml')
	if args.debug:
		print("[DEBUG] Parsing retExamineRecord (write_item())...")
	report_attrs = soup.find('retExamineRecord') # All reports under lab_request_no
	if args.debug:
		print("[DEBUG] Parsing retStateReportList...")
	report_text = soup.find('retStateReportList') # Will return results for text report
	report_num = soup.find_all('retNumReportLis') # Will return results for numeric report

	# TODO: consider adding option to get text reports, numeric reports, or both
	# Text reports
	if report_text and (args.mode == 'all' or args.mode == 'text'):
		if args.debug:
			print("[DEBUG] Inserting text report into CSV file...")
		csv_writer.writerow([pid, datetime.datetime.strptime(report_attrs.Execute_Time.text, "%Y/%m/%d %H:%M:%S").isoformat(), report_attrs.Report_Name.text, sample_site, report_text.Report_Text.text])
	elif report_num and (args.mode == 'all' or args.mode == 'numeric'):
	# Numeric reports
		if args.debug:
			print("[DEBUG] Parsing retNumReportLis...")
		for report in report_num:
			if args.debug:
				print("[DEBUG] Inserting numerical report into CSV file...")
			# Skip blank reports
			if (report.Test_Name.text, report.Test_Value.text, report.Unit.text) == ("","",""):
				continue
			#csv_writer.writerow([pid, datetime.datetime.strptime(report_attrs.Execute_Time.text, "%Y/%m/%d %H:%M:%S").isoformat(), report_attrs.Report_Name.text, sample_site, report.Test_Name.text, report.Test_Value.text, report.Ref_Low.text, report.Ref_High.text, report.Unit.text, '0'])
			csv_writer.writerow([pid, datetime.datetime.strptime(report_attrs.Execute_Time.text, "%Y/%m/%d %H:%M:%S").isoformat(), report_attrs.Report_Name.text, report.Test_Name.text, report.Test_Value.text, report.Unit.text])
	return False

def get_lab_data(pid, start='2018/1/1', end='today'):
	'''Main request function. Start date (arbitrarily) hardcoded as 2018/1/1 .'''
	# Default value of end is the string 'today'. Ugly kludge, but currently no better ideas.
	if end == 'today':
		end = today
	if args.debug:
		print("[DEBUG] Currently in function get_lab_data()...")
		print("[DEBUG] Start date:", start)
		print("[DEBUG] End date:", args.end)
		print("[DEBUG] Building SOAP menu request...")
	soap_env = build_soap_menu(pid, start, end)
	if args.debug:
		print("[DEBUG] Creating request URL...")
	url = urllib.request.Request(emrservice, data=bytes(soap_env, 'utf-8'), headers=header_data)
	if args.debug:
		print("[DEBUG] Requesting data...")
	response = urllib.request.urlopen(url)
	r = response.read()
	if args.raw and args.debug:
		print('[DEBUG] Raw output from get_lab_data(): ', r, file=sys.stderr)
	if args.debug:
		print("[DEBUG] Parsing response data as XML...")
	soup = bs4.BeautifulSoup(r, 'xml')
	if args.debug:
		print("[DEBUG] Soup:", soup)

	# Get all reports ordered for this particular pid
	if args.debug:
		print("[DEBUG] Finding retExamineRecord (get_lab_data())...")
	reports_all = soup.find_all('retExamineRecord')
	if args.debug:
		print("[DEBUG] All reports:", reports_all)
	if len(reports_all) == 0:
		print("Error: no reports returned for " + pid, file=sys.stderr)
		with open("error.log", mode="a+", encoding="utf-8") as fh:
			print(u"Error processing " + str(pid), file=fh)
		if not args.file:
			exit(1)
	else:
		# Try to use CSV
		filename = pid + "_lab" + ".csv"
		csv_writer = csv.writer(open(filename, 'wb+'), encoding='utf-8')
		# Write header
		#csv_writer.writerow([u"Patient_ID", u"Time", u"Report_Type", u"Test_name", u"Value", u"Unit"])
	for report in reports_all:
		# u'\u78ba\u8a8d\u5831\u544a' == '確認報告'
		# Note that report.Status.text may be empty
		if args.debug:
			print("[DEBUG] Report status: ", report.Status.text)
		if report.Status.text != u'\u78ba\u8a8d\u5831\u544a':
			continue
		# sample_site refers to site of sample collection (e.g., blood). Note
		# this is in Chinese.
		sample_site = report.Code_Name.text
		if args.debug:
			print("[DEBUG] sample_site is: " + sample_site)
		# You know, this typo should've been corrected a long time ago...
		write_item(pid, report.Requset_No.text, sample_site, csv_writer)
	return False

if __name__ == '__main__':
	# Creates our argument parser. This program takes only 1 argument, which is	
	# the patient's ID number (medical record number).
	parser = argparse.ArgumentParser(description='Retrieve LIS data and write to CSV file.')
	parser.add_argument('-d', '--debug', action='store_true', help='print debug messages')
	parser.add_argument('-m', '--mode', type=str, choices=['all', 'text', 'numeric'], help='type of report to retrieve (default: all)', default='all')
	parser.add_argument('-s', '--start', type=str, default='2018-01-01', help='start date (default: 2018-01-01)')
	parser.add_argument('-e', '--end', type=str, default='today', help='end date (default: today)')
	parser.add_argument('-f', '--file', type=str, help='file containing patient record numbers, one on each line')
	parser.add_argument('-p', '--pid', type=str, required=('-f' not in sys.argv) and ('--file' not in sys.argv), help='patient record number')
	parser.add_argument('-r', '--raw', action='store_true', help='print raw returned data (for debugging)')
	parser.add_argument('--version', action='version', version="%(prog)s version " + VERSION)
	args = parser.parse_args()

	# Define the EMR service URL and appropriate header here
	emrservice = 'http://hisweb.hosp.ncku/HISService/OPD/nckuHisWeb/EmrService.svc'
	header_data = {'Content-Type': 'application/soap+xml; charset=utf-8','User-Agent':''}
	if args.debug:
		print("[DEBUG] emrservice:" + emrservice)

	# Generates dates in the format YYYY/MM/DD, where the months and days are not
	# zero-padded. For example: 2016/5/13.
	# Important distinction to make here: 'args.start' and 'args.end' are the
	# ISO8601-formatted start and end dates, while 'start' and 'end' are the mangled
	# start and end dates.
	d = datetime.datetime.now()
	s = datetime.datetime.strptime(args.start, '%Y-%m-%d')
	e = d if (args.end.lower()=='today') else (datetime.datetime.strptime(args.end, '%Y-%m-%d'))
	today = '/'.join(map(str,[d.year,d.month,d.day]))
	last_year = '/'.join(map(str,[d.year-1,d.month,d.day]))
	start = '/'.join(map(str,[s.year,s.month,s.day]))
	end = today if (args.end.lower()=='today') else '/'.join(map(str,[e.year,e.month,e.day]))
	if args.debug:
		print("[DEBUG] Today's date: " + today)
		print("[DEBUG] Last year's date: " + last_year)
		print("[DEBUG] Start date: " + start)
	if s > e:
		print("Error: start date later than end date", file=sys.stderr, flush=True)
		exit(1)

	if args.file:
		with open(args.file, 'r') as fh:
			for n in fh.readlines():
				if args.debug:
					print('[DEBUG] Working on', n, file=sys.stderr)
				n = n.strip()
				if not re.match('\d{8}', n):
					continue
				get_lab_data(n, start, end)
	if args.pid:
		get_lab_data(args.pid, start, end)
