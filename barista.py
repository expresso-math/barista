import redis
import datetime
import random


r = redis.StrictRedis(host='localhost', port=6379, db=0)

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

    def __init__(self):
        """ Make a brand new session and save it. """
        self.session_identifier = get_unique_session_identifier()

    def __init__(self, identifier):
        """ Retrieve the session of identifier and create our object from it """
        self.session_identifier = identifier
        if r.exists('session:' + self.session_identifier):
            ## Session already exists, grab its data.
            self.expressions = r.lrange('session:' + self.session_identifier, 0, -1)
        else:
            ## Session apparently doesn't exist, we should return false, since the only
            ## session names that we should receive are ones we already know.
            raise StandardError('Session doesn\'t exist!')

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

            key --> "symbol_box:<symbold_identifier>"
            value -->   Redis sorted set
                        (value being the symbol, score being the, well, score)
                        (( This __can__ be a float... ))

    """
    bounding_box = []
    possible_characters = {  }
    def __init__(self):
        self.bounding_box = []
        self.possible_characters = {  }
    def __init__(self, box):
        self.bounding_box = box
        self.possible_characters = {  }

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
    expression_identifier = ''
    symbols = []
    image = None
    def __init__(self):
        # Make (a relatively) unique identifier for this expression.
        now = datetime.datetime.now()
        m = md5.new(str(now))
        self.expression_identifier = m.hexdigest()
        self.symbols = []
        self.image = None
    def __init__(self, new_image):
        self.symbols = []
        self.image = new_image