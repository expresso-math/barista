import os
import datetime
from flask import Flask
from flask.ext import restful

import barista_utilities as util

app = Flask(__name__)
api = restful.Api(app)

sessions = []
sessions_images = {}

AWS_PUBLIC_KEY = 'AKIAJQTURA4O3CYWYPPA'
AWS_SECRET_KEY = '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'

class Session(restful.Resource):
    def get(self, session_id=''):
        
        # Setup for the return.
        return_data = { 'session_name' : '', 'images': [] }
        name = ''

        if session_id:
            # A session ID has been defined.
            if session_id not in sessions:
                # The defined session ID does not exist as a current session,
                # so we make one given the session name.
                name = session_id
                self.add_session(name)
            else:
                # The defined session ID does exist already, so we just forward
                # this to the next step.
                name = session_id
        else:
            # No session ID was defined, so we make one up for the client.
            name = util.generate_session_name()
            while name in sessions:
                name = util.generate_session_name()
            self.add_session(name)

        return_data['session_name'] = name
        return_data['images'] = sessions_images[name]

        print "Session_id passed in is '" + session_id + "'."
        print "Sessions stored are " + str(sessions) + "."

        return return_data

    def add_session(self, session_id):
        sessions.append(session_id)
        sessions_images[session_id] = []

class Expression(restful.Resource):
    def get(self, session_id):
        return 'this is new expression belonging to ' + session_id + '!!'

class Image(restful.Resource):
    def get(self, session_id):
        return 'you got an image!'
    def post(self, session_id):
        return 'you posted an image!'

class SymbolSet(restful.Resource):
    def get(self, expression_id):
        return 'you got a symbol set!'
    def post(self, expression_id):
        return 'you set a symbol set!'

class EquationSet(restful.Resource):
    def get(self, expression_id):
        return 'you got a equation set!'
    def post(self, expression_id):
        return 'you set a equation set!'

class Equation(restful.Resource):
    def get(self, expression_id):
        return 'this is an equation!'

# Set up resources in API.
api.add_resource(Session, '/','/session', '/<string:session_id>', '/session/<string:session_id>')
api.add_resource(Expression, '/<string:session_id>/expression')
api.add_resource(Image, '/expression/<string:expression_id>/image')
api.add_resource(SymbolSet, '/expression/<string:expression_id>/symbolset')
api.add_resource(EquationSet, '/expression/<string:expression_id>/equationset')
api.add_resource(Equation, '/expression/<string:expression_id>/equation')

# Run the app, getting the proper port from an ENV
# if set, otherwise defaulting to 5000.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)