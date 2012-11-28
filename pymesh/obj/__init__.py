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
import re
from string import Template
import Queue

from pyglet.gl import *


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


class OBJ_Loader( object ):

    def parse_statement( self, statement ):
        """Processes the passed in statement.

        This will call the appropriate member function
        for the statement dynamically.
        Member functions must be in the form:
        _parse_%s( self, statement )
        where %s is the statement type.
        Eg.
        _parse_vt( self, statement )
        will parse texture coordinates.

        If an appropriate member function is not found
        nothing will be done and a statement will be
        printed.

        This method does not permit statements beginning with
        invalid function characters to be passed through.
        This includes comments (#).

        Comments and empty lines should not be passed to this
        function.
        'call' statements should also be handled outside
        this function.

        Can throw NotImplementedError for unimplemented features,
        AssertError for programmatical errors and other exceptions
        for malformed or unexpected data.
        """
        # get the statement type
        values = statement.split()

        type = values[ 0 ]
        if len(values) > 1:
            values = values[ 1: ]
        else:
            # no values, so empty our arg list
            values = []

        # check if we have a function that handles this type of value
        # all parse functions are named _parse_$ where $ is
        # the statement type
        func = getattr( self, '_parse_%s' % type, None )
        if func != None:
            func( statement )
        else:
            raise NotImplementedError(
                'Command "%s" is unknown' % type
                )

    def process_filename_list( self, values ):
        # filenames are normally split by whitespace
        # but the specification also allows for files with spaces in them
        # so we need to see if a value doesn't end with an extension
        # if not, concatenate it with the next value
        return re.split( r'\W+\.\W+', values )


class OBJ_Material( OBJ_Loader ):
    """
    http://people.sc.fsu.edu/~jburkardt/data/mtl/mtl.html
    http://paulbourke.net/dataformats/mtl/

    Supported material statements:

    newmtl name
    Begins a new material

    Ka r g b
    Defines the ambient color of the material to be (r,g,b).
    The default is (0.2,0.2,0.2);

    Kd r g b
    Defines the diffuse color of the material to be (r,g,b).
    The default is (0.8,0.8,0.8);

    Ks r g b
    Defines the specular color of the material to be (r,g,b).
    This color shows up in highlights.
    The default is (1.0,1.0,1.0);

    d alpha
    Defines the transparency of the material to be alpha.
    The default is 1.0 (not transparent at all)
    Some formats use Tr instead of d;

    d -halo alpha
    Specifies that a dissolve is dependent on the surface orientation 
    relative to the viewer.

    Tr alpha
    Remaps to 'd'.

    Ns s
    Defines the shininess of the material to be s. The default is 0.0;

    illum n
    Denotes the illumination model used by the material.
    Valid values are:
    - 1: indicates a flat material with no specular highlights,
        so the value of Ks is not used.
    - 2: denotes the presence of specular highlights,
        so a specification for Ks is required.

    Ni n
    Specifies the optical density for the surface.  This is also known as 
    index of refraction.
    "optical_density" is the value for the optical density.  The values can 
    range from 0.001 to 10.  A value of 1.0 means that light does not bend 
    as it passes through an object.  Increasing the optical_density 
    increases the amount of bending.  Glass has an index of refraction of 
    about 1.5.  Values of less than 1.0 produce bizarre results and are not 
    recommended.

    sharpness value
    Specifies the sharpness of the reflections from the local reflection 
    map.  If a material does not have a local reflection map defined in its 
    material definition, sharpness will apply to the global reflection map 
    defined in PreView.
     
     "value" can be a number from 0 to 1000.  The default is 60.  A high 
    value results in a clear reflection of objects in the reflection map.
     Tip    Sharpness values greater than 100 map introduce aliasing effects 
    in flat surfaces that are viewed at a sharp angle

    map_Ka filename
    names a file containing a texture map,
    which should just be an ASCII dump of RGB values;

    map_Kd -options args filename
    Specifies that a color texture file or color procedural texture file is 
    linked to the diffuse reflectivity of the material.  During rendering, 
    the map_Kd value is multiplied by the Kd value.

    map_Ks -options args filename
    Specifies that a color texture file or color procedural texture file is 
    linked to the specular reflectivity of the material.  During rendering, 
    the map_Ks value is multiplied by the Ks value.

    map_Ns -options args filename
    Specifies that a scalar texture file or scalar procedural texture file 
    is linked to the specular exponent of the material.  During rendering, 
    the map_Ns value is multiplied by the Ns value.

    map_d -options args filename
     Specifies that a scalar texture file or scalar procedural texture file 
    is linked to the dissolve of the material.  During rendering, the map_d 
    value is multiplied by the d value.

    decal -options args filename
    Specifies that a scalar texture file or a scalar procedural texture 
    file is used to selectively replace the material color with the texture 
    color.

    bump -options args filename
    Specifies that a bump texture file or a bump procedural texture file is 
    linked to the material.

    disp -options args filename
    Specifies that a scalar texture is used to deform the surface of an 
    object, creating surface roughness.

    map_aat on
    Turns on anti-aliasing of textures in this material without anti-
    aliasing all textures in the scene.


    r amount
    The reflectivity amount.
    Between 0.0 and 1.0.
    Defaults to 0.0.



    Unsupported Statements:

    refl -type sphere -options -args filename
    Specifies an infinitely large sphere that casts reflections onto the 
    material.  You specify one texture file.

    """
    
    def __init__( self ):
        super( OBJ_Material, self ).__init__()

        self.materials = {}
        self.textures = set([])

        self._current_material = None

    def _create_material( self ):
        """Creates an empty mesh with default values.

        All meshes begin as part of the default group.
        Any group statement will over-ride this.

        Points, lines and faces are a lists.
        Each value in the list is a tuple that represents the indicies
        for vertex, texture coordinate and normal data respectively.
        """
        return {
            'name':         None,
            'ambient':      [ 0.2, 0.2, 0.2 ],
            'diffuse':      [ 0.8, 0.8, 0.8 ],
            'specular':     [ 1.0, 1.0, 1.0 ],
            'alpha':        1.0,
            'halo':         1.0,
            'shine':        0.0,
            'illum':        1,
            'sharpness':    60,
            'reflectivity': 0.0,
            'density':      None,
            'anti-alias':   False,
            'textures':     {
                'ambient':  None,
                'diffuse':  None,
                'specular': None,
                'shine':    None,
                'bump':     None,
                'displacement': None,
                'decal':    None,
                },
            }

    def _parse_newmtl( self, statement ):
        # there should only be 1 name value
        # but the value can have a space in it
        type, value = statement.split( None, 1 )

        # create a new material
        # and set it as the current one
        # if we don't have one, create one
        self._current_material = self._create_material()

        # add it to the list of meshes
        self._current_material['name'] = value

        # add it to the list of meshes
        self.materials[ value ] = self._current_material

    def _parse_Ka( self, statement ):
        type, values = statement.split( None, 1 )
        red, green, blue = values.split()
        
        self._current_material['ambient'] = [
            float(red),
            float(green),
            float(blue)
            ]

    def _parse_Kd( self, statement ):
        type, values = statement.split( None, 1 )
        red, green, blue = values.split()
        
        self._current_material['diffuse'] = [
            float(red),
            float(green),
            float(blue)
            ]

    def _parse_Ks( self, statement ):
        type, values = statement.split( None, 1 )
        red, green, blue = values.split()
        
        self._current_material['specular'] = [
            float(red),
            float(green),
            float(blue)
            ]

    def _parse_Tr( self, statement ):
        # there should only be 1 name value
        # but there may be a '-halo' in the middle
        type, value = statement.split( None, 1 )

        value = value.split( None, 1 )
        if len(value) == 1:
            self._current_material['alpha'] = float(value[ 0 ])
        else:
            if value[ 0 ] == '-halo':
                self._current_material['halo'] = float(value[ 1 ])

    def _parse_d( self, statement ):
        # redirect to Tr
        return self._parse_Tr( statement )

    def _parse_Ns( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        self._current_material['shine'] = float(value)

    def _parse_Ni( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        self._current_material['density'] = float(value)

    def _parse_illum( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        self._current_material['illum'] = int(value)

    def _parse_map_Ka( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        # TODO: handle texture options

        self._current_material['textures']['ambient'] = value

        # add to our global texture set
        self.textures.add( value )

    def _parse_map_Kd( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        # TODO: handle texture options

        self._current_material['textures']['diffuse'] = value

        # add to our global texture set
        self.textures.add( value )

    def _parse_map_Ks( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        # TODO: handle texture options

        self._current_material['textures']['specular'] = value

        # add to our global texture set
        self.textures.add( value )

    def _parse_map_Ns( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        # TODO: handle texture options

        self._current_material['textures']['shine'] = value

        # add to our global texture set
        self.textures.add( value )

    def _parse_map_d( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        # TODO: handle texture options

        self._current_material['textures']['shine'] = value

        # add to our global texture set
        self.textures.add( value )

    def _parse_disp( self, statement ):
        # TODO: handle texture options

        self._current_material['textures']['displacement'] = value

        # add to our global texture set
        self.textures.add( value )

    def _parse_decal( self, statement ):
        # TODO: handle texture options

        self._current_material['textures']['decal'] = value

        # add to our global texture set
        self.textures.add( value )

    def _parse_bump( self, statement ):
        # TODO: handle texture options

        self._current_material['textures']['bump'] = value

        # add to our global texture set
        self.textures.add( value )

    def _parse_sharpness( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        self._current_material['sharpness'] = int(value)

    def _parse_map_aat( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        if value == 'on':
            self._current_material['anti-alias'] = True
        elif value == 'off':
            self._current_material['anti-alias'] = False

    def _parse_r( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        self._current_material['reflectivity'] = float(value)

    def _parse_refl( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )


class OBJ_Mesh( OBJ_Loader ):
    """
    Unsupported General Statements:
    csh [-]command
    Executes a C-shell unix command.
    Prefixing the command with a dash (-) ignores any errors.



    Supported Vertex data Statements:
    Vertices
    v x y z [w]
    Values are floating point.
    Defaults:
        w = 1.0
    
    Normals
    vn i j k
    Values are floating point.

    Texture coordinates
    vt u [v] [w]
    Values are integers or floats.
    Defaults:
        v = 0
        w = 0



    Unsupported Vertex data Statements:
    vp u v [w]
    a point on a curve or mesh.



    Unsupported Free-form curve/mesh attributes:
    cstype rat type
    deg degu degv
    bmat u matrix
    bmat v matrix
    step stepu stepv



    Supported Elements:
    Faces
    Vertices only
    f v(1) v(2) ... v(n)

    Vertices and Texture coordinates
    f v(1)/vt(1) v(2)/vt(2) ... v(n)/vt(n)

    Vertices, Texture Coordinates and Normals
    f v(1)/vt(1)/vn(1) v(2)/vt(2)/vn(2) ... v(n)/vt(n)/vn(n)

    Vertices and Normals
    f v(1)//vn(1) v(2)//vn(2) ... v(n)//vn(n)
    Specifies the indices of vertices to be rendered as a polygon.
    A negative value indicates an indice from the end of the currently
    specified list of vertices, texture coordinates or normals.
    Not the end of the final list.

    p v(1) v(2) ... v(n)
    Specifies the indices of vertices to be rendered as points.
    A negative value indicates an indice from the end of the currently
    specified list of vertices, texture coordinates or normals.
    Not the end of the final list.

    l v(1) v(2) ... v(n)
    l v(1)/vt(1) v(2)/vt(2) ... v(n)/vt(n)
    specifies the indices of vertices to be rendered as points.
    A negative value indicates an indice from the end of the currently
    specified list of vertices, texture coordinates or normals.
    Not the end of the final list.



    Unsupported Elements:
    curv u0 u1 v1 v2 ...
    curv2 vp1 vp2 vp3 ...
    surf s0 s1 t0 t1 v(1)/vt(1)/vn(1) v(2)/vt(2)/vn(2) ... v(n)/vt(n)/vn(n)



    Unsupported Free-form curve/mesh body statements:
    parm u p1 p2 p3 ...
    parm v p1 p2 p3 ...
    trim u0 u1 curv2d u0 u1 curv2d ...
    hole u0 u1 curv2d u0 u1 curv2d ...
    scrv u0 u1 curv2d u0 u1 curv2d ...
    sp vp1 vp ...
    end



    Unsupported connectivity between free-form meshes
    con surf_1 q0_1 q1_1 curv2d_1  surf_2 q0_2 q1_2 curv2d_2



    Supported Grouping statements:
    o name
    Defines the name of the objects that follow.
    There is no default.

    g name(1) [name(2)] ... [name(n)]
    Specifies the group name of the following geometry.
    Specifying multiple names makes the geometry part of all of those groups.
    The default group name is 'default'.
    
    s [1-n|off|0]
    Smoothing groups
    Makes the following geometry part of the specified smoothing group.
    A value of 0 or 'off' turns smoothing off.
    Vertex normals over-ride smoothing.



    Unsupported Grouping Statements:
    mg group_number res
    Merge (weld) vertices of meshes together within 'res' tolerance.



    Supported Display/render attributes:
    maplib filename1 filename2 ...
    Specifies texture map to load.

    usemap map_name/off

    mtllib filename(1) filename(2) ... filename(n)
    Specifies the filename of a material to load.

    usemtl name
    Assigns the specified material to the following geometry.

    shadow_obj filename
    The filename can be a .obj or .mod file.
    If no extension is given, .obj is assumed.

    trace_obj filename
    The filename can be a .obj or .mod file.
    If no extension is given, .obj is assumed.


    Unsupported Display/render attributes:
    bevel on/off
    c_interp on/off
    d_interp on/off
    lod level

    ctech technique resolution
    stech technique resolution



    Unsupported Superseded statements:
    bsp v1 v2 ... v16
    bzp v1 v2 ... v16
    cdc v1 v2 v3 v4 v5 ...
    cdp v1 v2 v3 ... v16
    res useg vseg
    fo v1 v2 ... vn



    Unsupported Non-standard statements:
    pl v1 v2 v3 v4
    Defines a plane with a position vertex and two normals:
    One for the rotation normal and one for the plane normal.

    sp v1 v2 v3
    Defines a spheres with a position vertex and two normals:
    one for the up normal and one for the equator normal.
    The length of either normal can be chosen for the sphere radius.

    lp v
    Defines a light at the specified point.
    Material sets the output parameters.

    lq v1 v2 v3 v4
    Defines a quad that emits light.

    ld v vn
    Defines a disc-shaped arealight source.
    The normal specifies the direction and size of the disc.

    c v1 v2 vn
    Used to define a simple camera.
    The 2 vertices define the camera position and the point the camera is focusing on.
    The normal defines the up vector.
    """

    default_group = 'default'


    def __init__( self ):
        super( OBJ_Mesh, self ).__init__()

        self.vertices = []
        self.texture_coords = []
        self.normals = []
        self.names = set([])
        self.groups = set([])
        self.materials = set([])
        self.textures = set([])
        self.meshes = []
        self.shadow = None
        self.trace = None

        self._current_mesh = None

    def _create_mesh( self ):
        """Creates an empty mesh with default values.

        All meshes begin as part of the default group.
        Any group statement will over-ride this.

        Points, lines and faces are a lists.
        Each value in the list is a tuple that represents the indicies
        for vertex, texture coordinate and normal data respectively.
        """
        return {
            'name':         None,
            'groups':       [ OBJ_Mesh.default_group ],
            'smoothing':    None,
            'material':     None,
            'texture':      None,
            'points':       [],
            'lines':        [],
            'faces':        [],
            }

    def _add_mesh_to_list( self, mesh ):
        self.meshes.append( mesh )

    def _ensure_current_mesh( self ):
        """Ensures there is a current mesh.
        If none is set, a new mesh is created.
        """
        # check if we don't have a mesh
        if not self._current_mesh:
            # if we don't have one, create one
            self._current_mesh = self._create_mesh()

            # add it to the list of meshes
            self._add_mesh_to_list( self._current_mesh )

    def _current_mesh_has_data( self ):
        """Checks if there is a current mesh and if
        one is set, that it has some polygon data.

        This is used by certain statements to see if they
        should create a new mesh or edit the existing mesh.
        """
        # if there is no current mesh, then there is no data set
        if not self._current_mesh:
            return False

        # if there is a mesh
        # the presence of any geometry indices indicates
        # we have data set
        if \
            len(self._current_mesh[ 'points' ]) > 0 or \
            len(self._current_mesh[ 'lines' ]) > 0 or \
            len(self._current_mesh[ 'faces' ]) > 0:
            return True

        # if we get this far, there is no data set
        return False

    def _push_current_mesh( self ):
        """Pushes the current mesh onto the stack.
        If no mesh is present, no mesh will be pushed
        and the current mesh will be set to an empty
        mesh.
        """
        if self._current_mesh:
            # duplicate ourself
            self._current_mesh = self._current_mesh.copy()
            # copy the current mesh and push it into
            # our meshes list
            self._add_mesh_to_list( self._current_mesh )
        else:
            # create an empty mesh
            self._current_mesh = _create_mesh

    def _parse_v( self, statement ):
        type, values = statement.split( None, 1 )
        values = values.split()

        # convert to float and a list
        floats = map( float, values )

        # divide by W component if present
        if len(floats) == 4:
            w = 1.0 / floats[ 3 ]
            floats = [ value * 3 for value in floats[ :3 ] ]

        # append to our vertices
        # this will append a list inside our vertices list
        self.vertices.append( tuple(floats) )

    def _parse_vt( self, statement ):
        type, values = statement.split( None, 1 )
        values = values.split()

        # convert to float and a list
        floats = map( float, values )

        # append to our vertices
        # this will append a list inside our vertices list
        self.texture_coords.append( floats )

    def _parse_vn( self, statement ):
        type, values = statement.split( None, 1 )
        values = values.split()

        # convert to float and a list
        floats = map( float, values )

        # divide by W component if present
        if len(floats) == 4:
            div = 1.0 / floats[ 3 ]
            floats[ 0 ] *= div
            floats[ 1 ] *= div
            floats[ 2 ] *= div
            floats = floats[ :3 ]

        # append to our vertices
        # this will append a list inside our vertices list
        self.normals.append( floats )

    def _convert_indice( self, value ):
        """Converts a parsed indice value to an absolute
        index. Also handles '' and None values that result
        from string splitting or list buffering.
        """
        # convert from offset to absolute indice
        if value == None:
            return value
        elif value == '':
            return None
        else:
            value = int(value)
            # obj uses 1 based indices
            # so convert to 0 based
            if value > 0:
                value -= 1
            # check for relative indices
            # these are negative values
            elif value < 0:
                value = len( self.vertices ) + value
            else:
                # shouldn't be any 0 indices
                assert False
            return value

    def _convert_indices( self, values ):
        """Converts a list of OBJ indices in the format v/vt/vn
        into absolute indices.

        Each vertex returned will contain 3 values.
        No index is indicated by the None value.
        """
        # iterate through each set of vertices and
        # convert to a tuple of 3 values
        # () vertex, texture coord, normal )
        # this will be an absolute indice, or None
        # if no indice is provided
        # faces can have vertex, texture coord and normal
        # it is invalid to mix vertex definitions
        # but we don't validate that here
        result = []

        for value in values:
            indices = value.split( '/' )

            # ensure we have 3 padded values
            indices.extend( [None] * (3 - len(indices)) )

            indices = map( self._convert_indice, indices )

            # append to mesh
            result.append( tuple(indices) )

        return result

    def _parse_p( self, statement ):
        type, values = statement.split( None, 1 )
        values = values.split()

        # ensure we have a current mesh
        self._ensure_current_mesh()
        
        # convert our indices to integers and absolute
        # values
        indices = self._convert_indices( values )

        # append to mesh
        self._current_mesh[ 'points' ].extend( indices )

    def _parse_l( self, statement ):
        type, values = statement.split( None, 1 )
        values = values.split()

        # ensure we have a current mesh
        self._ensure_current_mesh()

        # convert our indices to integers and absolute
        # values
        indices = self._convert_indices( values )

        # append to mesh
        self._current_mesh[ 'lines' ].append( tuple(indices) )

    def _parse_f( self, statement ):
        type, values = statement.split( None, 1 )
        values = values.split()

        # ensure we have a current mesh
        self._ensure_current_mesh()

        # convert our indices to integers and absolute
        # values
        indices = self._convert_indices( values )

        # append to mesh
        self._current_mesh[ 'faces' ].append( tuple(indices) )

    def _parse_o( self, statement ):
        # there should only be 1 name value
        type, value = statement.split()

        # push the current mesh and begin a new one
        # don't copy the mesh if we haven't actually set
        # any faces yet
        # this is because we may have multiple 'setup' statements
        if self._current_mesh_has_data():
            self._push_current_mesh()
        else:
            self._ensure_current_mesh()

        # set the name of the mesh
        self._current_mesh[ 'name' ] = value

        # add the name to our list
        self.names.add( value )

    def _parse_g( self, statement ):
        # g can have 0 arguments
        # if 0 arguments are supplied, the group is 'default'
        values = statement.split()
        type = values[ 0 ]

        if len(values) > 1:
            values = values[ 1: ]
        else:
            values = [ OBJ_Mesh.default_group ]

        # push the current mesh and begin a new one
        # don't copy the mesh if we haven't actually set
        # any faces yet
        # this is because we may have multiple 'setup' statements
        if self._current_mesh_has_data():
            self._push_current_mesh()
        else:
            self._ensure_current_mesh()

        # set the groups for the mesh
        self._current_mesh[ 'groups' ] = values

        # add the groups to our list
        self.groups.update( values )

    def _parse_s( self, statement ):
        # there should only be 1 smoothing group value
        type, value = statement.split()

        # push the current mesh and begin a new one
        # don't copy the mesh if we haven't actually set
        # any faces yet
        # this is because we may have multiple 'setup' statements
        if self._current_mesh_has_data():
            self._push_current_mesh()
        else:
            self._ensure_current_mesh()

        # set the smoothing group
        if value == 'off' or value == '0':
            # smoothing disabled
            self._current_mesh[ 'smoothing' ] = None
        else:
            # convert to int
            self._current_mesh[ 'smoothing' ] = int(value)

    def _parse_maplib( self, statement ):
        type, values = statement.split( None, 1 )

        # process the filenames
        filenames = self.process_filename_list( values )

        # store the specified texture maps in our list
        self.textures.update( filenames )

    def _parse_usemap( self, statement ):
        # there should only be 1 texture value
        # any spaces in the arguments are part of the
        # name itself and not delimiters
        type, value = statement.split( None, 1 )

        # push the current mesh and begin a new one
        # don't copy the mesh if we haven't actually set
        # any faces yet
        # this is because we may have multiple 'setup' statements
        if self._current_mesh_has_data():
            self._push_current_mesh()
        else:
            self._ensure_current_mesh()

        # set the name of the mesh
        self._current_mesh[ 'texture' ] = value

    def _parse_mtllib( self, statement ):
        type, values = statement.split( None, 1 )

        # process the filenames
        filenames = self.process_filename_list( values )

        # store the specified material files
        self.materials.update( filenames )

    def _parse_usemtl( self, statement ):
        # there should only be 1 texture value
        # any spaces in the arguments are part of the
        # name itself and not delimiters
        type, value = statement.split( None, 1 )

        # push the current mesh and begin a new one
        # don't copy the mesh if we haven't actually set
        # any faces yet
        # this is because we may have multiple 'setup' statements
        if self._current_mesh_has_data():
            self._push_current_mesh()
        else:
            self._ensure_current_mesh()

        # set the name of the mesh
        self._current_mesh[ 'material' ] = value

    def _parse_call( self, statement ):
        # this should be handled before we get here
        # this is a programming error and not a user error
        assert False

    def _parse_shadow_obj( self, statement ):
        # there should only be 1 shadow value
        type, values = statement.split()

        # set the name of the mesh
        self.shadow = values

    def _parse_trace_obj( self, statement ):
        # there should only be 1 shadow value
        type, values = statement.split()

        # set the name of the mesh
        self.trace = values

    def _parse_csh( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_vp( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_fo( self, statement ):
        # redirect to 'f' as per documentation
        self._parse_f( statement )

    def _parse_cstype( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_deg( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_bmat( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_step( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_curv( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_curv2( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_surf( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_parm( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_trim( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_hole( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_scrv( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_sp( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_end( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_con( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_mg( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_bevel( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_c_interp( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_d_interp( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_lod( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_ctech( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_stech( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_bsp( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_bzp( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_cdc( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_res( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_pl( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_sp( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_lp( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_lq( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_ld( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

    def _parse_c( self, statement ):
        raise NotImplementedError(
            '"%s" not supported' % statement.split( None, 1 )[ 0 ]
            )

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
        self.textures = []
        self.materials = []

    def load( self, filename ):
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
        for material in self.model.materials:
            # convert any further filenames to be relative to the file
            material = os.path.join( path, material )

            with open( material, 'r' ) as f:
                self._parse_obj_material( f )

    def _parse_obj_mesh( self, buffer, path ):
        # we will store our values as a property of this method
        # this lets the inner functions access them
        data = OBJ_Mesh()

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
