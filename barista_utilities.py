import random

adjectives  = ['iced', 'tall', 'short', 'grande', 'nonfat', 'skinny', 'almond', 'soy', 'vanilla', 'extra-hot', 'breve', 'cinnamon', 'dry']
nouns       = ['mocha', 'latte', 'cappuccino', 'americano', 'steamer', 'macchiato']

def generate_session_name(): 
    adjective = adjectives[random.randint(0,len(adjectives)-1)]
    noun      = nouns[random.randint(0,len(nouns)-1)]
    number    = str(random.randint(0, 9))+str(random.randint(0, 9))+str(random.randint(0, 9))+str(random.randint(0, 9))
    name = '' + str(adjective) + '-' + str(noun) + '-' + str(number) + ''
    print name
    return name