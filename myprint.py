import sys

def Print(farg="", *args, **kwargs):
	
	if not 'sep' in kwargs:
		sep = " "
	else:
		sep = kwargs['sep']
	if not 'end' in kwargs:
		end = "\n"
	else:
		end = kwargs['end']
	if not 'file' in kwargs:
		file = sys.stdout
	else:
		file = kwargs['file']

	# print("debug",kwargs)
	s = str(farg)
	if len(args) != 0:
		for arg in args:
			s += sep + str(arg)
	file.write(s+end)

if __name__ == '__main__':
	Print(1)
	Print(1,2)
	Print(1,2,3)
	Print("a", 1)
	Print(1,2,3,sep='')
	Print(1,"a",3,sep="_",end="#\n")

