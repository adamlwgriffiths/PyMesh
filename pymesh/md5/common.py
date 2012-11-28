import math


def process_md5_buffer( buffer ):
    """Generator that processes a buffer and returns
    complete OBJ statements.

    Empty lines will be ignored.
    Comments will be ignored.
    Multi-line statements will be concatenated to a single line.
    Start and end whitespace will be stripped.
    """

    def md5_line( buffer ):
        """Generator that returns valid OBJ statements.

        Removes comments, whitespace and concatenates multi-line
        statements.
        """
        while True:
            line = buffer.next()

            # check if we've hit the end
            # EOF is signified by ''
            # whereas an empty line is '\n'
            if line == '':
                break

            # remove any whitespace
            line = line.strip()

            # remove any comments
            line = line.split( '//' )[ 0 ]

            # don't return empty lines
            if len( line ) <= 0:
                continue

            yield line

    # use our generator to remove comments and empty lines
    gen = md5_line( buffer )

    # iterate through each valid line of the OBJ file
    # and yield full statements
    for line in gen:
        yield line

def parse_to( buffer, keyword ):
    """Continues through the buffer until a line with a
    first token that matches the specified keyword.
    """
    while True:
        line = buffer.next()

        if line == '':
            return None

        values = line.split( None )
        if values[ 0 ] == keyword:
            return line

def compute_quaternion_w( x, y, z ):
    """Computes the Quaternion W component from the
    Quaternion X, Y and Z components.
    """
    # extract our W quaternion component
    w = 1.0 - (x ** 2) - (y ** 2) - (z ** 2)
    if w < 0.0:
        w = 0.0
    else:
        w = math.sqrt( w )
    return w


class MD5( object ):

    md5_version = 10

    def __init__( self ):
        super( MD5, self ).__init__()

        self.md5_version = None

    def load( self, filename ):
        """
        Reads the MD2 data from the existing
        specified filename.

        @param filename: the filename of the md2 file
        to load.
        """
        with open( filename, 'r' ) as f:
            self.load_from_buffer( f )
    
    def load_from_buffer( self, buffer ):
        raise NotImplementedError

