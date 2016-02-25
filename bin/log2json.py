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
	def __init__( self ):
		self.file_types = ( 'ftp', 'gridftp', 'apache', 'gridftp-anon' )
		self.my_options = dict()
		try:
			opts, args = getopt.getopt( sys.argv[1:], "t:i:o:", ['type=', 'input=', 'output='] )
		except getopt.GetoptError as err:
			print str(err)
			self.usage()
			sys.exit( 2 )
		self.my_options['type'] = None
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
			elif ( opt in ('-o', '--output') ):
				self.my_options['output'] = arg
			else:
				assert False, 'Unknown option'

	def options_list( self ):
		return (self.my_options['type'], self.my_options['input'], self.my_options['output'] )

	def options_dict( self ):
		return self.my_options

	def option( self, option ):
		if ( self.my_options.has_key( option ) ):
			return self.my_options[option]
		else:
			return None

	def usage( self ):
		print "USAGE:"

class GenericLog:
	def __init__( self, log_line ):
		self.line = log_line
		self.log_dict = dict()
		socket.gethostbyname( socket.gethostname())

	def parse( self ):
		# This is a placeholder
		True

	def to_json( self ):
		self.json = json.dumps( self.log_dict )

	def dump_json( self, output_fd=None ):
		if ( self.json and len( self.json ) > 2 ):
			if ( output_fd ):
				output_fd.write( self.json + '\n' )
			else:
				print self.json

	def string_to_datetime( self, date_string ):
		dt = datetime.datetime.strptime( date_string, '%d/%b/%Y:%H:%M:%S' )
		#
		# Return time/date in ISO 8601 format, minus the normal punctuation. Since Apache does not include
		# microseconds, just fill in zeroes for that data.
		#
		return string.translate( dt.isoformat( ' ' ), None, '- :' ) + '.000000'

	def dump( self ):
		print
		print "log line: '" + self.line
		print "values:", self.log_dict
		print "json:", self.json

class GridftpLog( GenericLog ):
	def __init__( self, log_line ):
		GenericLog.__init__(  self, log_line )
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

class ApacheAccessLog( GenericLog ):
	def __init__( self, log_line ):
		GenericLog.__init__( self, log_line )
		self.my_IP = socket.gethostbyname(socket.gethostname())
	
	def parse( self ):
		fields = re.search( '([^ ]*) ([^ ]*) ([^ ]*) \[([^ ]*) ([^\]]*)\] "([^ ]*) ([^ ]*) ([^"]*)" ([0-9]*) ([0-9]*)(.*)', self.line )
		if ( fields ):
			vals = fields.groups()
			self.log_dict['DEST'] = name2IP( vals[0] )
			self.log_dict['HOST'] = self.my_IP
			self.log_dict['START'] = self.string_to_datetime( vals[3] )
			self.log_dict['STOP'] = ''
			self.log_dict['PATH'] = vals[6]
			self.log_dict['PROTOCOL'] = 'ftp'
			self.log_dict['BYTES'] = vals[9]

def name2IP( name ):
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

try:
	opts = ParseOptions()
except:
	print "quitting"
	sys.exit( 2 )

file_type = opts.option( 'type' )
try:
	fd = open( opts.option( 'input' ) )
except:
	print "*** Failed to open input file '" + opts.option( 'input' ) + "' ***"
	sys.exit( 3 )
if ( opts.option( 'output' ) ):
	try:
		out_fd = open( opts.option( 'output' ), 'w' )
	except:
		print "*** Failed to open output file '" + opts.option( 'output' ) + "' ***"
		sys.exit( 3 )
else:
	out_fd = None

for line in fd.readlines():
	if ( file_type == 'apache' ):
		log_line = ApacheAccessLog( line )
	elif ( file_type == 'gridftp' ):
		log_line = GridftpLog( line )
	elif ( file_type == 'gridftp-anon' ):
		log_line = None
	log_line.parse()
	log_line.to_json()
	log_line.dump_json( output_fd=out_fd )
	#log_line.dump()
