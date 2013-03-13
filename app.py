import os, datetime, md5, time

from flask import Flask, request, make_response
from flask.ext import restful
from flask.ext.restful import fields

from werkzeug import secure_filename

from PIL import Image

import barista
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
        if session_id:
            session = barista.Session(session_id)
        else:
            session = barista.Session()
        return_data = session.get_session_json()
        return return_data, 201

class Expression(restful.Resource):
    def get(self, session_id):
        if Session.session_exists(session_id):
            new_expression = self.add_expression(session_id)
            return new_expression, 201
        else:
            return restful.abort(404)

    def add_expression(session_id):
        # Make (a relatively) unique identifier for this expression.
        now = datetime.datetime.now()
        m = md5.new(str(now))
        expression_id = m.hexdigest()

        # Add this expression to the session.
        sessions[session_id].append(expression_id)

        # Create the data for the expression
        expressions[expression_id] = {} # Empty for now, will be full soon enough.

        return {'expression_id': expression_id}
    # Make it a "Class method"
    add_expression = Callable(add_expression)

    def expression_exists(expression_id):
        return expression_id in expressions.keys()
    # Make it a "Class method"
    expression_exists = Callable(expression_exists)

    def has_image(expression_id):
        return expressions[expression_id].has_key('image')
    # Make it a "Class method"
    has_image = Callable(has_image)

class DrawnImage(restful.Resource):
    def get(self, expression_id):
        if Expression.expression_exists(expression_id):
            if Expression.has_image(expression_id):
                return DrawnImage.make_image_response(expression_id)
            else:
                return {'message':'Expression does not have an image set, yet.'}, 404
        else:
            return {'message':'Expression does not exist.'}, 404
    def post(self, expression_id):
        if Expression.expression_exists(expression_id):
            the_file = request.files['image'] # NOTE: Not sure if this will change client to client.
            DrawnImage.store_image(expression_id, the_file)
            time.sleep(2)
            return expression_id, 201
        else:
            return {'message':'Expression does not exist.'}, 404

    def store_image(expression_id, filedata):
        ## Store the image, for now in our list storage... this will become more robust, I presume.
        expressions[expression_id]['image'] = filedata.stream
    store_image = Callable(store_image)

    def make_image_response(expression_id):
        ## We have an image, so pull out the bits of it and make a response
        ## with the proper headers so that it downloads.
        image_stream = expressions[expression_id]['image']
        response = make_response(image_stream.getvalue())
        response.headers['Content-Type'] = 'image/png'
        response.headers['Content-Disposition'] = 'attachment; filename=img.png'
        return response
    make_image_response = Callable(make_image_response)


class SymbolSet(restful.Resource):
    def get(self, expression_id):
        symbol1 = { 'box': [12.0, 42.0, 100.0, 150.0], 'characters': { 'a' : 0.9, 'b': 0.5 } }
        symbol2 = { 'box': [152.0, 42.0, 100.0, 150.0], 'characters': { 'x' : 0.4, 'b': 0.1 } }
        time.sleep(2)
        symbol_set = { 'symbols': [symbol1, symbol2] }
        return symbol_set
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
api.add_resource(DrawnImage, '/expression/<string:expression_id>/image')
api.add_resource(SymbolSet, '/expression/<string:expression_id>/symbolset')
api.add_resource(EquationSet, '/expression/<string:expression_id>/equationset')
api.add_resource(Equation, '/expression/<string:expression_id>/equation')

# Run the app, getting the proper port from an ENV
# if set, otherwise defaulting to 5000.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)