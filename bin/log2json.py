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

class ParseOptions:
	#
	# Class to handle command-line argument processing.
	#
	def __init__( self ):
		self.my_options = dict()
		self.input_fd = sys.stdin
		self.output_fd = sys.stdout
		self.file_types = ( 'ftp', 'gridftp', 'apache', 'gridftp-anon' )
		try:
			opts, args = getopt.getopt( sys.argv[1:], "t:i:o:", ['type=', 'input=', 'output='] )
		except getopt.GetoptError as err:
			print str(err)
			self.usage()
			sys.exit( 2 )
		self.my_options['type'] = 'gridftp'
		self.my_options['input'] = None
		self.my_options['output'] = None
		for opt, arg in opts:
			if ( opt in ('-t', '--type' ) ):
				if ( arg not in self.file_types ):
					print "*** Unknown file type: '" + arg + "' ***"
				else:
					self.my_options['type'] = arg
			elif( opt in ('-i', '--input') ):
				self.my_options['input'] = arg
				try:
					self.input_fd = open( arg, 'r' )
				except:
					print "*** Failed to open input file '" + arg + "' ***"
					sys.exit( 2 )
			elif ( opt in ('-o', '--output') ):
				self.my_options['output'] = arg
				try:
					self.output_fd = open( arg, 'w' )
				except:
					print "*** Failed to open output file '" + arg + "' ***"
					sys.exit( 2 )
			else:
				assert False, 'Unknown option'

	def options_list( self ):
		#
		# Return all options as a Python list
		#
		return (self.my_options['type'], self.my_options['input'], self.my_options['output'] )

	def options_dict( self ):
		#
		# Return all options as a Python dictionary
		#
		return self.my_options

	def option( self, option ):
		#
		# Return the named option as a string, or "None" if the option
		# doesn't exist.
		#
		if ( self.my_options.has_key( option ) ):
			return self.my_options[option]
		else:
			return None

	def usage( self ):
		print 'USAGE:'
		print sys.argv[0] + ' -t <type> [--type=<type>] -i <in_file> [--input=in_file] -o <out_file> [--output=<out_file>]'
		print '               Where:'
		print '                      <type> is one of gridftp, apache, ftp'
		print '                      <in_file> is the path/name of the log file to process (default stdin)'
		print '                      <out_file> is the path/name of the file in which to write the JSON code (default stdout)'
		print

class JsonFilesLog:
	def __init__( self ):
		self.json_container = { 'files': list() }
		self.json = None

	def add_log_line( self, line_dict ):
		self.json_container['files'].append( line_dict )

	def to_json( self ):
		#
		# Convert the parsed log file entry to JSON
		#
		self.json = json.dumps( self.json_container, indent=2 )

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

	def dump( self ):
		print "json_container:"
		print self.json_container

class GenericLogLine:
	#
	# Class GenericLogLine implements the basic class/method structure for parsing different
	# log file formats. It is not intended to be instantiated directly.
	#
	def __init__( self, log_line ):
		self.line = log_line
		self.log_dict = dict()
		try:
			socket.gethostbyname( socket.gethostname())
		except:
			print "Can't get my own IP address! " + socket.gethostname()

	def parse( self ):
		# This is a placeholder for the actual log file parsing code
		True

	def to_json( self ):
		#
		# Convert the parsed log file entry to JSON
		#
		self.json = json.dumps( self.log_dict )

	def get_dict( self ):
		return self.log_dict

	def dump_json( self, output_fd=None ):
		#
		# Write the JSON code to STDOUT, or an open file descriptor, if one is provided
		#
		if ( self.json and len( self.json ) > 2 ):
			if ( output_fd ):
				output_fd.write( self.json + '\n' )
			else:
				print self.json

	def apache_time_to_datetime( self, date_string ):
		#
		# Convert an Apache access log file time/date value to ISO 8601 format. Since Apache
		# doesn't include microseconds, fill that field in as a static "0" value
		#
		dt = datetime.datetime.strptime( date_string, '%d/%b/%Y:%H:%M:%S' )
		return string.translate( dt.isoformat( ' ' ), None, '- :' ) + '.000000'

	def dump( self ):
		#
		# A simple dump to STDOUT routine for debugging
		#
		print
		print "log line: '" + self.line
		print "values:", self.log_dict
		print "json:", self.json

class GridftpLog( GenericLogLine ):
	#
	# Process a single Gridftp log file line
	#
	def __init__( self, log_line ):
		# Call the superclass constructor
		GenericLogLine.__init__(  self, log_line )
		# keywords{} maps log file keywords to standard keywords used in the JSON file
		self.keywords = {'START': 'START', 'DATE': 'STOP', 'NBYTES': 'BYTES', 'DEST': 'DEST', 'HOST': 'SOURCE', 'TYPE': 'TYPE', 'CODE': 'CODE'}
		self.log_dict = dict()

	def parse( self ):
		fields = self.line.split()
		key_vals = dict()
		for f in fields:
			try:
				k_v = f.split( '=' )
			except:
				continue
			if ( self.keywords.has_key( k_v[0] ) ):
				self.log_dict[self.keywords[k_v[0]]] = string.translate( k_v[1], None, '[]' )
		#
		# Gridftp logs on both the client and server, so reverse the "HOST" and "DEST"
		# based on the "TYPE" field
		#
		if ( self.log_dict.has_key( 'TYPE' ) and self.log_dict['TYPE'] == 'STOR' ):
			tmp = self.log_dict['DEST']
			self.log_dict['DEST'] = self.log_dict['SOURCE']
			self.log_dict['SOURCE'] = tmp
		#
		# Convert any hostnames/FQDNs to IP
		#
		if ( self.log_dict.has_key( 'SOURCE' ) ):
			self.log_dict['SOURCE'] = name2IP( self.log_dict['SOURCE'] )
		if ( self.log_dict.has_key( 'DEST' ) ):
			self.log_dict['DEST'] = name2IP( self.log_dict['DEST'] )

class ApacheAccessLogLine( GenericLogLine ):
	#
	# Process a single Apache access log file line
	#
	def __init__( self, log_line ):
		# Call the superclass constructor
		GenericLogLine.__init__( self, log_line )
		self.my_IP = socket.gethostbyname(socket.gethostname())
	
	def parse( self ):
		fields = re.search( '([^ ]*) ([^ ]*) ([^ ]*) \[([^ ]*) ([^\]]*)\] "([^ ]*) ([^ ]*) ([^"]*)" ([0-9]*) ([0-9]*)(.*)', self.line )
		if ( fields ):
			vals = fields.groups()
			self.log_dict['DEST'] = name2IP( vals[0] )
			self.log_dict['HOST'] = self.my_IP
			self.log_dict['START'] = self.apache_time_to_datetime( vals[3] )
			self.log_dict['STOP'] = ''
			self.log_dict['PATH'] = vals[6]
			self.log_dict['PROTOCOL'] = 'ftp'
			self.log_dict['BYTES'] = vals[9]

def name2IP( name ):
	#
	# Accept a source/destination host string and convert it to an IP address. If the incoming
	# value is already an IP address, simply return it unchanged.
	#
	# Check to see if this is already an IP address
	#
	try:
		socket.inet_aton( name )
		return name
	except:
		#
		# Not an IP address, see if the name resolves
		#
		try:
			ip = socket.gethostbyname( name )
			return ip
		except:
			return name

#
# MAIN PROGRAM
#
try:
	opts = ParseOptions()
except:
	sys.exit( 2 )

file_type = opts.option( 'type' )

json_files = JsonFilesLog()

for line in opts.input_fd.readlines():
	if ( file_type == 'apache' ):
		log_line = ApacheAccessLogLine( line )
	elif ( file_type == 'gridftp' ):
		log_line = GridftpLog( line )
	elif ( file_type == 'gridftp-anon' ):
		log_line = None
	log_line.parse()
	json_files.add_log_line( log_line.get_dict() )
json_files.dump_json( output_fd=opts.option( 'output_fd' ))
