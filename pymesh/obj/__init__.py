"""Implements a Wavefront OBJ format loader.

OBJ References:
http://paulbourke.net/dataformats/obj/
http://www.martinreddy.net/gfx/3d/OBJ.spec
http://en.wikipedia.org/wiki/Wavefront_.obj_file
http://en.wikibooks.org/wiki/OpenGL_Programming/Modern_OpenGL_Tutorial_Load_OBJ
http://openglsamples.sourceforge.net/files/glut_obj.cpp

MTL References:
http://paulbourke.net/dataformats/mtl/
http://people.sc.fsu.edu/~jburkardt/data/mtl/mtl.html


Future optimisations:
Merge groups with the same:
    name, groups, material, texture and smoothing group
I attempted this by using a dictionary with the above values as a tuple for
the key, but this slowed down loading massively.
Ironically it didn't slow down loading in this file, but my conversion
to OpenGL. No idea how.
"""

import os
from string import Template
import Queue

from mesh import OBJ_Mesh
from material import OBJ_Material


class BufferStack( object ):
    """Provides an iterable method to read from a stack of buffers.

    Buffers can be pushed onto the stack, making this buffer the
    active buffer.
    Each call of readline, or iteration, will read the next line
    of the active buffer.

    This lets you read a file, then open another stream in the middle.
    Effectively injecting one buffer inside another without complex
    data manipulation.

    This is used by the OBJ loader when a 'call' statement is
    processessed to effectively 'inject' another file into the
    buffer.
    """

    class Iterator( object ):
        def __init__( self, buffer ):
            super( Iterator, self ).__init__()
            self.buffer = buffer

        def __iter__( self ):
            return self

        def next( self ):
            line = buffer.readline()
            if line:
                return line
            else:
                raise StopIteration

    def __init__( self ):
        super( BufferStack, self ).__init__()

        self.stack = Queue.LifoQueue()
        self.buffer = None

    def __iter__( self ):
        return BufferStack.Iterator( self )

    def readline( self ):
        while self.buffer:
            line = self.buffer.readline()

            if line == '':
                self._pop()
            else:
                return line

        # return EOF
        raise StopIteration

    def push( self, buffer ):
        if self.buffer:
            self.stack.put( self.buffer )
        self.buffer = buffer

    def _pop( self ):
        # pop the next buffer
        if not self.stack.empty():
            self.buffer = self.stack.get()
        else:
            self.buffer = None

class ArgumentBufferStack( BufferStack ):
    """Provides string replacement of lines that are
    read from the BufferStack.

    This implements variable replacement of OBJ files.
    Ie, $1 in the file becomes arg1.
    """

    def __init__( self ):
        super( ArgumentBufferStack, self ).__init__()

        self.args_stack = Queue.LifoQueue()
        self.args = None

    def readline( self ):
        line = super( ArgumentBufferStack, self ).readline()

        # perform argument replacement
        template = Template( line )
        line = template.substitute( self.args )

        return line

    def push_args( self, args ):
        """Pushes the args as the current buffer's arguement list.
        """
        if self.args:
            self.args_stack.push( self.args )
        # convert our arguments to a dictionary
        dict_args = {}
        for num, arg in zip( range(len(args)), args ):
            dict_args[ num ] = arg

        self.args = dict_args







def process_obj_buffer( buffer ):
    """Generator that processes a buffer and returns
    complete OBJ statements.

    Empty lines will be ignored.
    Comments will be ignored.
    Multi-line statements will be concatenated to a single line.
    Start and end whitespace will be stripped.
    """

    def obj_line( buffer ):
        """Generator that returns valid OBJ statements.

        Removes comments, whitespace and concatenates multi-line
        statements.
        """
        while True:
            line = buffer.readline()

            # check if we've hit the end
            # EOF is signified by ''
            # whereas an empty line is '\n'
            if line == '':
                break

            # remove any whitespace
            line = line.strip()

            if line.startswith( '#' ):
                continue

            if len( line ) <= 0:
                continue

            yield line

    # use our generator to remove comments and empty lines
    gen = obj_line( buffer )

    # iterate through each valid line of the OBJ file
    # and yield full statements
    for line in gen:
        # concatenate lines until we get a full statement
        while line.endswith( '\\' ):
            try:
                # remove the \ token
                # add some white space
                line = line[:-1].strip() + ' ' + gen.next()
            except:
                raise EOFError( 'Line had a continuation but no following line to concatenate with' )

        yield line


class OBJ( object ):
    """
    Loads a Wavefront OBJ formatted mesh.

    The Wavefront specification can be found here:
    http://www.martinreddy.net/gfx/3d/OBJ.spec

    General syntax:
    # comment
    Denotes a comment

    value value value \
    value value
    Indicates the values continue on the next line

    Supported General Statements:

    call filename.ext arg1 arg2 ...
    Injects the specified file at the current location in the file.
    The filename can be a .obj or .mod file.
    The extension must be specified.
    arg1 onwards specify arguments that are passed to the file.
    Arguments are replaced like in a unix file.
    $1 is replaced by arg1, $2 by arg2 and so on.

    For other supported and unsupported statements, see OBJ_Mesh.
    """
    
    def __init__( self ):
        super( OBJ, self ).__init__()

        self.model = None
        self.shadow = None
        self.trace = None
        self.textures = set([])
        self.materials = set([])

    def load( self, filename, ignore_smoothing_groups = True ):
        """
        Reads the OBJ data from the existing
        specified filename.

        @param filename: the filename of the OBJ file
        to load.
        """

        # extract the path of the original filename
        path = os.path.dirname( filename )

        with open( filename, 'r' ) as f:
            # process the main model
            self.model = self._parse_obj_mesh( f, path )

        # process any shadow objects
        self.shadow = None
        if self.model.shadow:
            # convert any further filenames to be relative to the file
            shadow = os.path.join( path, self.model.shadow )

            with open( shadow, 'r' ) as f:
                self.shadow = self._parse_obj_mesh( f, path )

        # process any trace objects
        self.trace = None
        if self.model.trace:
            # convert any further filenames to be relative to the file
            trace = os.path.join( path, self.model.trace )

            with open( trace, 'r' ) as f:
                self.trace = self._parse_obj_mesh( f, path )

        # process any materials
        self.textures = set([])
        self.materials = set([])
        for material_path in self.model.materials:
            # convert any further filenames to be relative to the file
            material_path = os.path.join( path, material_path )

            with open( material_path, 'r' ) as f:
                material = self._parse_obj_material( f )

            self.materials.add( material )

            # add the textures to our list of textures
            self.textures.update( material.textures )

    def _parse_obj_mesh( self, buffer, path, ignore_smoothing_groups = True ):
        # we will store our values as a property of this method
        # this lets the inner functions access them
        data = OBJ_Mesh( ignore_smoothing_groups )

        buffers = ArgumentBufferStack()
        buffers.push( buffer )
        buffers.push_args( [] )

        # pass the buffer stack to our statement parser
        # this will construct full statements from our data
        # and concatenate any multiple line statements into
        # complete statements
        statements = process_obj_buffer( buffers )

        # process the file
        for line in statements:
            # tokenize based on space
            # there are some statements with 0 parameters
            # such as  'g'
            # so we need to extract the specific values later
            values = line.split()

            # get the first word
            # this is the statement type
            type = values[ 0 ]
            if len(values) > 1:
                values = values[ 1: ]
            else:
                # no values, so empty our arg list
                values = []

            # check if the statement is a 'call' statement
            # we need to handle this ourselves
            if type == 'call':
                filename = values[ 0 ]
                args = []

                # extract our arguments
                if len(values) > 1:
                    args = values[ 1: ]

                # make filename relative to original
                filename = os.path.join( path, filename )

                # open it as a file and push into our read buffer
                f = open( filename, 'r' )
                statements.push( f )
                statements.push_args( args )

                # iterate again
                continue

            # pass to our obj parser
            try:
                data.parse_statement( line )
            except NotImplementedError as e:
                print e

        # zero the current mesh
        data._current_mesh = None

        return data

    def _parse_obj_material( self, buffer ):
        # we will store our values as a property of this method
        # this lets the inner functions access them
        data = OBJ_Material()

        # pass the buffer stack to our statement parser
        # this will construct full statements from our data
        # and concatenate any multiple line statements into
        # complete statements
        statements = process_obj_buffer( buffer )

        # process the file
        for line in statements:
            # pass to our obj parser
            try:
                data.parse_statement( line )
            except NotImplementedError as e:
                print e

        # zero the current mesh
        data._current_material = None

        return data

