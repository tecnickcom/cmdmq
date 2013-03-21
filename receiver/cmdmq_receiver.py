#!/usr/bin/env python

#==============================================================================+
# File name   : cmdmq_receiver.py
# Begin       : 2013-03-06
# Last Update : 2013-03-21
# Version     : 1.0.0
#
# Description : RabbitMQ RPC server used to receive and execute ZFS commands.
#
# Installation: Copy this script on the NAS4Free node.
#               Set the execuable permission (chmod +x cmdmq_receiver.py).
#               Start the RabbitMQ server.
#               Execute this script.
#
# Author: Nicola Asuni
#
# (c) Copyright:
#               Fubra Limited
#               Manor Coach House
#               Church Hill
#               Aldershot
#               Hampshire
#               GU12 4RQ
#               UK
#               http://www.fubra.com
#               support@fubra.com
#
# License:
#    Copyright (C) 2013-2013 Fubra Limited
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    See LICENSE.TXT file for more information.
#==============================================================================+

import pika
import subprocess
import json
import time
import logging
import re
import ssl
import os
import sys
import argparse
from ConfigParser import SafeConfigParser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# This script must be executed by root
if not os.geteuid()==0:
	sys.exit("\n*** Only root can run this script ***\n")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# PROCESS THE COMMAND LINE ARGUMENTS

parser = argparse.ArgumentParser(description='Listen to a RabbitMQ queue for commands to be executed')
parser.add_argument('-c', '--config', action='store', nargs='?', const='cmdmq_receiver.conf', default='/etc/cmdmq_receiver/default.conf', type=file, required=False, help='configuration file - by default /etc/cmdmq_receiver/default.conf, or local cmdmq_receiver.conf if only -c is specified', dest='config_file')
args = parser.parse_args()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# CONFIGURATION PARAMETERS

parser = SafeConfigParser()
parser.readfp(args.config_file)

# RabbitMQ server IP address
rmq_ip = parser.get('general', 'rmq_ip')

# RabbitMQ server port number
rmq_port = parser.getint('general', 'rmq_port')

# queue name (storage node hostname)
rmq_queue = parser.get('general', 'rmq_queue')

# RabbitMQ authentication
rmq_username = parser.get('general', 'rmq_username')
rmq_password = parser.get('general', 'rmq_password')

# SSL options
rmq_ssl = parser.getboolean('general', 'rmq_ssl')
rmq_ssl_options = parser.get('general', 'rmq_ssl_options')

# number of seconds to wait for restart after general error
retry_time = parser.getint('general', 'retry_time')

# log file name
log_file_name = parser.get('general', 'log_file')

# log file
log_file = open(log_file_name, "a")

# create a list of patterns for allowed commands
allowed_cmds = parser.get('filter', 'allowed_cmds').split(',')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# redirect stdout to a log file
old_stdout = sys.stdout
sys.stdout = log_file

# log only critical error messages
logging.basicConfig(filename=log_file_name, level=logging.ERROR)

# function to print a log message on stdout
def log_message(message):
	now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
	print "%s - %s" % (now, message)
	sys.stdout.flush()

log_message('*** - PROGRAM STARTED - trying to connect')

while True:
	try:
		conn_credentials = pika.PlainCredentials(rmq_username, rmq_password)
		conn_params = pika.ConnectionParameters(
			host=rmq_ip,
			port=rmq_port,
			virtual_host=None,
			credentials=conn_credentials,
			channel_max=None,
			frame_max=None,
			heartbeat_interval=None,
			ssl=rmq_ssl,
			ssl_options=rmq_ssl_options,
			connection_attempts=5,
			retry_delay=2,
			socket_timeout=None,
			locale=None,
			backpressure_detection=None)

		connection = pika.BlockingConnection(conn_params)
		channel = connection.channel()
		channel.queue_declare(queue=rmq_queue)

		def on_request(ch, method, props, body):

			# acknowledge command receipt
			ch.basic_ack(delivery_tag=method.delivery_tag)

			log_message('[R] - Received command: ' + body)

			# check for invalid characters
			match = re.search(r'[&><|`]', body)
			if match is not None:
				# return error message
				log_message('[E] - Invalid character on command: ' + body)
				retval = json.dumps({'ret':1, 'out':'', 'err':'invalid character on command'})
			else:
				# initialize empty command
				cmd = ''
				# filter allowed commands
				for recmd in allowed_cmds:
					p = re.compile(recmd)
					match = p.search(body)
					if match is not None:
						# command is valid, exit the loop
						cmd = body
						break

				if cmd:
					# execute the requested command
					process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					# wait for the process to terminate and store stdout, stderr and error code
					out, err = process.communicate()
					errcode = process.returncode
					# encode answer as json object
					retval = json.dumps({'ret':errcode, 'out':out, 'err':err})
					log_message('[X] - Command executed: ' + cmd)
				else:
					# return error message
					retval = json.dumps({'ret':1, 'out':'', 'err':'unrecognized command'})
					log_message('[E] - Unrecognized command: ' + body)

			# send results back
			ch.basic_publish(exchange='', routing_key=props.reply_to, properties=pika.BasicProperties(correlation_id=props.correlation_id), body=retval)

		channel.basic_qos(prefetch_count=1)
		channel.basic_consume(on_request, queue=rmq_queue)

		log_message('[S] - Awaiting remote command requests')

		channel.start_consuming()

	except KeyboardInterrupt:
		try:
			channel.stop_consuming()
			connection.close()
		except:
			pass
		log_message('[E] - Program manually interrupted')
		sys.stdout = old_stdout
		log_file.close()
		exit(1)
	except Exception,e:
		try:
			# retry to connect
			log_message('[E] - ' + str(e) + ' - restart in ' + str(retry_time) + ' secs')
			try:
				channel.stop_consuming()
				connection.close()
			except:
				pass
			time.sleep(retry_time)
		except KeyboardInterrupt:
			try:
				channel.stop_consuming()
				connection.close()
			except:
				pass
			log_message('[E] - Program manually interrupted')
			sys.stdout = old_stdout
			log_file.close()
			exit(1)

#==============================================================================+
# END OF FILE
#==============================================================================+
