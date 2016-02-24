#!/bin/env python

#
# A simple Python program that ingests an Apache access log, picks out interesting data, and outputs each line
# in JSON format.
#
import os
import sys
import re
import datetime
import time
import json
import socket

class FtpLog:
	def __init__( self, log_line ):
		self.line = log_line
		self.log_dict = dict()
		self.my_IP = socket.gethostbyname(socket.gethostname())
	
	def parse( self ):
		fields = re.search( '([^ ]*) ([^ ]*) ([^ ]*) \[([^ ]*) ([^\]]*)\] "([^ ]*) ([^ ]*) ([^"]*)" ([0-9]*) ([0-9]*)(.*)', self.line )
		if ( fields ):
			vals = fields.groups()
			self.log_dict['DEST'] = vals[0]
			self.log_dict['SOURCE'] = self.my_IP
			self.log_dict['START'] = self.string_to_datetime( vals[3] )
			self.log_dict['STOP'] = ''
			self.log_dict['PATH'] = vals[6]
			self.log_dict['PROTOCOL'] = 'ftp'
			self.log_dict['BYTES'] = vals[9]

	def string_to_datetime( self, date_string ):
		dt = datetime.datetime.strptime( date_string, '%d/%b/%Y:%H:%M:%S' )
		return dt.strftime( "%m/%d/%Y %H:%M:%S" )

	def to_json( self ):
		self.json = json.dumps( self.log_dict )

	def dump_json( self ):
		if ( self.json and len( self.json ) > 2 ):
			print self.json

	def dump( self ):
		print
		print "log line: '" + self.line
		print "values:", self.log_dict
		print "json:", self.json

file_name = 'APS_Apache.log'
fd = open( file_name )
for line in fd.readlines():
	l = FtpLog( line )
	l.parse()
	l.to_json()
	l.dump_json()
