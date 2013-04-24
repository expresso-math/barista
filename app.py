# Python standard imports.
import os
import time

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
		session = barista.Session()
		if session_id:
			session.create_new(session_id)
		else:
			session.create_new()
		session.save_data()
		return session.compose_json()

class Expression(restful.Resource):
	def get(self, session_id):
		try:
			session = barista.Session()
			session.get_or_create(session_id)

			expression = barista.Expression()
			expression.create_new()

			print expression
			
			session.add_expression(expression)
			session.save_data()
			
			return { 'expression_identifier' : expression.expression_identifier }
		except Exception, e:
			print e
			return { 'message': 'User-specified session does not exist.' }, 404

class DrawnImage(restful.Resource):
	def get(self, expression_id):
		expression = barista.Expression()
		try:
			expression.load_existing(expression_id)
			image = expression.get_image_for_return()
			return send_file(image, mimetype='image/png')
			
		except Exception, e:
			return { 'message': 'Error retrieving image. Perhaps it doesn\'t exist?' }, 404
		
	def post(self, expression_id):
		try:
			image = request.files['image']
			expression = barista.Expression()
			expression.load_existing(expression_id)
			expression.add_image(image)
			expression.save_data()
			return 201
		except Exception, e:
			return { 'message': 'Error uploading image to specified expression.' }, 500


class SymbolSet(restful.Resource):
	def get(self, expression_id):
		expression = barista.Expression()
		try:
			expression.load_existing(expression_id)
			expression.identify_symbols()
			return expression.compose_json_symbols()
		except Exception, e:
			return { 'message': 'Error getting symbol set for specified expression. Could be a bad ID or no symbols.'}, 500

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

class Utility(restful.Resource):
	def get(self, method):
		u = barista.Utility()
		if method == 'load':
			print 'loading'
			u.load()
		elif method == 'train':
			print 'training'
			u.train()
		elif method == 'reset':
			print 'resetting'
			u.reset()
		else:
			print 'failing'
			return 500
		return 200

# Set up resources in API.
api.add_resource(Session, '/','/session', '/<string:session_id>', '/session/<string:session_id>')
api.add_resource(Expression, '/<string:session_id>/expression')
api.add_resource(DrawnImage, '/expression/<string:expression_id>/image')
api.add_resource(SymbolSet, '/expression/<string:expression_id>/symbolset')
api.add_resource(EquationSet, '/expression/<string:expression_id>/equationset')
api.add_resource(Equation, '/expression/<string:expression_id>/equation')
api.add_resource(Trainer, '/trainer')
api.add_resource(Utility, '/utility/<string:method>')

# Run the app, getting the proper port from an ENV
# if set, otherwise defaulting to 5000.
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port, debug=True)
