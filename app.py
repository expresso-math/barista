import os, datetime, md5

from flask import Flask, request
from flask.ext import restful
from flask.ext.restful import fields

from werkzeug import secure_filename

# from PIL import Image

import barista_utilities as util

UPLOAD_FOLDER = './uploaded_images'
ALLOWED_EXTENSIONS = set(['png'])

app = Flask(__name__)
api = restful.Api(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Temporary runtime variables for data. Will be removed once we come up
# with a more permanent data store.
sessions = {}
expressions = {}

AWS_PUBLIC_KEY = 'AKIAJQTURA4O3CYWYPPA'
AWS_SECRET_KEY = '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'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

class Callable:
    def __init__(self, a_callable):
        self.__call__ = a_callable

class Session(restful.Resource):
    def get(self, session_id=''):
        
        # Setup for the return.
        return_data = { 'session_name' : '', 'expressions': [] }
        name = ''

        if session_id:
            # A session ID has been defined.
            if not Session.session_exists(session_id):
                # The defined session ID does not exist as a current session,
                # so we make one given the session name.
                name = session_id
                Session.add_session(name)
            else:
                # The defined session ID does exist already, so we just forward
                # this to the next step.
                name = session_id
        else:
            # No session ID was defined, so we make one up for the client.
            name = util.generate_session_name()
            while Session.session_exists(name):
                name = util.generate_session_name()
            Session.add_session(name)

        return_data['session_name'] = name
        return_data['expressions'] = sessions[name]

        return return_data

    def add_session(session_id):
        sessions[session_id] = []
    # Make it a "Class method"
    add_session = Callable(add_session)

    def session_exists(session_id):
        return session_id in sessions
    # Make it a "Class method"
    session_exists = Callable(session_exists)

class Expression(restful.Resource):
    def get(self, session_id):
        if Session.session_exists(session_id):
            new_expression = self.add_expression(session_id)
            return new_expression
        else:
            return restful.abort(404)

    def add_expression(session_id):
        # Make (a relatively) unique identifier for this expression.
        now = datetime.datetime.now()
        m = md5.new(str(now))
        expression_id = m.hexdigest()

        # Add this expression to the session.
        sessions[session_id].append(expression_id)
        print str(sessions[session_id])

        # Create the data for the expression
        expressions[expression_id] = [] # Empty for now, will be full soon enough.

        return expression_id
    # Make it a "Class method"
    add_expression = Callable(add_expression)

class Image(restful.Resource):
    def get(self, expression_id):
        return 'This is the image for ' + expression_id + '.'
    def post(self, expression_id):
        the_file = request.files['filedata'] # NOTE: Not sure if this will change client to client.
        if the_file and allowed_file(the_file.filename):
            filename = secure_filename(the_file.filename)
            filenameonly, extension = os.path.splitext(filename)
            savename = expression_id + extension
            the_file.save(os.path.join(app.config['UPLOAD_FOLDER'], savename))
        print 'Posting the given image into ' + expression_id + '\'s data.'
        return expression_id + '.png Saved.', 201

class SymbolSet(restful.Resource):
    def get(self, expression_id):
        return 'you got a symbol set!'
    def put(self, expression_id):
        return 'you set a symbol set!'

class EquationSet(restful.Resource):
    def get(self, expression_id):
        return 'you got a equation set!'
    def put(self, expression_id):
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