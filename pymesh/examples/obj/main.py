import os

from pymesh.obj import OBJ


def main():
	# get our current directory
	path = os.path.join(
            os.path.dirname( __file__ ),
            '../data/obj/cessna.obj'
            )

	obj = OBJ()
	obj.load( path )

if __name__ == '__main__':
	main()

