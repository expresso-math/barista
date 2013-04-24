### This is a restructuring of Barista and its classes.
### This is for the sake of clarity and making sense of everything.
### One big object of this is to toss a lot of functionality into methods 
### instead of doing everything in constructors. Permanence should not be
### automatic -- Barista should require committing of changes.

# Python standard imports for use in this module.
import datetime, random, cStringIO, time

# Redis, RedisQ
import redis, rq

# Settings
from barista_settings import settings

# Import roaster, for RQ-mirroring ability.
import roaster

import ascii

# Set up Redis connections.
rq_connection = redis.Redis(host=settings['rq_hostname'], port=settings['rq_port'], db=settings['rq_db'])
r = redis.StrictRedis(host=settings['redis_hostname'], port=settings['redis_port'], db=settings['redis_db'])

# Set up RQ.
q = rq.Queue(connection=rq_connection)

# This should probably only get called once or so. We're making sure the keys
# for expression_identifier_ids and symbol_identifier_ids exist so we can get
# unique incremented values.
if not r.exists('expression_identifier_ids'):
	r.set('expression_identifier_ids', 1)
if not r.exists('symbol_identifier_ids'):
	r.set('symbol_identifier_ids', 1)


# Fun method to get fancy unique session identifers.
def get_unique_session_identifier():
	adjectives  = ['iced', 'tall', 'short', 'grande', 'nonfat', 'skinny', 'almond', 'soy', 'vanilla', 'extra-hot', 'breve', 'cinnamon', 'dry']
	nouns       = ['mocha', 'latte', 'cappuccino', 'americano', 'steamer', 'macchiato']
	adjective = adjectives[random.randint(0,len(adjectives)-1)]
	noun      = nouns[random.randint(0,len(nouns)-1)]
	number    = str(random.randint(0, 9))+str(random.randint(0, 9))+str(random.randint(0, 9))+str(random.randint(0, 9))
	name = '' + str(adjective) + '-' + str(noun) + '-' + str(number) + ''
	while r.exists(name):
		adjective = adjectives[random.randint(0,len(adjectives)-1)]
		noun      = nouns[random.randint(0,len(nouns)-1)]
		number    = str(random.randint(0, 9))+str(random.randint(0, 9))+str(random.randint(0, 9))+str(random.randint(0, 9))
		name = '' + str(adjective) + '-' + str(noun) + '-' + str(number) + ''
	return name


## Data classes

### Session. Pretty straightforward.

class Session:
	""" 
		Class representing a session. Holds an identifier
		associated with this session and defines several
		helpful methods.

		REDIS DATA:
		key     --> "session:<self.session_identifier>"
		value   --> [list of expression_identifier(s)]
	"""

	def __init__(self):
		""" Create a new empty session object. """
		self.session_identifier = ''
		self.expressions = []
		self.dirty = True

	def create_new(self, custom_identifier=None):
		""" Make this object into a new Session as far as the database is concerned. """
		if custom_identifier is None:
			self.session_identifier = get_unique_session_identifier()
		else:
			self.session_identifier = custom_identifier
		self.expressions = []
		self.dirty = True

	def load_existing(self, existing_identifier):
		""" Load data from an existing persistence of a Session object. """
		if(r.exists('session:' + existing_identifier)):
			self.session_identifier = existing_identifier
			self.expressions = r.lrange('session:' + self.session_identifier, 0, -1)
		else:
			raise Exception('Session does not exist.')
		self.dirty = False

	def get_or_create(self, existing_identifier):
		""" Get data from an existing persistence of a Session object, or create a new one. """
		if(r.exists('session:' + existing_identifier)):
			self.load_existing(existing_identifier)
		else:
			self.create_new(existing_identifier)
		self.dirty = False

	def add_expression(self, expression):
		""" Add the given expression identifier to our list of expressions for this session. """
		expression.save_data()
		self.expressions.append(expression.expression_identifier)
		self.dirty = True

	def get_most_recent_expression_identifier(self):
		""" Get the most recently-pushed expression identifier. """
		if len(self.expressions) > 0:
			return self.expressions[-1]

	def save_data(self):
		session_key = 'session:' + self.session_identifier
		if self.dirty:
			saved_expressions = r.lrange(session_key, 0, -1)
			for expression in self.expressions:
				if expression not in saved_expressions:
					r.lpush(session_key, expression)
			self.dirty = False
		else:
			pass
			## Do nothing -- we're clean.

	def compose_json(self):
		""" Get the session information that is most likely needed and return its dict for JSONification """
		## Save before returning.
		self.save_data()
		## Make dictionary and fill it.
		response_dictionary = { }
		response_dictionary['session_identifier'] = self.session_identifier
		response_dictionary['expressions'] = self.expressions
		## Return dictionary. Will be JSONified.
		return response_dictionary

class Expression:
	"""
		A composition of symbols.

		Discussion:
			Again running into the Redis datastorage problem with multiple datatypes.
			I think we can get away with this:

			key --> "expression_symbols:<expression_identifier>"
			value --> List of symbol identifiers

			key --> "expression_image:<expression_identifier>"
			value --> the stringIO for the image itself.

	"""

	def __init__(self):
		"""
			Empty Expression object created
		"""
		self.expression_identifier = ''
		self.symbols = []
		self.image = None
		self.dirty = True

	def create_new(self):
		self.expression_identifier = r.incr('expression_identifier_ids')
		self.dirty = True

	def load_existing(self, expression_identifier, should_load_image=False):
		if r.exists('expression_symbols:' + str(expression_identifier)):
			self.expression_identifier = expression_identifier
			self.symbols = r.lrange('expression_symbols:' + str(self.expression_identifier), 0, -1)
			if r.exists('expression_image:' + str(expression_identifier)) and should_load_image:
				## Image exists, grab it, if we are commanded to.
				print "Is this the real life?"
				self.image = r.get('expression_image:' + str(expression_identifier))
			else:
				self.image = None
			self.dirty = False
		else:
			if expression_identifier <= r.get('expression_identifier_ids'):
				# It DOES exist!
				self.expression_identifier = expression_identifier
				self.dirty = True
			else:
				raise Exception('Expression does not exist.')

	def add_image(self, image):
		if not self.image:
			self.image = image.stream.read()
		else:
			raise Exception('Image is already set. Cannot be reset.')
		self.dirty = True

	def identify_symbols(self):
		# ## Enqueue job. THIS COMING EVENTUALLY.
		symbol_identification_job = q.enqueue(roaster.identify_symbols, self.expression_identifier)
		start_time = time.time()
		timeout = 10
		while symbol_identification_job.result is None and time.time() < (start_time + timeout):
		    ##Do nothing.
		    pass
		## Now we have a result. Do something with it?
		if time.time() >= (start_time + timeout) :
			## We failed! THROW AN ERROR!
			raise Exception('Symbol Recognition timed out...')
		self.load_existing(self.expression_identifier)


	def save_data(self):
		if self.dirty:
			image_key = 'expression_image:' + str(self.expression_identifier)
			symbols_key = 'expression_symbols:' + str(self.expression_identifier)
			saved_symbols = r.lrange(symbols_key, 0, -1)
			if not r.exists(image_key) and self.image:
				r.set(image_key, self.image)
			for symbol in self.symbols:
				if symbol not in saved_symbols:
					r.lpush(symbols_key, symbol)
			self.dirty = False
		else:
			pass
			# Do nothing, for now, I guess.        	

	def get_image_for_return(self):
		"""
			Retrieves string representation of the image and returns as a file stream.
		"""
		image_key = 'expression_image:' + str(self.expression_identifier)
		if r.exists(image_key):
			stream = r.get(image_key)
			output = cStringIO.StringIO()
			output.write(stream)
			output.seek(0)
			return output
		else:
			raise Exception('Image does not exist!')

	def compose_json_symbols(self):
		symbol_data = []
		for symbol_identifier in self.symbols:
			s = Symbol()
			try:
				s.load_existing(symbol_identifier)
				box = s.bounding_box
				symbols = { }
				for pair in s.possible_symbols:
					symbols[pair[0]] = pair[1]
				symbol_data.append( { 'box':box, 'symbols':symbols } )
			except Exception, e:
				pass
				# EXPLODE
		return { 'symbols': symbol_data }

class Symbol:
	"""
		A class carrying a bounding box list and a dictionary
		of possible symbols it represents key-valued to 
		the probability of a match.

		Discussion: 
			Redis datastorage can't do something this complicated,
			at least I don't believe so, not on the surface. I posit
			that we make:

			key --> "symbol_box:<symbol_identifier>"
			value -->   Redis list with the box's values.

			key --> "symbol_candidates:<symbol_identifier>"
			value -->   Redis sorted set
						(value being the symbol, score being the, well, score)
						(( This __can__ be a float... ))

	"""

	def __init__(self):
		self.symbol_identifier = ''
		self.bounding_box = [0,0,0,0]
		self.possible_symbols = [ ] # List of tuples?
		self.dirty = True

	def create_new(self):
		self.symbol_identifier = r.incr('symbol_identifier_ids')
		self.dirty = True

	def load_existing(self, symbol_identifier):
		self.symbol_identifier = symbol_identifier
		box_key = 'symbol_box:' + self.symbol_identifier
		candidates_key = 'symbol_candidates:' + self.symbol_identifier
		if r.exists(box_key):
			self.bounding_box = r.lrange(box_key, 0, -1)
			self.possible_symbols = r.zrange(candidates_key, 0, -1, withscores=True)
		else:
			raise Exception('Symbol does not exist.')

	def set_box(self, new_x, new_y, new_w, new_h):
		self.bounding_box = [new_x, new_y, new_w, new_h]
		self.dirty = True

	def set_possible_symbols(self, new_possible_symbols):
		self.possible_symbols = new_possible_symbols
		self.dirty = True

	def add_possible_symbol(self, symbol, score):
		new_symbol = (symbol, score)
		self.possible_symbols.append(new_symbol)
		self.dirty = True

	def save_data(self):
		box_key = 'symbol_box:' + self.symbol_identifier
		candidates_key = 'symbol_candidates:' + self.symbol_identifier
		if self.dirty:
			if not self.bounding_box == [int(x) for x in r.lrange(box_key, 0, -1)]:
				r.delete(box_key)
				[r.rpush(x) for x in self.bounding_box]
			else:
				pass
				# Do nothing; bounding boxes match.
			saved_symbols = r.zrange(candidates_key, 0, -1, withscores=True)
			for symbol_pair in self.possible_symbols:
				if symbol_pair not in saved_symbols:
					r.zadd(candidates_key, symbol_pair[1], symbol_pair[0])
			self.dirty = False
		else:
			# Nothing to save!
			pass

class TrainingEvent:
	"""
		An event of training. Short-life object, not meant to persist very long.
		Just long enough to send Roaster the information it contains.
	"""
	def __init__(self, new_symbol=None):
		if new_symbol:
			## A symbol has been defined, so we can just set our self symbol to that.
			self.symbol = new_symbol
			self.image = None
		else:
			self.symbol = self.random_symbol()
			self.image = None

	def add_image(self, new_image):
		new_image.stream.seek(0)
		self.image = new_image.stream.read()

	def random_symbol(self):
		return ascii.get_random()

	def send_data(self):
		job = q.enqueue(roaster.train, self.image, self.symbol)

class Utility:
	def train(self):
		job = q.enqueue(roaster.run_training)
	def load(self):
		job = q.enqueue(roaster.load_data)
