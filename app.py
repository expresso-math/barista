import os
from flask import Flask
from flask.ext import restful

app = Flask(__name__)
api = restful.Api(app)

class HelloWorld(restful.Resource):
    def get(self):
        return {'hello': 'world'}

api.add_resource(HelloWorld, '/')

class Presidents(restful.Resource):
    def get(self):
        return { '0': {'name': 'Washington, George' },
            '1': {'name': 'Adams, John' },
                '2': {'name': 'Jefferson, Thomas'} }

api.add_resource(Presidents, '/presidents')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
