#!/usr/bin/python3
# An autogenerated selection of SurpriseDog's common functions relevant to this project.
# To see how this file was created visit: https://github.com/SurpriseDog/Star-Wrangler
# Written by SurpriseDog at: https://github.com/SurpriseDog

import os
import sys
import time
import json
import subprocess
from shutil import get_terminal_size


def sig(num, digits=3):
	"Return number formatted for significant digits (formerly get_significant)"
	ret = ("{0:." + str(digits) + "g}").format(num)
	if 'e' in ret:
		if abs(num) >= 1:
			return str(int(num))
		else:
			return str(num)
	else:
		return ret


def rfs(num, mult=1000, digits=3, order=' KMGTPEZY', suffix='B'):
	'''A "readable" file size
	mult is the value of a kilobyte in the filesystem. (1000 or 1024)'''
	if abs(num) < mult:
		return str(num) + suffix
	# Faster than using math.log:
	for x in range(len(order) - 1, -1, -1):
		magnitude = mult**x
		if abs(num) >= magnitude:
			return sig(num / magnitude, digits) + ' ' + (order[x] + suffix).rstrip()


def samepath(*paths):
	"Are any of these file pathname duplicates?"
	return bool(len({os.path.abspath(path) for path in paths}) != len(paths))


def mkdir(target, exist_ok=True, **kargs):
	"Make a directory without fuss"
	os.makedirs(target, exist_ok=exist_ok, **kargs)


def print_columns(args, col_width=20, columns=None, just='left', space=0, wrap=True):
	'''Print columns of col_width size.
	columns = manual list of column widths
	just = justification: left, right or center'''

	just = just[0].lower()
	if not columns:
		columns = [col_width] * len(args)

	output = ""
	_col_count = len(columns)
	extra = []
	for count, section in enumerate(args):
		width = columns[count]
		section = str(section)

		if wrap:
			lines = None
			if len(section) > width - space:
				# print(section, len(section), width)
				# lines = slicer(section, *([width] * (len(section) // width + 1)))
				lines = indenter(section, wrap=width - space)
				if len(lines) >= 2 and len(lines[-1]) <= space:
					lines[-2] += lines[-1]
					lines.pop(-1)
			if '\n' in section:
				lines = section.split('\n')
			if lines:
				section = lines[0]
				for lineno, line in enumerate(lines[1:]):
					if lineno + 1 > len(extra):
						extra.append([''] * len(args))
					extra[lineno][count] = line

		if just == 'l':
			output += section.ljust(width)
		elif just == 'r':
			output += section.rjust(width)
		elif just == 'c':
			output += section.center(width)
	print(output)

	for line in extra:
		print_columns(line, col_width, columns, just, space, wrap=False)


def auto_columns(array, space=4, manual=None, printme=True, wrap=0, crop=[]):
	'''Automatically adjust column size
	Takes in a 2d array and prints it neatly
	space = spaces between columns
	manual = dictionary of column adjustments made to space variable
	crop = array of max length for each column, 0 = unlimited
	example: {-1:2} sets the space variable to 2 for the last column'''
	if not manual:
		manual = dict()

	# Convert generators and map objects:
	array = list(array)

	if crop:
		out = []
		for row in array:
			row = list(row)
			for index in range(len(row)):
				line = str(row[index])
				cut = crop[index]
				if cut > 3 and len(line) > cut:
					row[index] = line[:cut-3]+'...'
			out.append(row)
		array = out


	# Fixed so array can have inconsistently sized rows
	col_width = {}
	for row in array:
		row = list(map(str, row))
		for col in range(len(row)):
			length = len(row[col])
			if length > col_width.get(col, 0):
				col_width[col] = length

	col_width = [col_width[key] for key in sorted(col_width.keys())]
	spaces = [space] * len(col_width)
	spaces[-1] = 0

	# Make any manual adjustments
	for col, val in manual.items():
		spaces[col] = val

	col_width = [sum(x) for x in zip(col_width, spaces)]

	# Adjust for line wrap
	max_width = get_terminal_size().columns     # Terminal size
	if wrap:
		max_width = min(max_width, wrap)
	extra = sum(col_width) - max_width          # Amount columns exceed the terminal width

	def fill_remainder():
		"After operation to reduce column sizes, use up any remaining space"
		remain = max_width - sum(col_width)
		for x in range(len(col_width)):
			if remain:
				col_width[x] += 1
				remain -= 1

	if extra > 0:
		# print('extra', extra, 'total', total, 'max_width', max_width)
		# print(col_width, '=', sum(col_width))
		if max(col_width) > 0.5 * sum(col_width):
			# If there's one large column, reduce it
			index = col_width.index(max(col_width))
			col_width[index] -= extra
			if col_width[index] < max_width // len(col_width):
				# However if that's not enough reduce all columns equally
				col_width = [max_width // len(col_width)] * len(col_width)
				fill_remainder()
		else:
			# Otherwise reduce all columns proportionally
			col_width = [int(width * (max_width / (max_width + extra))) for width in col_width]
			fill_remainder()
		# print(col_width, '=', sum(col_width))

	# Turn on for visual representation of columns:
	# print(''.join([str(count) * x  for count, x in enumerate(col_width)]))

	if printme:
		for row in array:
			print_columns(row, columns=col_width, space=0)

	return col_width


def error(*args, header='\nError:', **kargs):
	eprint(*args, header=header, v=3, **kargs)
	sys.exit(1)


def search_list(expr, the_list, getfirst=False, func='match', ignorecase=True, searcher=None):
	'''Search for expression in each item in list (or dictionary!)
	getfirst = Return the first value found, otherwise None
	searcher = Custom lamda function'''

	if not searcher:
		# func = dict(search='in').get('search', func)
		# Avoiding regex now in case substring has a regex escape character
		if ignorecase:
			expr = expr.lower()
		if func in ('in', 'search'):
			if ignorecase:
				def searcher(expr, item): return expr in item.lower()   # pylint: disable=E0102
			else:
				def searcher(expr, item): return expr in item           # pylint: disable=E0102
		elif func == 'match':
			if ignorecase:
				def searcher(expr, item): return item.lower().startswith(expr)  # pylint: disable=E0102
			else:
				def searcher(expr, item): return item.startswith(expr)          # pylint: disable=E0102
		else:
			# Could have nested these, but this is faster.
			raise ValueError("Unknown search type:", func)

	output = []
	for item in the_list:
		if searcher(expr, item):
			if isinstance(the_list, dict):
				output.append(the_list[item])
			else:
				output.append(item)
			if getfirst:
				return output[0]
	return output


def plural(val, word, multiple=None):
	'''Return value + word with plural ending
	You give plural the multiple version of the word to use or let it try to figure it out.
	https://www.grammarly.com/blog/plural-nouns/
	'''

	def get_word(word):
		word = word.lower()
		vowels = 'aoeiu'

		# Exceptions that have irregular changes
		exceptions = dict(
			child='children',
			goose='geese',
			man='men',
			woman='women',
			tooth='teeth',
			foot='feet',
			mouse='mice',
			person='people',
			dice='dies')
		if word in exceptions:
			return exceptions[word]

		# Game words that don't change ending
		if word in (
				'bison',
				'buffalo',
				'carp',
				'cod',
				'deer',
				'fish',
				'kakapo',
				'neat',
				'pike',
				'salmon',
				'sheep',
				'shrimp',
				'shrimps',
				'squid',
				'trout'):
			return word

		for ending in ('f', 'fe'):
			if word.endswith(ending):
				return word[:-1] + 'ves'

		if word.endswith('us') and len(word) > 4:
			return word[:-2] + 'i'

		if word.endswith('o'):
			if word not in ('photo', 'piano', 'halo'):
				return word + 'es'

		if word.endswith('is'):
			return word[:-2] + 'es'

		if word.endswith('on'):
			return word[:-2] + 'a'

		if word.endswith('y') and word[-2] not in vowels:
			return word[:-1] + 'ies'

		for ending in ('s', 'ss', 'sh', 'ch', 'x', 'z'):
			if word.endswith(ending):
				return word + 'es'

		return word + 's'

	if val == 1:
		return str(val) + ' ' + word
	elif multiple:
		return str(val) + ' ' + multiple
	else:
		replacement = get_word(word)
		if word.title() == word:
			replacement = replacement.title()
		if word.upper() == word:
			replacement = replacement.upper()

		return str(val) + ' ' + replacement


def indenter(*args, header='', level=0, tab=4, wrap=0, even=False):
	"Break up text into tabbed lines. Wrap at max characters. 0 = Don't wrap"

	if type(tab) == int:
		tab = ' ' * tab
	header = header + tab * level
	words = (' '.join(map(str, args))).split(' ')

	lc = float('inf')       # line count
	for wrap in range(wrap, -1, -1):
		out = []
		line = ''
		count = 0
		for word in words:
			if count:
				new = line + ' ' + word
			else:
				new = header + word
			count += 1
			if wrap and len(new.replace('\t', ' ' * 4)) > wrap:
				out.append(line)
				line = header + word
			else:
				line = new
		if line:
			out.append(line)
		if not even:
			return out
		if len(out) > lc:
			return prev
		prev = out.copy()
		lc = len(out)
	return out


def tab_printer(*args, **kargs):
	for line in indenter(*args, **kargs):
		print(line)


def json_loader(data):
	try:
		tree = json.loads(data)
	except json.decoder.JSONDecodeError as err:
		print('\n'*5)
		if len(data) > 5000:
			data = data[:5000] + ' ...'
		print('Json Data:', repr(data))
		raise ValueError("Json error", err.__class__.__name__)
	return tree


class Eprinter:
	'''Drop in replace to print errors if verbose level higher than setup level
	To replace every print statement type: from common import eprint as print

	eprint(v=-1)    # Normally hidden messages
	eprint(v=0)     # Default level
	eprint(v=1)     # Priority messages
	eprint(v=2)     # Warnings
	eprint(v=3)     # Errors
	'''

	# Setup: eprint = Eprinter(<verbosity level>).eprint
	# Simple setup: from common import eprint
	# Usage: eprint(messages, v=1)

	# Don't forget they must end in 'm'
	BOLD = '\033[1m'
	WARNING = '\x1b[1;33;40m'
	FAIL = '\x1b[0;31;40m'
	END = '\x1b[0m'

	def __init__(self, verbose=0):
		self.level = verbose

	def eprint(self, *args, v=0, color=None, header=None, **kargs):
		'''Print to stderr
		Custom color example: color='1;33;40'
		More colors: https://stackoverflow.com/a/21786287/11343425
		'''
		verbose = v
		# Will print if verbose >= level
		if verbose < self.level:
			return 0

		if not color:
			if v == 2 and not color:
				color = f"{self.WARNING}"
			if v >= 3 and not color:
				color = f"{self.FAIL}" + f"{self.BOLD}"
		else:
			color = '\x1b[' + color + 'm'

		msg = ' '.join(map(str, args))
		if header:
			msg = header + ' ' + msg
		if color:
			print(color + msg + f"{self.END}", file=sys.stderr, **kargs)
		else:
			print(msg, file=sys.stderr, **kargs)
		return len(msg)


eprint = Eprinter(verbose=1).eprint     # pylint: disable=C0103


def warn(*args, header="\n\nWarning:", delay=1 / 64):
	time.sleep(eprint(*args, header=header, v=2) * delay)


def flatten(tree):
	"Flatten a nested list, tuple or dict of any depth into a flat list"
	# For big data sets use this: https://stackoverflow.com/a/45323085/11343425
	out = []
	if isinstance(tree, dict):
		for key, val in tree.items():
			if type(val) in (list, tuple, dict):
				out += flatten(val)
			else:
				out.append({key: val})

	else:
		for item in tree:
			if type(item) in (list, tuple, dict):
				out += flatten(item)
			else:
				out.append(item)
	return out


def quickrun(*cmd, check=False, encoding='utf-8', errors='replace', mode='w', input=None,
			 verbose=0, testing=False, ofile=None, trifecta=False, hidewarning = False, **kargs):
	'''Run a command, list of commands as arguments or any combination therof and return
	the output is a list of decoded lines.
	check    = if the process exits with a non-zero exit code then quit
	testing  = Print command and don't do anything.
	ofile    = output file
	mode     = output file write mode
	trifecta = return (returncode, stdout, stderr)
	input	 = stdinput (auto converted to bytes)
	'''
	cmd = list(map(str, flatten(cmd)))
	if len(cmd) == 1:
		cmd = cmd[0]

	if testing:
		print("Not running command:", cmd)
		return []

	if verbose:
		print("Running command:", cmd)
		print("               =", ' '.join(cmd))

	if ofile:
		output = open(ofile, mode=mode)
	else:
		output = subprocess.PIPE

	if input:
		if type(input) != bytes:
			input = input.encode()

	#Run the command and get return value
	ret = subprocess.run(cmd, check=check, stdout=output, stderr=output, input=input, **kargs)
	code = ret.returncode
	stdout = ret.stdout.decode(encoding=encoding, errors=errors).splitlines() if ret.stdout else []
	stderr = ret.stderr.decode(encoding=encoding, errors=errors).splitlines() if ret.stderr else []

	if ofile:
		output.close()
		return []

	if trifecta:
		return code, stdout, stderr

	if code and not hidewarning:
		warn("Process returned code:", code)

	for line in stderr:
		print(line)

	return stdout


def srun(*cmds, **kargs):
	"Split all text before quick run"
	return quickrun(flatten([str(item).split() for item in cmds]), **kargs)
