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
import string
import getopt

class JsonFiles:
	def __init__( self ):
		self.json_data = list()
		self.aggregate_data = dict()
		self.json = None

	def ingest( self, files ):
		#
		# "files" is a list of files from which to read JSON transfer log data
		#
		for file in files:
			try:
				fd = open( file, 'r' )
			except:
				print "*** Failed to open JSON log file '" + file + "' ***"
				continue
			log_dict = json.load( fd )
			self.json_data.append( log_dict )

	def aggregate( self ):
		for data_set in self.json_data:
			jf = data_set['files']
			for entry in jf:
				if ( entry.has_key( 'SOURCE' ) and entry.has_key( 'DEST' ) and entry.has_key( 'BYTES' ) ):
					source = entry['SOURCE']
					dest = entry['DEST']
					xfer_bytes = int(entry['BYTES'])
					xfer_start_time = entry['START']
					xfer_stop_time = entry['STOP']
					xfer_key = source + ',' + dest
					if ( not self.aggregate_data.has_key( xfer_key ) ):
						self.aggregate_data[xfer_key] = dict()
						self.aggregate_data[xfer_key]['BYTES'] = 0
						self.aggregate_data[xfer_key]['TIME'] = 0
						self.aggregate_data[xfer_key]['SOURCE'] = source
						self.aggregate_data[xfer_key]['DEST'] = dest
					self.aggregate_data[xfer_key]['BYTES'] += xfer_bytes
					self.aggregate_data[xfer_key]['TIME'] += self.elapsed_time( xfer_start_time, xfer_stop_time )

	def to_json( self ):
		#
		# Convert the parsed log file entry to JSON
		#
		self.records = { 'RECORDS': self.aggregate_data }
		self.json = json.dumps( self.records )

	def dump_json( self, output_fd=None ):
		#
		# Write the JSON code to STDOUT, or an open file descriptor, if one is provided
		#
		if ( not self.json ):
			self.to_json()

		if ( self.json and len( self.json ) > 2 ):
			if ( output_fd ):
				output_fd.write( self.json + '\n' )
			else:
				print self.json

	def elapsed_time( self, start, end ):
		#
		# Start and end are strings in ISO 6081 time format (yyyymmddHHMMSS.UUUUUU)
		#
		try:
			start_time = datetime.datetime.strptime( start, "%Y%m%d%H%M%S.%f" )
			end_time = datetime.datetime.strptime( end, "%Y%m%d%H%M%S.%f" )
			et = end_time - start_time
		except:
			et = 0
		return (et.days * 86400 + et.seconds)

	def aggregate_dump( self ):
		print "json aggregate data:"
		print self.aggregate_data

	def dump( self ):
		print "json_data:"
		print self.json_data

#
# MAIN PROGRAM
#
j = JsonFiles()
#j.ingest( ('gftp.json',) )
j.ingest( ('kip_gridftp.json',) )
j.aggregate()
j.dump_json()
