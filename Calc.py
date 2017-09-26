#!/usr/bin/python
# -*-coding:Latin-1 -*

# Cahier des charges
# Symboles acceptes: 
# +-*/^e
# espace
# ()
# 0123456789
# .
#test 26/09/2017 - 13:15


'''
AIDE MEMOIRE

> 5e6 <=> 5*10^6 => 5*(10^6)

>Priorité des opérateurs : (vide => ordre syntaxique)
	+	-	*	/	^	e
+			*	/	^	e
-			*	/	^	e
*	*	*			^	e
/	/	/			^	e
^	^	^	^	^		e
e 	e 	e 	e 	e 	e

+ et - => priorité 1
* et / => priorité 2
^ => priorité 3
e => priorité 4

>Modifications hiérarchique
--1+2 => -(-1)+2
1+2+3 => (1+2)+3
1+2*3+4 => 1+(2*3)+4 => (1+(2*3))+4
1+2*3*4 => 1+((2*3)*4)
1+2*3^4e5 => 1+(2*(3^(4e5)))

>types de blocs
1
-1
1.1
-1.1
(1)
(-1)
-(1)
-(-1)




>Etape du parsing
vérifier les caractères autorisés
supprimer les espaces
rajouter les parenthèses manquantes à la fin
	vérifier les erreurs de parenthèses
Etape 1 Modifications hiérarchique (faire en sorte qu'il n'y ai que 2 opérande par opération)

Etape 2 Construction de l'arbre
Pour chaque bloc
	supprimer les paires de parenthèses en trop : ((1+2)) => 1+2
	séparer blocs et opérateurs (délicat)
	au même niveau de parenthésage, isoler les opération prioritaire récursivement

Regex :
Numbers : -?[0-9]*(\.[0-9]+)?([e|E][+-]?[0-9]+)?
functions : [a-z]+[0-9]*

<b001> => blocks
<n001> => numbers
<f001> => functions

1+(2*3) => <n001>+<b001>
	<b001>.string = <n002>*<n003>


'''

import os
import re
import math
from myprint import *


ALPHABET = [chr(i) for i in range(ord('a'), ord('z')+1)]
VALID_CHARS = [	"0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
				"+", "-", "*", "/", "^", "E", "(", ")", " ", "."] + ALPHABET
# OPERATOR INDEXES	 0	1	2	3	4	5
OPERATORS = 		[ "+", "-", "*", "/", "^", "E"]
OPERATOR_PRIORITY = [  1,   1,   2,   2,   3,   4]

# end of line:
if os.name == 'posix':
	eol = "\n"
elif os.name == 'nt':
	eol = "\r\n"


# General purpose functions **************************************************

def strInser(s_init,pos, s_to_inser): # OK
	if pos < 0 or pos > len(s_init)-1:
		return s_init
	return s_init[:pos] + s_to_inser + s_init[pos:]

def strDel(s_init, pos, nchar=1): # OK
	if pos < 0 or pos > len(s_init)-1:
		return s_init
	return s_init[:pos] + ("" if pos+nchar > len(s_init) else s_init[pos+nchar:])

def strRepl(s_init, pos, nchar, s_to_inser): # OK
	if pos < 0 or pos > len(s_init)-1:
		return s_init
	return s_init[:pos] + s_to_inser + s_init[(pos+nchar):]



# Dedicated functions *********************************************************

def printError(err): # OK
	'''
		err is a tuple like (s, pos) with
		s the string
		pos is None if no error and the position otherwise
	'''
	if err[1] == None:
		return
	Print(err[0])
	for i in range(err[1]) : Print(" ", end = "")
	Print("^")

def getEntry(): # OK
	Print(">", end="")
	return input()

def checkChars(s): # OK
	'''
		check if the chars in the typed string are valid
		Return a tuple with:
			(s, None) if no errors
			(s, pos) with pos the position of the error otherwise
	'''
	global VALID_CHARS
	for i in range(len(s)):
		if s[i] not in VALID_CHARS:
			return (s, i)
	return (s, None)

def removeSpaces(s): # OK
	return s.replace(' ', '')

def checkBrackets(s): # OK
	'''
		add forgotten brackets at the end
		check if there's a bracket error like (1+3)*2+5)
		Return a tuple with:
			(s, None) if no errors
			(s, pos) with pos the position of the error otherwise
	'''
	i=0
	level = 0
	while i < len(s):
		if s[i] == '(':
			level += 1
		elif s[i] == ')':
			level -= 1
		if level < 0: # Return -1 if there's a bracket error
			return (s, i)
		i += 1
	while level > 0:
		s = s + ')'
		level -= 1
	while s[0] == '(' and s[-1] == ')': # remove every external bracket pairs
		s=s[1:][:-1]
	if s[0] != '(': # add just one external bracket pair
		s = '(' + s + ')'	
	return (s, None)

def checkCommonErrors(s): # OK
	'''
		Return a tuple with
			(s, None) if no errors were found
			(s, pos) with pos the position of the first error otherwise
	'''
	ERRORS = ['\+\*', '\+/', '\+\^', '\+E', '-\*', '-/', '-\^', '-E', 
	          '\*\*', '\*/', '\*^', '\*E', '/\*', '//', '/\^', '/E',
	          '\^\*', '\^/', '\^\^', '\^E', 'E\*', 'E/', 'E\^', 'EE',
	          '\(\*', '\(/', '\(\^', '\(E', '\+\)', '-\)', '\*\)', '/\)', 
	          '\^\)', 'E\)', '\(\)', '-\+']
	for e in ERRORS:
		f = re.search(e,s)
		if f != None:
			pos = f.span(0)[0] + 1
			return (s, pos)
	return (s, None)

def doCommonReplacements(s): # OK
	SEARCH_FOR   = ['\+\+', '\+--', '\+-', '---', '--', '\(\+', '\*\+', '/\+', '\^\+', 'E\+'] # regex pattern
	REPLACE_WITH = ['+'   , '+'   , '-'  , '-'  , '+' , '('   , '*'   , '/'  , '^'   , 'E']
	for i in range(len(SEARCH_FOR)):
		regexp = re.compile(SEARCH_FOR[i])
		f = regexp.search(s)
		while f != None:
			s = regexp.sub(REPLACE_WITH[i], s)
			f = regexp.search(s)
	return s


def replaceBlocks(s):
	# regex for finding numbers (decimals, floats, all of them except hexa)
	numreg = "-?[0-9]*(\\.[0-9]+)?([e|E][+-]?[0-9]+)?"


class block:
	'''
		Can be:
			a number
			something between brackets
			f(something)
	'''
	def __init__(self):
		# initialize block
		value = None
		operandes = []
		operators = []
		# operator = None
		# level_zero = True # says if there is no subBlock (<=> no operators)
	
	def parseLvl1(self, str, start, end):
		# build a tree only with brackets, functions and numbers
		'''
		# parse the string str from the index start to end (excluded)
		# Example : 1+(2*3) from i=0 to i=9 gives
		# self:
		#		value = None
		#		level_zero = False
		# 		operande1 = subBlock1
		#		operande2 = subBlock2
		#		operator = 0
		# subBlock1:
		#		value = 1
		#		level_zero = True
		# 		operande1 = 0
		#		operande2 = 0
		#		operator = None
		# subBlock2:
		#		value = None
		#		level_zero = False
		# 		operande1 = subBlock2.1
		#		operande2 = subBlock2.1
		#		operator = 2
		# subBlock2.1:
		#		value = 2
		#		level_zero = True
		# 		operande1 = 0
		#		operande2 = 0
		#		operator = None
		# subBlock2.2:
		#		value = 3
		#		level_zero = True
		# 		operande1 = 0
		#		operande2 = 0
		#		operator = None
		#
		# Hierarchy :
		# self
		# 		subBlock1
		#		subBlock2
		#			subBlock2.1
		#			subblock2.2
		'''

		pass
	def unPlusMinus(self, s, pos):
		'''
			remove the unecessary serie of + - operators
			RETURN 
				- 
		'''

	def delimitBlock(self, s, pos):
		'''
			s is the string to parse
			pos the position of the first char of the block
			RETURN
				- the size of the block
		'''

	def compute(self):
		pass

	value = 0
	operande1 = 0
	operande2 = 0
	operator = -1


def test(s):
	# s=getEntry()
	r = checkChars(s)
	if r[1] != None:
		Print("Syntax error : ")
		printError(r)
		return

	s = removeSpaces(s)

	r = checkBrackets(s)
	if r[1] != None:
		Print("Bracket error : ")
		printError(r)
	else:
		s = r[0]

	r = checkCommonErrors(s)
	if r[1] != None:
		Print("Syntax error : ")
		printError(r)

	s = doCommonReplacements(s)
	Print(s)
	Print()
	Print()
	Print()
if __name__ == '__main__':
	fi = open("unitTests.txt", "r")
	content = fi.read()
	fi.close()
	tests = content.split(eol)

	i=1
	for t in tests:
		Print(i,':')
		i=i+1
		Print(t)
		test(t)
