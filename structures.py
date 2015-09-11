class Variable:
	def __init__(self, n, t):
		self.name = n
		self.type = t
		self.read = False

class Array:
	def __init__(self, n, t, s):
		self.name = n
		self.type = t
		self.dim = len(s)
		self.sizes = s

class Function:
	def __init__(self, n = None, p = None, r = None):
		self.name = n
		self.parameters = p
		if r != None:
			self.type = r.type
			self.return_var = r
		else:
			self.type = ""
			self.return_var = None

variables = {}
arrays = {}
functions = []
