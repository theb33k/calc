import re

def matchList(regex, text, include_infos=False):
	cr = re.compile(regex)
	a=[]
	for m in cr.finditer(text):
		if include_infos:
			a.append((m.group(), m.start(), m.end()))
		else:
			a.append(m.group())
	return a