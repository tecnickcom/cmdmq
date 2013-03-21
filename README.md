cmdMQ - README
====================

+ Name: cmdMQ

+ Version: 1.0.0

+ Release date: 2013-03-21

+ Author: Nicola Asuni

+ Copyright (2013-2013):

> > Fubra Limited  
> > Manor Coach House  
> > Church Hill  
> > Aldershot  
> > Hampshire  
> > GU12 4RQ  
> > <http://www.fubra.com>  
> > <support@fubra.com>  


SOFTWARE LICENSE:
-----------------

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.

See LICENSE.TXT file for more information.


DESCRIPTION:
------------

cmdMQ is a Free Open Source Software system to send commands to a remote computer using RabbitMQ queues.
This system uses an RPC (Remote Procedure Call) model to send commands from one note to another and get the results as JSON formatted data.
The RabbitMQ server (broker) can be installed on the sender computer node, the receiver computer node or another computer node.
The cmdMQ-Receiver runs and execute received commands as root. The only commands executed are the one specified on the configuration file using a regular expression syntax.



## cmdmq_sender ##

This section contains the software to be installed on the computer that sends commands.
Once configured, you can send a command to the queue using the following systax:

	cmdmq_sender.py -e "<command to be executed>"

For example:

	cmdmq_sender.py -e "ls -la"
	
This file must be marked as executable:

	chmod +x cmdmq_sender.py
	
Or called using python:

	python cmdmq_sender.py
		

This command returns a JSON object with the following information:
		
	{
		'ret':<ERROR_CODE>,
		'out':<COMMAND_OUTPUT>,
		'err':<ERROR_MESSAGE>
	}

## cmdmq_receiver ##

This section contains the software to be installed on the computer that receives and execute commands.
Once configured, this program can be started using one of the provided init scripts or manually:

	cmdmq_receiver.py



## INSTALLATION ##

### Install RabbitMQ on CentOS ###

Install EPEL, then:

 yum -y install openssl
 yum -y install erlang

Download the RabbitMQ RPM

 wget http://www.rabbitmq.com/releases/rabbitmq-server/v3.0.4/rabbitmq-server-3.0.4-1.noarch.rpm

Install RabbitMQ:

 rpm --import http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
 yum -y install rabbitmq-server-3.0.4-1.noarch.rpm

Edit the RabbitMQ main configuration file only if you want to use SSL

 nano /etc/rabbitmq/rabbitmq.config

 [
   {rabbit, [
      {ssl_listeners, [5671]},
      {ssl_options, [{cacertfile,"/etc/rabbitmq/ssl/cacert.pem"},
                     {certfile,"/etc/rabbitmq/ssl/cert.pem"},
                     {keyfile,"/etc/rabbitmq/ssl/key.pem"},
                     {verify,verify_none},
                     {fail_if_no_peer_cert,false}]}
    ]}
 ].

Copy the certificate files as indicated on the configuration file.
For the generation of the SSL certificates please consult:
http://www.rabbitmq.com/ssl.html

Start the service:

 service rabbitmq-server start

Start service at reboot:

 chkconfig rabbitmq-server on.

Use rabbitmqctl stop to stop the server.
Use rabbitmqctl status to check whether it is running.


### Install RabbitMQ on NAS4Free ###

Create the user "rabbitmq" with shell "nologin" and primary group "daemon".

To install additional packages we need to set the correct repository (discarded after reboot):

 setenv PACKAGESITE ftp://ftp.freebsd.org/pub/FreeBSD/ports/amd64/packages-9-current/Latest/

Install the following packages (used for the mesaging system):

 pkg_add -r openssl
 cp /usr/local/openssl/openssl.cnf.sample /usr/local/openssl/openssl.cnf
 
 pkg_add -r rabbitmq

Edit the /etc/rc.conf file and add the following lines:

 rabbitmq_enable="YES"
 rabbitmq_user="root"

Edit the RabbitMQ main configuration file only if you want to use SSL

 nano /etc/rabbitmq/rabbitmq.config

 [
   {rabbit, [
      {ssl_listeners, [5671]},
      {ssl_options, [{cacertfile,"/etc/rabbitmq/ssl/cacert.pem"},
                     {certfile,"/etc/rabbitmq/ssl/cert.pem"},
                     {keyfile,"/etc/rabbitmq/ssl/key.pem"},
                     {verify,verify_none},
                     {fail_if_no_peer_cert,false}]}
    ]}
 ].


Copy the configuration file:

 cp /etc/rabbitmq/rabbitmq.config /usr/local/etc/rabbitmq/rabbitmq.config 

Copy the certificate files as indicated on the configuration file.

To start the RabbitMQ server:
 
 /usr/local/etc/rc.d/rabbitmq start


### SSL TEST ###

In one terminal window execute the following command: 

 openssl s_server -accept 8443 -cert /etc/rabbitmq/server/cert.pem -key /etc/rabbitmq/server/key.pem -CAfile /etc/rabbitmq/testca/cacert.pem

In another terminal window execute

 openssl s_client -connect 127.0.0.1:8443 -cert /etc/rabbitmq/client/cert.pem -key /etc/rabbitmq/client/key.pem -CAfile /etc/rabbitmq/testca/cacert.pem

If the certificates and keys have been correctly created, an SSL connection establishment sequence will appear and the terminals will be linked.
Input from either terminal will appear on the other.


### Install cmdMQ on CentOS ###

Install python packages

	yum -y install python python-pip python-pika

Copy the cmdmq_receiver.py script to /usr/local/sbin/cmdmq_receiver.py and mark it as executable with
 
	chmod +x /usr/local/sbin/cmdmq_receiver.py

Copy the cmdmq_receiver.conf configuration file to /etc/cmdmq_receiver/default.conf and edit it.

Copy the cmdmq_receiver init script to /etc/init.d/cmdmq_receiver and mark it as executable with 

	chmod +x /etc/init.d/cmdmq_receiver


### Install cmdMQ on NAS4Free ###

To install additional packages we need to set the correct repository (discarded after reboot):

	setenv PACKAGESITE ftp://ftp.freebsd.org/pub/FreeBSD/ports/amd64/packages-9-current/Latest/

install the following packages (used for the mesaging system):

	pkg_add -r python
	pkg_add -r py27-utils
	pkg_add -r py27-pip
 
 reboot

	pip install http://pypi.python.org/packages/source/p/pika/pika-0.9.9.tar.gz

Copy the cmdmq_receiver.py script to /usr/local/sbin/cmdmq_receiver.py and mark it as executable with
 
	chmod +x /usr/local/sbin/cmdmq_receiver.py

Copy the cmdmq_receiver.conf configuration file to /etc/cmdmq_receiver/default.conf and edit it.

Copy the cmdmq_receiver_fsb init script to /usr/local/etc/rc.d/cmdmq_receiver and mark it as executable with 

	chmod +x /usr/local/etc/rc.d/cmdmq_receiver

Edit the /etc/rc.conf file and add the following lines to start the service at boot:

	cmdmq_receiver_enable="YES"
