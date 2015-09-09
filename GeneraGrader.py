#!/usr/bin/env python2

import sys
import re # regexp, used to check variables and functions names.

types_c = {'int':'int', 'l':'long int', 'll':'long long int', 'ull':'unsigned long long int', 'char':'char', 'double':'double', 'float':'float'}
stdio_types = {'int':'d', 'l':'ld', 'll':'lld', 'ull':'llu', 'char':'c', 'double':'lf', 'float':'f'}		
grader_c = open("grader.cpp", "w")
		
variables = {}
arrays = {}


def DeclareVariable(var):
	grader_c.write("static " + types_c[var["type"]] + " " + var["name"] + ";\n");
	
def DeclareArray(arr):
	grader_c.write("static " + arr["type"] + ( "*" * len(arr["dim"]) ) + " " + arr["name"] + ";\n" )

def FileHeaders():
	grader_c.write(
"""#include <stdio.h>
#include <assert.h>
#include <stdlib.h>

static FILE *fr, *fw;\n""")
	
def MainFunction():
	grader_c.write("""
int main() {
	#ifdef EVAL
		fr = fopen("input.txt", "r");
		fw = fopen("output.txt", "w");
	#else
		fr = stdin;
		fw = stdout;
	#endif
	
	// Reading input\n""")
	
def AllocateArray(name, arr):
	ArrLen = len(arr["dim"])
	
	for i in range(0, ArrLen):
		grader_c.write("\t"*i)
		if i != 0:
			it = "i" + str(i-1)
			grader_c.write("for (int " + it + " = 0; " + it + " < " + arr['dim'][i-1] + "; " + it + "++) {\n")
		
		grader_c.write("\t"*(i+1))
		grader_c.write(name)
		for j in range(0, i):
			grader_c.write("[i" + str(j) + "]")
		grader_c.write(" = (")
		grader_c.write(arr["type"] + " " + ("*" * (ArrLen-i)));
		grader_c.write(")malloc(" + arr["dim"][i] + " * sizeof(")
		grader_c.write(arr["type"] + ("*" * (ArrLen-i-1)))
		grader_c.write("));\n");
	
	for i in range(0, ArrLen - 1):
		grader_c.write("\t" * (ArrLen - i - 1)+ "}\n");
				
	grader_c.write("\n")

def ReadArrays(ReadArr):
	AllDim = arrays[ReadArr[0]]["dim"]
	for i in range(0, len(AllDim)):
		grader_c.write('\t' * (i+1))
		it = "i" + str(i)
		grader_c.write("for (int " + it + " = 0; " + it + " < " + AllDim[i] + "; " + it + "++) {\n")
	
	
	grader_c.write("\t" * (len(AllDim)+1))
	grader_c.write("fscanf(fr, \"")
				
	for name in ReadArr:
		grader_c.write("%" + stdio_types[arrays[name]["type"]] + " ")
	
	grader_c.write("\"")
	
	indexes = ""
	for i in range(0, len(AllDim)):
		indexes += "[i" + str(i) + "]"
	for name in ReadArr:
		grader_c.write(", &" + name + indexes)
	grader_c.write(");\n")
		
	for i in range(0, len(AllDim)):
		grader_c.write("\t" * (len(AllDim) - i)+ "}\n");
	
	grader_c.write("\n")
	
def ReadVariables(ReadVar):
	grader_c.write("\tfscanf(fr, \"");
			
	for var in ReadVar:
		if var not in variables:
			sys.exit("Una variabile da leggere non esiste")
		variables[var]['read'] = 1
		grader_c.write("%" + stdio_types[variables[var]["type"]] + " ")
	
	grader_c.write("\" ")
	
	for var in ReadVar:
		grader_c.write(", &" + var)
	
	grader_c.write(");\n\n")

def BetweenReadAndWrite():
	grader_c.write("\t// Writing output\n")

def WriteArrays(WriteArr):
	AllDim = arrays[WriteArr[0]]["dim"]
	for i in range(0, len(AllDim)):
		grader_c.write('\t' * (i+1))
		it = "i" + str(i)
		grader_c.write("for (int " + it + " = 0; " + it + " < " + AllDim[i] + "; " + it + "++) {\n")
	
	
	grader_c.write("\t" * (len(AllDim)+1))
	grader_c.write("fprintf(fw, \"")
				
	for name in WriteArr:
		grader_c.write("%" + stdio_types[arrays[name]["type"]] + " ")
	
	if len(WriteArr) > 1:
		grader_c.write("\\n")
	grader_c.write("\"")
	
	indexes = ""
	for i in range(0, len(AllDim)):
		indexes += "[i" + str(i) + "]"
	for name in WriteArr:
		grader_c.write(", " + name + indexes)
	grader_c.write(");\n")
		
	for i in range(0, len(AllDim)):
		grader_c.write("\t" * (len(AllDim) - i)+ "}\n")
		if i == len(AllDim)-1 and len(WriteArr) > 1:
			grader_c.write("\t" * (len(AllDim) - i)+ "fprintf(fw, \"\\n\");\n");
	grader_c.write("\n")

def WriteVariables(WriteVar):
	grader_c.write("\tfprintf(fw, \"")
	for name in WriteVar:
		grader_c.write("%" + stdio_types[variables[name]["type"]] + " ")
	grader_c.write("\\n\"")
	for name in WriteVar:
		grader_c.write(", " + name)
	grader_c.write(");\n\n")

def FileFooters():
	grader_c.write(
"""	fclose(fr);
	fclose(fw);
	return 0;
}
""")

FileHeaders()

var = open("variables.txt", "r")
lines = var.read().splitlines()
var.close()

# Parsing variables.txt
for line in lines:
	line.strip()
	if not line.startswith("#") and len(line) != 0: # Ignore empty lines and comments
		var = re.split('[ \[\]]', line) # Split line by square brackets and space
		var = [x for x in var if x] # Remove empty chunks
		
		if not var[0] in types_c:
			sys.exit("Tipo non esistente")
		
		if not re.match("^[a-zA-Z_$][0-9a-zA-Z_$]*$", var[1]):
			sys.exit("Il nome di una variabile contiene dei caratteri non ammessi")
		
		if len(var) == 2:
			if var[1] in variables:
				sys.exit("Nome della variabile già utilizzata")
			VarObj = {"name":var[1], "type":var[0], "read":0}
			variables[var[1]] = VarObj
					
			DeclareVariable(VarObj)
			
		else:
			dim = len(var)-2
			if var[1] in arrays:
				sys.exit("Nome dell'array già utilizzato")
			if dim == 0:
				sys.exit("Dimensioni dell'array non specificate")
			for num in var[2:]:
				if not num in variables:
					sys.exit("Dimensione dell'array non definita")
			ArrObj = {"name":var[1], "type":var[0], "dim":var[2:]}
			arrays[var[1]] = ArrObj
			
			DeclareArray(ArrObj)
			

MainFunction()

InputFormat = open("InputFormat.txt","r")
lines = InputFormat.read().splitlines()

# Parsing InputFormat.txt
for line in lines:
	line.strip()
	if not line.startswith("#") and len(line) != 0:
		if "[" in line: # Read arrays
			ReadArr = re.sub("[\[\]]", "", line) # Remove square brackets
			ReadArr = re.split(" ", ReadArr) # Split line by spaces
			ReadArr = [x for x in ReadArr if x] # Remove empty chuncks
			
			for name in ReadArr:
				if name not in arrays:
					sys.exit("Un array da leggere non esiste")
				
				arr = arrays[name]
				if arr["dim"] != arrays[ReadArr[0]]["dim"]:
					sys.exit("Array da leggere insieme devono avere le stesse dimensioni")
				
				for var in arr["dim"]:
					if variables[var]["read"] == 0:
						sys.exit("Quando si legge un array devono essere note le dimensioni")
						
				AllocateArray(name, arr)
					
			ReadArrays(ReadArr)
			
		else: # Read variables
			ReadVar = re.split(" ", line) # Split line by spaces
			ReadVar = [x for x in ReadVar if x] # Remove empty chuncks
			
			ReadVariables(ReadVar)

BetweenReadAndWrite()

OutputFormat = open("OutputFormat.txt","r")
lines = OutputFormat.read().splitlines()

# Parsing OutputFormat.txt
for line in lines:
	line.strip()
	if not line.startswith("#") and len(line) != 0:
		if "[" in line: # Write arrays
			WriteArr = re.sub("[\[\]]", "", line) # Remove square brackets
			WriteArr = re.split(" ", WriteArr) # Split line by spaces
			WriteArr = [x for x in WriteArr if x] # Remove empty chuncks
			
			for name in WriteArr:
				if name not in arrays:
					sys.exit("Un array da scrivere non esiste")
				
				arr = arrays[name]
				if arr["dim"] != arrays[WriteArr[0]]["dim"]:
					sys.exit("Array da scrivere insieme devono avere le stesse dimensioni")
					
			WriteArrays(WriteArr)
			
		else: # Write variables
			WriteVar = re.split(" ", line) # Split line by spaces
			WriteVar = [x for x in WriteVar if x] # Remove empty chuncks
			
			WriteVariables(WriteVar)

FileFooters()
