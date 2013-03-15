# Socket, so we can get local hostname.
import socket

hostname = socket.gethostname()
#print hostname
local = hostname == 'Plutonium'
#print local

settings = {}

## Redis Settings
if local:
	settings['redis_hostname'] = 'localhost'
	settings['redis_port'] = 6379
	settings['redis_db'] = 1
else:
	settings['redis_hostname'] = 'ec2-54-244-145-206.us-west-2.compute.amazonaws.com'
	settings['redis_port'] = 6379
	settings['redis_db'] = 1