#!/usr/bin/env python3
import os
import smtplib
import sys
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from functions.variables import TMP_PATH

COMMASPACE = ', ' # Character to separate email recipients

# Default SMTP server parameters
DEFAULT_SERVER = '192.168.0.60'
DEFAULT_SERVER_PORT =  8025
DEFAULT_SERVER_LOGIN = 'licensebot'
DEFAULT_SERVER_PASSWORD = 'CHANGE_ME'

def send_mail(send_from, send_to, subject, body, attachments=None,
	server=DEFAULT_SERVER,
	server_port=DEFAULT_SERVER_PORT,
	server_login=DEFAULT_SERVER_LOGIN,
	server_password=DEFAULT_SERVER_PASSWORD):
	"""
	Function that sends email using given relay mail servers

	Args:
		send_from: 		email sender
		send_to:		email recipients
		subject: 		email subject
		body:			content of the email message
		attachments: 	files to attach to the email message
		server: 		relay mail server 
		server_port: 	relay mail server SNMP port
		server_login:	relay mail server login (SNMP access)
		server_password: relay mail server password (SNMP access)

	Returns:
		None
	"""
	message = MIMEMultipart()

	message['Subject'] = subject
	message['To'] = COMMASPACE.join(send_to)
	message['From'] = send_from

	# Content of the mail message in HTML format
	message.attach(MIMEText(body, 'html'))

	# Add mail attachment if available
	if attachments != None:
		for file in attachments:
			try:
				with open(TMP_PATH + file, 'rb') as f:
					att = MIMEBase('application', 'octet-stream')
					att.set_payload(f.read())
				encoders.encode_base64(att)
				att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
				message.attach(att)
			except:
				print('Unable to open ' + file + ' - Error: ' + sys.exc_info()[0])
				raise

	# Sen email message
	try:
		with smtplib.SMTP(server, server_port) as server:
			server.ehlo()
			server.login(server_login, server_password)
			server.sendmail(send_from, send_to, message.as_string())
			server.close()
	except:
		print("Unable to send email. Error: ", sys.exc_info()[0])
		raise