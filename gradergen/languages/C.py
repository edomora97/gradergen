import pkg_resources
import sys
import os
from gradergen import structures
from gradergen.structures import Variable, Array, Function, IOline, Expression


class LanguageC(object):
	def __init__(self, fast_io, data):
		self.data = data

		self.grader = ""
		self.template = ""
		if fast_io == 1:
			self.fast_io = True
		else:
			self.fast_io = False

	extension = "c"

	types = {'':'void', 'int':'int', 'longint':'long long int', 'char':'char', 'real':'double'}
	
	template_types = {'':'', 'int':'1', 'longint':'123456789123ll', 'char':'\'f\'', 'real':'123.456'}
	
	stdio_types = {'int':'d', 'longint':'lld', 'char':'c', 'real':'lf'}

	headers = """\
#include <stdio.h>
#include <assert.h>
#include <stdlib.h>

static FILE *fr, *fw;
"""

	main_function = """\

int main() {
	%(input)s
	%(output)s
"""

	footers = """\

	fclose(fr);
	fclose(fw);
	return 0;
}
"""

	byref_symbol = "* "
	byref_call = "&"
	byref_access = "*"

	comments = {
		"dec_var": "Declaring variables",
		"dec_fun": "Declaring functions",
		"dec_help": "Declaring helper functions",
		"input": "Reading input",
		"call_fun": "Calling functions",
		"output": "Writing output",
	}
	
	# Print the string corresponding to a parameter
	def print_parameter(self, param):
		return self.types[param.type] + ("*" * param.dim) + (self.byref_symbol if param.by_ref and param.dim == 0 else "") + param.name
			
	# array type
	def at(self, type, dim):
		return self.types[type] + "*"*dim

	# write line
	def write_line(self, line, tabulation = 0):
		self.grader += "\t"*tabulation + line + "\n"

	# write comment
	def write_comment(self, short_description, tabulation = 0):
		if len(self.comments[short_description]) > 0:
			self.grader += "\n" + ("\t"*tabulation) + "// " + self.comments[short_description] +"\n"

	def declare_variable(self, var):
		self.write_line("static {0} {1};".format(self.types[var.type], var.name))

	def declare_array(self, arr):
		self.write_line("static {0} {1};".format(self.at(arr.type, arr.dim), arr.name) )

	def declare_prototype(self, fun):
		printed_parameters = [print_parameter(param) for param in fun.parameters]
		
		self.write_line("{0} {1}({2});".format(self.types[fun.type], fun.name, ", ".join(printed_parameters)))

	def allocate_array(self, arr):
		for i in range(arr.dim):
			if i != 0:
				self.write_line("for (int {0} = 0; {0} < {1}; {0}++) {{".format("i" + str(i-1), arr.sizes[i-1].to_string()), i)

			indexes = "".join("[i" + str(x) + "]" for x in range(i))
			self.write_line("{0}{1} = ({2}*)malloc(({3}) * sizeof({2}));".format(arr.name, indexes, self.at(arr.type, arr.dim-i-1), arr.sizes[i].to_string()), i+1)

		for i in range(arr.dim - 1):
			self.write_line("}", arr.dim - i - 1)

	def read_arrays(self, all_arrs):
		all_dim = all_arrs[0].dim
		all_sizes = all_arrs[0].sizes
		for i in range(all_dim):
			self.write_line("for (int {0} = 0; {0} < {1}; {0}++) {{".format("i" + str(i), all_sizes[i].to_string()), i+1)

		indexes = "".join("[i" + str(x) + "]" for x in range(0, all_dim))
		if self.fast_io:
			for arr in all_arrs:
				self.write_line("{0} = fast_read_{1}();".format(arr.name + indexes, arr.type), all_dim+1)
		else:
			format_string = " ".join("%" + self.stdio_types[arr.type] for arr in all_arrs)
			pointers = ", ".join("&" + arr.name + indexes for arr in all_arrs)
			# The space after the format_string is used to ignore all whitespaces
			self.write_line("fscanf(fr, \" {0}\", {1});".format(format_string, pointers), all_dim+1)

		for i in range(all_dim):
			self.write_line("}", all_dim - i)

	def read_variables(self, all_vars):
		if self.fast_io:
			for var in all_vars:
				self.write_line("{0} = fast_read_{1}();".format(var.name, var.type), 1)
		else:
			format_string = " ".join("%" + self.stdio_types[var.type] for var in all_vars)
			pointers = ", ".join("&" + var.name for var in all_vars)
			# The space after the format_string is used to ignore all whitespaces
			self.write_line("fscanf(fr, \" {0}\", {1});".format(format_string, pointers), 1)

	def call_function(self, fun):
		parameter_names = [(self.byref_call if by_ref else "") + var.name for (var, by_ref) in fun.parameters]
		parameters = ', '.join(parameter_names)
		
		if fun.type == "":
			self.write_line("{0}({1});".format(fun.name, parameters), 1)
		else:
			self.write_line("{2} = {0}({1});".format(fun.name, parameters, fun.return_var.name), 1)

	def write_arrays(self, all_arrs):
		all_dim = all_arrs[0].dim
		all_sizes = all_arrs[0].sizes

		for i in range(all_dim):
			self.write_line("for (int {0} = 0; {0} < {1}; {0}++) {{".format("i" + str(i), all_sizes[i].to_string()), i+1)

		indexes = "".join("[i" + str(x) + "]" for x in range(all_dim))
		if self.fast_io:
			for arr in all_arrs:
				self.write_line("fast_write_{0}({1});".format(arr.type, arr.name + indexes), all_dim + 1)
				if arr != all_arrs[-1]:
					self.write_line("fast_write_char(' ');", all_dim + 1)
			if len(all_arrs) > 1:
				self.write_line("fast_write_char('\\n');", all_dim + 1)
			elif all_arrs[0].type != 'char':
				self.write_line("fast_write_char(' ');", all_dim + 1)
		else:
			format_string = " ".join("%" + self.stdio_types[arr.type] for arr in all_arrs)
			antipointers = ", ".join(arr.name + indexes for arr in all_arrs)
			if len(all_arrs) > 1:
				self.write_line("fprintf(fw, \"{0}\\n\", {1});".format(format_string, antipointers), all_dim+1)
			elif all_arrs[0].type != 'char':
				self.write_line("fprintf(fw, \"{0} \", {1});".format(format_string, antipointers), all_dim+1)
			else:
				self.write_line("fprintf(fw, \"{0}\", {1});".format(format_string, antipointers), all_dim+1)

		for i in range(all_dim):
			self.write_line("}", all_dim - i)
			if i == 0 and len(all_arrs) == 1:
				if self.fast_io:
					self.write_line("fast_write_char('\\n');", all_dim - i)
				else:
					self.write_line("fprintf(fw, \"\\n\");", all_dim - i)

	def write_variables(self, all_vars):
		if self.fast_io:
			for var in all_vars:
				self.write_line("fast_write_{0}({1});".format(var.type, var.name), 1)
				if var != all_vars[-1]:
					self.write_line("fast_write_char(' ');", 1)
			self.write_line("fast_write_char('\\n');", 1)
		else:
			format_string = " ".join("%" + self.stdio_types[var.type] for var in all_vars)
			antipointers = ", ".join(var.name for var in all_vars)
			self.write_line("fprintf(fw, \"{0}\\n\", {1});".format(format_string, antipointers), 1)

	def insert_headers(self):
		self.grader += self.headers

	def insert_main(self):
		if self.fast_io:
			fast_io_file = open(pkg_resources.resource_filename("gradergen.languages", "fast_io." + self.extension), "r")
			self.grader += "\n" + fast_io_file.read()
			fast_io_file.close()

		self.grader += self.main_function % {
			"input": "fr = stdin;" if self.data["input_file"] == "" else "fr = fopen(\"" + self.data["input_file"] + "\", \"r\");",
			"output": "fw = stdout;" if self.data["output_file"] == "" else "fw = fopen(\"" + self.data["output_file"] + "\", \"w\");",
		}

	def insert_footers(self):
		self.grader += self.footers

	def write_files(self, grader_name, template_name, use_helper):
		self.write_grader(use_helper)
		self.write(grader_name, self.grader)
		
		self.write_template()
		self.write(template_name, self.template)

	def write_grader(self, use_helper):
		self.grader = ""
		self.insert_headers()

		self.write_comment("dec_var")
		for var in self.data["variables"]:
			if type(var) == Variable:
				self.declare_variable(var)
			elif type(var) == Array:
				self.declare_array(var)

		self.write_comment("dec_fun")
		for fun in self.data["prototypes"]:
			self.declare_prototype(fun)

		if use_helper:
			self.write_comment("dec_help")
			self.grader += self.data["helper_data"]

		self.insert_main()
		self.write_comment("input", 1)
		for input_line in self.data["input"]:
			if input_line.type == "Array":
				for arr in input_line.list:
					self.allocate_array(arr)
					self.data["arrays"][arr.name].allocated = True
				self.read_arrays(input_line.list)

			elif input_line.type == "Variable":
				self.read_variables(input_line.list)

		self.write_comment("call_fun", 1)
		for fun in self.data["calls"]:
			for (var, by_ref) in fun.parameters):
				if type(var) == Array and var.allocated == False:
					if not all((expr.var is None or expr.var.read) for expr in param.sizes):
						sys.exit("Devono essere note le dimensioni degli array passati alle funzioni dell'utente")
					self.allocate_array(var)
					var.allocated = True
				if type(var) == Variable and not var.read and not by_ref:
					sys.exit("I parametri non passati per reference alle funzioni dell'utente devono essere noti")

			self.call_function(fun)
			if fun.return_var:
				fun.return_var.read = True

			# Variables passed by reference are "read"
			for (var, by_ref) in fun.parameters:
				if type(var) == Variable and by_ref:
					var.read = True

		self.write_comment("output", 1)
		for output_line in self.data["output"]:
			if output_line.type == "Array":
				self.write_arrays(output_line.list)
			elif output_line.type == "Variable":
				self.write_variables(output_line.list)

		self.insert_footers()

	def write_template(self):
		for fun in self.data["prototypes"]:
			printed_parameters = [print_parameter(param) for param in fun.parameters]
			self.template += "{0} {1}({2}) {{\n".format(self.types[fun.type], fun.name, ", ".join(printed_parameters))
			
			# Variables passed by ref are filled
			for param in fun.parameters:
				if param.by_ref:
					if param.dim == 0:
						self.template += "\t{0}{1} = {2};\n".format(self.byref_access, param.name, self.template_types[param.type])
					else:
						self.template += "\t{0}{1} = {2};\n".format(param.name, "[0]"*param.dim, self.template_types[param.type])
			self.template += "\treturn {0};\n".format(self.template_types[fun.type])
			
			self.template += "}\n\n"
			

	def write(self, filename, source):
		# Unlink is used to avoid following symlink
		try:
			os.unlink(filename)
		except OSError:
			pass
		
		with open(filename, "w") as f:
			f.write(source)
