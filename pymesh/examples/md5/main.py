import os

from pymesh.md5 import MD5_Mesh, MD5_Anim

def load_mesh( filename ):
    print 'Loading', filename

    md5 = MD5_Mesh()
    md5.load( filename )


def load_anim( filename ):
    print 'Loading', filename

    md5 = MD5_Anim()
    md5.load( filename )

def main():
    # load all md5 files in our data directory
    # get the path relative to our examples file
    path = os.path.join(
        os.path.dirname( __file__ ),
        '../data/md5'
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
            '../data/md5',
            filename
            )

        if extension.lower() == '.md5mesh':
            load_mesh( path )

        if extension.lower() == '.md5anim':
            load_anim( path )

if __name__ == '__main__':
    main()

