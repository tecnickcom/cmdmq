#!/usr/bin/env python

#==============================================================================+
# File name   : cmdmq_sender.py
# Begin       : 2013-03-06
# Last Update : 2013-04-03
# Version     : 1.0.0
#
# Description : RabbitMQ RPC client used to send commands to a remote
#               receiver.
#
#     Website : https://github.com/fubralimited/cmdmq
#
# Installation: Copy this script on the client node.
#               Set the execuable permission (chmod +x cmdmq_sender.py).
#               Call this script with the command to send as arguments.
#               For example: cmdmq_sender.py -e "ls -lah"
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
import uuid
import json
import logging
import ssl
import sys
import argparse
from ConfigParser import SafeConfigParser

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
 
# PROCESS THE COMMAND LINE ARGUMENTS

parser = argparse.ArgumentParser(description='Send a command to a remote receiver using RabbitMQ queue')
parser.add_argument('-c', '--config', action='store', nargs='?', const='cmdmq_sender.conf', default='/etc/cmdmq_sender/default.conf', type=file, required=False, help='configuration file - by default /etc/cmdmq_sender/default.conf, or local cmdmq_sender.conf if only -c is specified', dest='config_file')
parser.add_argument('-e', '--command', action='store', required=True, help='command to be sent enclosed by single or double quotes', dest='command')
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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# discard error messages
logging.basicConfig(filename='/dev/null', level=logging.CRITICAL)

class cmdRpcClient(object):

    def __init__(self):
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

			self.connection = pika.BlockingConnection(conn_params)
			self.channel = self.connection.channel()
			result = self.channel.queue_declare(exclusive=True)
			self.callback_queue = result.method.queue
			self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)
		except Exception,e:
			# print error message and exit
			print json.dumps({'ret':1, 'out':'', 'err':str(e)})
			exit(1)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, cmd):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
					routing_key=rmq_queue,
					properties=pika.BasicProperties(
						reply_to = self.callback_queue,
						correlation_id = self.corr_id,
						),
					body=str(cmd))
        while self.response is None:
            self.connection.process_data_events()
        return self.response

command_rpc = cmdRpcClient()

# send the command to the queue and wait for answer
response = command_rpc.call(args.command)

# output the response
print response

#==============================================================================+
# END OF FILE
#==============================================================================+
