# Python standard imports
import datetime, random, cStringIO

# Redis & RedisQ imports
import redis
import rq

# Barista imports
from barista_settings import settings

# Roaster imports
import roaster

## Set up Redis connections.
rq_connection = redis.Redis(host='ec2-54-244-145-206.us-west-2.compute.amazonaws.com', port=6379, db=0)
r = redis.StrictRedis(host=settings['redis_hostname'], port=settings['redis_port'], db=settings['redis_db'])

## Set up RQueue.
q = rq.Queue(connection=rq_connection)

if not r.exists('expression_identifier_ids'):
    r.set('expression_identifier_ids', 1)
if not r.exists('symbol_identifier_ids'):
    r.set('symbol_identifier_ids', 1)

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

class Session:
    """ 
        Class representing a session. Holds an identifier
        associated with this session and defines several
        helpful methods.

        REDIS DATA:
        key     --> "session:<self.session_identifier>"
        value   --> [list of expression_identifier(s)]
    """
    session_identifier = ''

    def __init__(self, identifier=None):
        """ Retrieve the session of identifier and create our object from it """
        if identifier:
            self.session_identifier = identifier
            self.expressions = r.lrange('session:' + self.session_identifier, 0, -1)
        else:
            self.session_identifier = get_unique_session_identifier()
            self.expressions = []

    def add_expression(self, expression):
        """ Add the given expression's identifier to our list of expressions for this session. """
        r.rpush('session:' + self.session_identifier, expression.expression_identifier)

    def get_most_recent_expression_identifier(self):
        """ Get the most recently-pushed expression identifier. """
        if r.llen(self.session_identifier) > 0:
            expression_identifier = r.lrange('session:' + self.session_identifier, -1, -1)[0]
            return expression_identifier
        return False

    def get_session_json(self):
        """ Get the session information that is most likely needed and return its dict for JSONification """
        response_dictionary = { }
        response_dictionary['session_identifier'] = self.session_identifier
        response_dictionary['expressions'] = r.lrange('session:' + self.session_identifier, 0, -1)
        return response_dictionary


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
    symbol_identifier = 0
    bounding_box = [0,0,0,0]
    possible_characters = {  }

    def __init__(self, box=None):
        if box:
            self.symbol_identifier = r.incr('symbol_identifier_ids')
            self.bounding_box = box
            self.possible_characters = {  }

            box_key = 'symbol_box:' + str(self.symbol_identifier)
            [r.rpush(box_key, value) for value in self.bounding_box]

            candidates_key = 'symbol_candidates:' + str(self.symbol_identifier)
            [r.zadd(candidates_key, key, self.possible_characters[key]) for key in self.possible_characters.keys()]
        else: 
            self.symbol_identifier = r.incr('symbol_identifier_ids')
            self.bounding_box = [0,0,0,0]
            self.possible_characters = {  }

            box_key = 'symbol_box:' + str(self.symbol_identifier)
            [r.rpush(box_key, value) for value in self.bounding_box]

            candidates_key = 'symbol_candidates:' + str(self.symbol_identifier)
            [r.zadd(candidates_key, key, self.possible_characters[key]) for key in self.possible_characters.keys()]

    def add_possible_symbol(self, symbol, score):

        self.possible_characters[symbol] = score

        candidates_key = 'symbol_candidates:' + str(self.symbol_identifier)
        r.zadd(candidates_key, symbol, score)


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

    expression_identifier = 0
    symbols = []
    image = None

    def __init__(self, expression_identifier=None):
        if expression_identifier:
            self.expression_identifier = expression_identifier
            symbols_key = 'expression_symbols:' + str(expression_identifier)
            image_key = 'expression_image:' + str(expression_identifier)
            if r.exists(symbols_key):
                self.symbols = r.lrange(symbols_key, 0, -1)
            if r.exists(image_key):
                self.image = r.get(image_key)
        else:
            # Make (a relatively) unique identifier for this expression.
            self.expression_identifier = r.incr('expression_identifier_ids')
            self.symbols = []
            self.image = None

    def add_image(self, image):
        image_key = 'expression_image:' + self.expression_identifier
        r.set(image_key, image.stream.read())
        ## Seek back to zero.
        image.stream.seek(0)
        ## Create our tuple to send.
        image_tuple = (self.expression_identifier, image.stream.read())
        ## Enqueue job.
        symbol_recognition_job = q.enqueue(roaster.identify_symbols, image_tuple)
        while symbol_recognition_job.result is None:
            ## Do nothing.
            pass
        ## Now we have a result. Do something with it?
        print symbol_recognition_job.result


    def get_image_for_return(self):
        image_key = 'expression_image:' + self.expression_identifier
        ## We have an image, so pull out the bits of it and make a response
        ## with the proper headers so that it downloads.
        if r.exists(image_key):
            stream = r.get(image_key)
            output = cStringIO.StringIO()
            output.write(stream)
            output.seek(0)
            return output


           