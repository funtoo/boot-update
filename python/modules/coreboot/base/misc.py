def deburr(str):
	# remove " " from around a string
	if str[0] != '"':
		return str
	elif str[0] == '"' and str[-1] == '"':
		return str[1:-1]
	else:
		# failed deburr
		raise
def einfo(msg):
	sys.stderr.write(msg+"\n")


