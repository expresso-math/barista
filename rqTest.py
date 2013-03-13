"""
A temporary python test script to make sure RQ is working across
EC2-Heroku borders.

Sends an image over to the EC2 instance by way of RQ
Daniel Guilak <daniel.guilak@gmail.com>
"""
# For RQ stuff:
from rq import Queue
from redis import Redis

import time
import cStringIO
import roaster

# Connect to Redis instance on EC2
redisConn = Redis("ec2-54-244-145-206.us-west-2.compute.amazonaws.com", 6379)
# Connect to the queue
q = Queue(connection=redisConn)  # no args implies the default queue

# New buffer
buff = cStringIO.StringIO()
# Opens temp.png and sets buffer to the beginning
buff.write(open('temp.png', 'rb').read())
buff.seek(0)

# Sends the buffer value to the queue and asks it to save
# the image on the EC2-side.
job = q.enqueue(roaster.saveImage, buff.getvalue())

# print job.result   # => None
# time.sleep(10)
# print job.result
# time.sleep(10)
# print job.result
