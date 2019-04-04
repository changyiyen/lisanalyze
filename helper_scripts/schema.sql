-- Schema for creating a SQLite database for lisanalyze use
-- Version 0.1.0-20190314

CREATE TABLE IF NOT EXISTS lis_data (time TEXT, lab_item TEXT, site TEXT, lab_test_name TEXT, lab_value TEXT, ref_low TEXT, ref_high TEXT, unit TEXT, method TEXT, comment TEXT, corrected INTEGER);
CREATE TABLE IF NOT EXISTS analysis_results(time TEXT UNIQUE, result TEXT, analysis_time TEXT);
CREATE TABLE IF NOT EXISTS kv (key TEXT UNIQUE, value TEXT);