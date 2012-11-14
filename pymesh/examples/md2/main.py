import os

from pymesh.md2 import MD2

def load_mesh( filename ):
    print 'Loading Raw', filename
    mesh = MD2()
    mesh.load( filename )

def main():
    # load all files in our data directory
    # get the path relative to our examples file
    path = os.path.join(
        os.path.dirname( __file__ ),
        '../data/md2'
        )
    # get the directory contents
    contents = os.listdir(path)

    # iterate through the contents and load
    # each file that is a .md5mesh or .md5anim file
    for filename in contents:
        name, extension = os.path.splitext( filename )

        # reattach our current directory
        path = os.path.join(
            os.path.dirname( __file__ ),
            '../data/md2',
            filename
            )

        if extension.lower() == '.md2':
            load_mesh( path )

if __name__ == '__main__':
    main()

