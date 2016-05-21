#!/usr/bin/python
# -*- coding: utf-8 -*-

# Imports lab values from the EMR server and writes the data to an SQLite
# database using the patient's ID number as the filename.
# Rewritten for Python 3.

import sys
import urllib.request
import bs4
import sqlite3
import datetime
import argparse

# Creates our argument parser. This program takes only 1 argument, which is
# the patient's ID number (medical record number).
parser = argparse.ArgumentParser(description='Imports LIS data.')
parser.add_argument('--debug', action='store_true', help='print debug messages')
parser.add_argument('pid', type=str, help='patient record number')
args = parser.parse_args()

# Define the EMR service URL and appropriate header here
emr_service = 'http://hisweb.hosp.ncku/HISService/OPD/nckuHisWeb/EmrService.svc'
header_data = {'Content-Type': 'application/soap+xml; charset=utf-8','User-Agent':''}
if args.debug:
	print("[DEBUG] emr_service:" + emr_service)
	print("[DEBUG] header_data: " + header_data)

# Generates dates in the format YYYY/MM/DD, where the months and days are not
# zero-padded. For example: 2016/5/13. Generates today's date and the date last year
d = datetime.datetime.now()
today = '/'.join(map(str,[d.year,d.month,d.day]))
last_year = '/'.join(map(str,[d.year-1,d.month,d.day]))
if args.debug:
	print("[DEBUG] Today's date: " + today)
	print("[DEBUG] Last year's date: " + last_year)

# Try to use sqlite3 as database
dbname = args.pid + ".sqlite3"
conn = sqlite3.connect(dbname)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS patient_info (pid TEXT, name TEXT, gender TEXT, age INTEGER, ethnicity TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS lis_data (time TEXT, lab_item TEXT, site TEXT, lab_value TEXT, ref_low TEXT, ref_high TEXT, unit TEXT, method TEXT, comment TEXT, corrected INTEGER) UNIQUE (time, lab_item, site, corrected)")
#c.execute("CREATE TABLE IF NOT EXISTS analysis_results (time TEXT, result TEXT, reference TEXT, comment TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS db_info (lisanalyze_version TEXT, format_version TEXT)")
if args.debug:
	print("[DEBUG] Name of database: " + dbname)

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

def write_item(pid, lab_request_no, sample_site):
	'''Writes results to SQLite database'''
	if args.debug:
		print("[DEBUG] Currently in function write_item()...")
		print("[DEBUG] Building SOAP item request for request no. %s..." % lab_request_no)
	soap_env = build_soap_item(pid, lab_request_no)
	if args.debug:
		print("[DEBUG] Creating request URL...")
	url = urllib.request.Request(emrservice, soap_env, header_data)
	if args.debug:
		print("[DEBUG] Requesting data...")
	response = urllib.request.urlopen(url)

	# Throws an UnicodeEncodeError because some genius used <選> as a tag, we will replace it with <gibberish>
	response_utf8 = response.read().decode('utf-8').replace(u'\u9078', 'gibberish')
	if args.debug:
		print("[DEBUG] Parsing response data as XML...")
	soup = bs4.BeautifulSoup(response_utf8, 'xml')

	report_attrs = soup.find('retexaminerecord') # All reports under lab_request_no
	report_text = soup.find('retstatereportlist') # Will return results for text report

	if report_text:
		if args.debug:
			print("[DEBUG] Inserting text report into database...")
		c.execute("INSERT INTO lis_data (time, lab_item, site, lab_value) VALUES (?,?,?,?)", (report_attrs.execute_time.text, report_attrs.report_name.text, sample_site, report_text.report_text.text))
	else:
		report_num = soup.find_all('retnumreportlis')
		for report in report_num:
			if args.debug:
				print("[DEBUG] Inserting numerical report into database...")
			c.execute("INSERT INTO lis_data (time, lab_item, site, lab_value, ref_low, ref_high, unit, corrected) VALUES (?,?,?,?,?,?,?)", (report_attrs.execute_time.text, report_attrs.report_name.text, sample_site, report.text_value.text, report.ref_low.text, report.ref_high.text, report.unit.text, '0'))
	return False

def get_lab_data(pid, start='2010/1/1', end=today):
	'''Main request function. Start date (arbitrarily) hardcoded as 2010/1/1 .'''
	if args.debug:
		print("[DEBUG] Currently in function get_lab_data()...")
		print("[DEBUG] Building SOAP menu request...")
	soap_env = build_soap_menu(pid, start, end)
	if args.debug:
		print("[DEBUG] Creating request URL...")
	url = urllib.request.Request(emrservice, data=soap_env, headers=header_data)
	if args.debug:
		print("[DEBUG] Requesting data...")
	response = urllib.request.urlopen(url)
	if args.debug:
		print("[DEBUG] Parsing response data as XML...")
	soup = bs4.BeautifulSoup(response.read(), 'xml')

	# Get all reports ordered for this particular pid
	reports_all = soup.find_all('retexaminerecord')
	for report in reports_all:
		# u'\u78ba\u8a8d\u5831\u544a' == '確認報告'
		if report.status.text is not u'\u78ba\u8a8d\u5831\u544a':
			continue
		# sample_site refers to site of sample collection (e.g., blood). Note
		# this is in Chinese.
		sample_site = report.code_name.text
		if args.debug:
			print("[DEBUG] sample_site is: " + sample_site)
		# You know, this typo should've been corrected a long time ago...
		write_item(pid, report.requset_no.text, sample_site)
	if args.debug:
		print("[DEBUG] Committing changes.")
	conn.commit()
	if args.debug:
		print("[DEBUG] Closing connection.")
	conn.close()
	return False

get_lab_data(args.pid)