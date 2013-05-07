from random import choice

values = [ '+', '-', '*', '/', '.', '(', ')', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'x', 'y', '=' ]
values = [ '1', '2' ]
ascii_values = [ord(x) for x in values]

def get_random():
	return choice(ascii_values)