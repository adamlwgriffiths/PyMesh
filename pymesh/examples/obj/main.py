import os

from pymesh.obj import OBJ

def load( filename ):
	print 'Loading', filename
	# get our current directory
	path = os.path.join(
        os.path.dirname( __file__ ),
        '../data/obj',
        filename
        )

	obj = OBJ()
	obj.load( path )

def main():
	files = [
		'cessna.obj',
		'cornell_box.obj',
		]
	for filename in files:
		load( filename )

if __name__ == '__main__':
	main()

