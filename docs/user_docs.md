# Documentation for lisanalyze users (version 0.2.0)

## Introduction

lisanalyze is a software framework designed to automate the interpretation of
medical laboratory values. It relies heavily on the use of plugins for its heavy
lifting, including file reads. It is designed to take an SQLite database file
containing lab values as input, read and analyze its contents, then write the
results back to the file. Further operations can then be made on the file, for
example, using a notification service to push analysis results to clients.

## Usage

lisanalyze is invoked directly using Python, e.g.
"python3 lisanalyze.py 12345678.sqlite".

By design, each time lisanalyze is invoked, it makes one pass over the specified
file, then exits. The reason is mainly to avoid the complexities that come with
designing it as a daemon, such as signal handlers. What this means, practically,
is that you may wish to run it as a cron job (or alternatively, run it from a
shell script that runs as a cron job, or by using the prototype daemon.py file
included).

Since the analysis results are stored in the original SQLite file (to facilitate
further analysis if needed), the easiest way of accessing the results is
probably by using the DB Browser for SQLite. A prototype web interface
(lisanalyze-webui) is placed in its own repository, and is a Flask-powered
single-page application that displays the results.