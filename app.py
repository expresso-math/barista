# Python standard imports.
import os

# Flask imports
from flask import Flask, request, make_response, send_file
from flask.ext import restful
from flask.ext.restful import fields, reqparse

# Filename stuff import for Flask.
from werkzeug import secure_filename

# Imaging library imports.
from PIL import Image

# Barista imports.
import barista

app = Flask(__name__)
api = restful.Api(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

class Session(restful.Resource):
    def get(self, session_id=None):
        try:
            if session_id:
                session = barista.Session(session_id)
            else:
                session = barista.Session()
            return_data = session.get_session_json()
            return return_data, 201
        except StandardError, e:
            return { 'message': 'user-specified session does not exist' }, 404

class Expression(restful.Resource):
    def get(self, session_id):
        try:
            session = barista.Session(session_id)
            expression = barista.Expression()
            session.add_expression(expression)
            return { 'expression_identifier' : expression.expression_identifier }
        except StandardError, e:
            return { 'message': 'User-specified session does not exist.' }, 404

class DrawnImage(restful.Resource):
    def get(self, expression_id):
        expression = barista.Expression(expression_id)
        try:
            image = expression.get_image_for_return()
            return send_file(image, mimetype='image/png')
            
        except StandardError, e:
            return { 'message': 'Error retrieving image. Perhaps it doesn\'t exist?' }, 404
        
    def post(self, expression_id):
        try:
            image = request.files['image']
            expression = barista.Expression(expression_id)
            expression.add_image(image)
            return 201
        except StandardError, e:
            return { 'message': 'Error uploading image to specified expression.' }, 404


class SymbolSet(restful.Resource):
    def get(self, expression_id):
        symbol1 = { 'box': [12.0, 42.0, 100.0, 150.0], 'characters': { 'a' : 0.9, 'b': 0.5 } }
        symbol2 = { 'box': [152.0, 92.0, 200.0, 500.0], 'characters': { 'x' : 0.4, 'b': 0.1 } }
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

class Trainer(restful.Resource):
    
    parser = reqparse.RequestParser()
    parser.add_argument('symbol', type=str)

    def get(self):
        trainer = barista.TrainingEvent()
        return { 'symbol' : trainer.symbol }, 201
    def post(self):
        args = self.parser.parse_args()
        symbol = args['symbol']
        image = request.files['image']
        trainer = barista.TrainingEvent(symbol)
        trainer.add_image(image)
        trainer.send_data()

# Set up resources in API.
api.add_resource(Session, '/','/session', '/<string:session_id>', '/session/<string:session_id>')
api.add_resource(Expression, '/<string:session_id>/expression')
api.add_resource(DrawnImage, '/expression/<string:expression_id>/image')
api.add_resource(SymbolSet, '/expression/<string:expression_id>/symbolset')
api.add_resource(EquationSet, '/expression/<string:expression_id>/equationset')
api.add_resource(Equation, '/expression/<string:expression_id>/equation')
api.add_resource(Trainer, '/trainer')

# Run the app, getting the proper port from an ENV
# if set, otherwise defaulting to 5000.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
