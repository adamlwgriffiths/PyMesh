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
	# load all .obj files in our data directory
	# get the path relative to our examples file
	path = os.path.join(
        os.path.dirname( __file__ ),
        '../data/obj'
        )
	# get the directory contents
	contents = os.listdir(path)

	# iterate through the contents and load
	# each file that is a .obj file
	for filename in contents:
		name, extension = os.path.splitext( filename )
		
		if extension.lower() == '.obj':
			load( filename )

if __name__ == '__main__':
	main()

