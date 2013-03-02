import os
import datetime
from flask import Flask
from flask.ext import restful
import boto

import barista_utilities as util

app = Flask(__name__)
api = restful.Api(app)

sessions = []
images = []
sessions_images = {}

s3_conn = boto.connect_s3('AKIAJQTURA4O3CYWYPPA', 'fe3AKimi8nLhGiT5VRJbZvQ1KlqImzqkxUHzW02P')
drawing_bucket = s3_conn.get_bucket('expresso-drawings')
print str(drawing_bucket.list())

class SessionManagement(restful.Resource):
    def get(self, session_id=''):
		if session_id not in sessions:
			name = util.generate_session_name()
			while name in sessions:
				name = util.generate_session_name()
			sessions.append(name)
			sessions_images[name] = []
		else:
			name = session_id
		print "Session Name: " + str(name)
		print "All Sessions: " + str(sessions)
		return name

class Image(restful.Resource):
	def get(self, session_id):
		session_images = sessions_images[session_id]
		most_recent = session_images[len(session_images)-1]
		message = 'The most recent image, ' + str(most_recent) + ', belonging to ' + session_id
		return message
	def put(self, session_id):
		images.append('an image from ' + str(datetime.datetime.now()))
		print str(sessions_images)
		session_images = sessions_images[session_id]
		image_id = len(images)-1
		session_images.append(image_id)
		sessions_images[session_id] = session_images
		message = 'Added image ' + str(image_id) + ' to session ' + session_id 
		return message

# Set up resources in API.
api.add_resource(SessionManagement, '/','/<string:session_id>')
api.add_resource(Image, '/<string:session_id>/image')

# Run the app, getting the proper port from an ENV
# if set, otherwise defaulting to 5000.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)