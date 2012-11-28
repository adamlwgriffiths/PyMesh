"""Processes MD5 Mesh files and returns mesh data in
an easy to read and process format.
"""

from collections import namedtuple

import numpy

from common import MD5, process_md5_buffer, parse_to, compute_quaternion_w


class MD5_SubMesh( object ):
    """Processes and stores MD5 mesh block data.

    Not to be confused with the MD5_Mesh class which parses .md5mesh
    files. This class parses the 'mesh {...}' block that is within
    a '.md5mesh' file.
    """

    vertex_layout = namedtuple(
        "MD5_Vertex",
        [
            'tcs',
            'start_weight',
            'weight_count'
            ]
        )

    weight_layout = namedtuple(
        "MD5_Weight",
        [
            'joint',
            'bias',
            'position'
            ]
        )
    

    class Vertices( object ):
        """Provides an iterator over MD5 SubMesh vertex data.
        """

        def __init__( self, submesh ):
            super( MD5_SubMesh.Vertices, self ).__init__()

            self.submesh = submesh

        def __iter__( self ):
            return self.next()

        def next( self ):
            for index in range( self.submesh.num_verts ):
                yield self.submesh.vertex( index )

    class Weights( object ):
        """Provides an iterator over MD5 SubMesh weight data.
        """

        def __init__( self, submesh ):
            super( MD5_SubMesh.Weights, self ).__init__()

            self.submesh = submesh

        def __iter__( self ):
            return self.next()

        def next( self ):
            for index in range( self.submesh.num_weights ):
                yield self.submesh.weight( index )

    def __init__( self, buffer, seek_to = True ):
        super( MD5_SubMesh, self ).__init__()

        self.shader = None

        # vertices
        self.tcs = None
        self.start_weights = None
        self.weight_counts = None

        # triangles
        self.tris = None

        # weights
        self.joints = None
        self.biases = None
        self.positions = None

        # load the joint data
        self._process_mesh( buffer, seek_to )

    @property
    def num_verts( self ):
        return len( self.tcs )

    @property
    def num_tris( self ):
        return len( self.tris )

    @property
    def num_weights( self ):
        return len( self.joints )

    @property
    def vertices( self ):
        """Returns an iterator that yields vertex_layout tuples.
        """
        return MD5_SubMesh.Vertices( self  )

    @property
    def weights( self ):
        """Returns an iterator that yields weight_layout tuples.
        """
        return MD5_SubMesh.Weights( self )

    def vertex( self, index ):
        """Returns a vertex_layout tuple for the specified vertex index.
        """
        return MD5_SubMesh.vertex_layout(
            self.tcs[ index ],
            self.start_weights[ index ],
            self.weight_counts[ index ]
            )

    def triangle( self, index ):
        """Returns a vertex indices for the triangle at the specified triangle index.
        """
        return self.tris[ index ]

    def weight( self, index ):
        """Returns a weight_layout tuple for the specified weight index.
        """
        return MD5_SubMesh.weight_layout(
            self.joints[ index ],
            self.biases[ index ],
            self.positions[ index ]
            )

    def _process_mesh( self, buffer, seek_to = True ):
        """Processes a single 'mesh' block.

        If 'seek_to' is True, the first step will be to seek to the next mesh block
        Otherwise it will begin parsing the mesh block where it is (looking for shader).
        """
        # find the 'mesh {' line
        if seek_to:
            parse_to( buffer, 'mesh' )

        self._process_shader( buffer )
        self._process_vertices( buffer )
        self._process_triangles( buffer )
        self._process_weights( buffer )

    def _process_shader( self, buffer ):
        """Extracts the 'shader' parameter from a mesh block.
        """
        line = parse_to( buffer, 'shader' )
        values = line.split( None, 1 )
        # remove quotes
        self.shader = values[ 1 ][ 1:-1 ]

    def _process_vertices( self, buffer ):
        """Processes the 'numverts' and 'vert' statements of a mesh block.
        """
        def process_vert( buffer ):
            values = buffer.split( None )

            # vert vertIndex ( texU texV ) weightIndex weightElem
            # we ignore the vertIndex as it is implied by order
            nil, nil, nil, tu, tv, nil, start_weight, weight_count = values

            tu, tv = float( tu ), float( tv )
            start_weight = int( start_weight )
            weight_count = int( weight_count )
            return ( tu, tv, start_weight, weight_count )

        line = parse_to( buffer, 'numverts' )
        values = line.split( None, 1 )
        num_verts = int( values[ 1 ] )

        self.tcs = numpy.empty( (num_verts, 2), dtype = 'float' )
        self.start_weights = numpy.empty( num_verts, dtype = 'int' )
        self.weight_counts = numpy.empty( num_verts, dtype = 'int' )

        # process the vertices
        for index in range( num_verts ):
            tu, tv, start_weight, weight_count = process_vert( buffer.next() )

            self.tcs[ index ] = [ tu, tv ]
            self.start_weights[ index ] = start_weight
            self.weight_counts[ index ] = weight_count

    def _process_triangles( self, buffer ):
        """Processes the 'numvtris' and 'tri' statements of a mesh block.
        """
        def process_tri( buffer ):
            values = buffer.split( None )

            # tri triIndex vertIndex1 vertIndex2 vertIndex3
            # we ignore the triIndex as it is implied by order
            nil, nil, v1, v2, v3 = values

            v1, v2, v3 = int( v1 ), int( v2 ), int( v3 )
            return ( v1, v2, v3 )

        line = parse_to( buffer, 'numtris' )
        values = line.split( None, 1 )
        num_tris = int( values[ 1 ] )

        self.tris = numpy.array(
            [
                process_tri( buffer.next() )
                for num in range( num_tris )
                ],
            dtype = 'float'
            )

    def _process_weights( self, buffer ):
        """Processes the 'numweights' and 'weight' statements of a mesh block.
        """
        def process_weight( buffer ):
            values = buffer.split( None )

            # weight weightIndex jointIndex weightValue ( xPos yPos zPos )
            # we ignore the weightIndex as it is implied by order
            nil, nil, joint, bias, nil, pos_x, pos_y, pos_z, nil = values

            joint = int( joint )
            bias = float( bias )
            pos_x, pos_y, pos_z = float( pos_x ), float( pos_y ), float( pos_z )
            return (
                joint,
                bias,
                ( pos_x, pos_y, pos_z )
                )

        line = parse_to( buffer, 'numweights' )
        values = line.split( None, 1 )
        num_weights = int( values[ 1 ] )

        self.joints = numpy.empty( num_weights, dtype = 'int' )
        self.biases = numpy.empty( num_weights, dtype = 'float' )
        self.positions = numpy.empty( (num_weights, 3), dtype = 'float' )

        for index in range( num_weights ):
            joint, bias, position = process_weight( buffer.next() )

            self.joints[ index ] = joint
            self.biases[ index ] = bias
            self.positions[ index ] = position


class MD5_Joints( object ):
    """Processes and stores MD5 Mesh joint data.

    This data is parse from the 'joints { ... }' block inside a '.md5mesh'
    file.

    The object is usable as an iterator.
    Ie.
    for joint in joints:
        print joint.name, joint.parent, joint.position, joint.orientation
    """

    joint_layout = namedtuple(
        "MD5_Joint",
        [
            'name',
            'parent',
            'position',
            'orientation'
            ]
        )
    
    def __init__( self, buffer, num_joints, seek_to = True ):
        super( MD5_Joints, self ).__init__()

        self.names = None
        self.parents = None
        self.positions = None
        self.orientations = None

        # load the joint data
        self._process_joints( buffer, num_joints, seek_to )

    def __iter__( self ):
        return self.next()

    def next( self ):
        for index in range( self.num_joints ):
            yield self.joint( index )

    def joint( self, index ):
        """Returns a joint_layout tuple for the specified joint index.
        """
        return MD5_Joints.joint_layout(
            self.names[ index ],
            self.parents[ index ],
            self.positions[ index ],
            self.orientations[ index ],
            )

    @property
    def num_joints( self ):
        return len( self.names )

    def _process_joints( self, buffer, num_joints, seek_to = True ):
        """Processes the joint block.
        Will simply iterate over 'self.num_joints' lines.
        This should be valid as any invalid lines or comments will be
        removed by our pre-parser 'process_md5_buffer'.

        Joints follow the format:
        "boneName" parentIndex ( xPos yPos zPos ) ( xOrient yOrient zOrient )

        parentIndex >= -1
        -1 indicates the current joint is the root joint.

        orientation is a quaternion.
        The W component is derrived from the x,y,z components.

        Returns a joint_layout named tuple.
        Parent is the parentIndex value.
        Position is in the format [x, y, z].
        Quaternion is in the format [x, y, z, w].
        """

        def process_joint( buffer ):
            """Processes a single joint statement
            """
            # split on whitespace
            values = buffer.split( None )

            # extract values
            # "boneName" parentIndex ( xPos yPos zPos ) ( xOrient yOrient zOrient )
            name, parent, nil, pos_x, pos_y, pos_z, nil, nil, quat_x, quat_y, quat_z, nil = values

            # remove quotes from name
            name = name[ 1:-1 ]

            # convert to appropriate type
            parent = int( parent )
            pos_x = float( pos_x )
            pos_y = float( pos_y )
            pos_z = float( pos_z )
            quat_x = float( quat_x )
            quat_y = float( quat_y )
            quat_z = float( quat_z )
            quat_w = compute_quaternion_w( quat_x, quat_y, quat_z )

            return (
                name,
                parent,
                (pos_x, pos_y, pos_z),
                (quat_x, quat_y, quat_z, quat_w)
                )

        # find the 'joints {' line
        if seek_to:
            parse_to( buffer, 'joints' )

        self.names = []
        self.parents = numpy.empty( (num_joints), dtype = 'int' )
        self.positions = numpy.empty( (num_joints, 3), dtype = 'float' )
        self.orientations = numpy.empty( (num_joints, 4), dtype = 'float' )

        # iterate through our specified number of joints
        for index in range( num_joints ):
            name, parent, position, orientation = process_joint( buffer.next() )

            self.names.append( name )
            self.parents[ index ] = parent
            self.positions[ index ] = position
            self.orientations[ index ] = orientation


class MD5_Mesh( MD5 ):
    """

    The MD5 file is expected to be in the proper layout.
    Values must be ordered as they are in the MD5 definition.
    For example:

    MD5Version 10

    numJoints N
    numMeshes N

    joints {
        "name" -1 ( 0 0 0 ) ( 0.0, 0.0, 0.0 )
        ...
    }

    mesh{
        shader "xyz"
        numverts N
        vert 0 ( 0.0 0.0 0.0 ) 1 1
        ...

        numtris N
        tri 0 0 1 2
        ...

        numweights N
        weight 0 1 1.0 ( 1.0 1.0 1.0 )
        ...
    }

    If any values are out of order (weights before tris) then the
    the result will be undefined.

    Comments will be automatically stripped and ignored.
    Extra commenting will not affect the parsing of the file.
    
    As long as the values are in the appropriate order, any extraneous
    white space or commenting between the values will not affect the
    parsing of the file.
    
    Bracketed values, ( ), MUST have a space between the brackets and
    the values.
    """

    def __init__( self ):
        super( MD5_Mesh, self ).__init__()

        self.md5_version = None
        self.joints = None
        self.meshes = None

    @property
    def num_joints( self ):
        return self.joints.num_joints

    @property
    def num_meshes( self ):
        return len( self.meshes )

    @property
    def num_verts( self ):
        total = 0
        for mesh in self.meshes:
            total += mesh.num_verts
        return total

    @property
    def num_tris( self ):
        total = 0
        for mesh in self.meshes:
            total += mesh.num_tris
        return total

    def joint( self, index ):
        return self.joints.joint( index )

    def mesh( self, index ):
        return self.meshes[ index ]

    def load_from_buffer( self, buffer ):
        """Reads the MD5 data from a stream object.

        Can be called instead of load() if data
        is not present in a file.

        @param f: the stream object, usually a file.
        """
        statements = process_md5_buffer( buffer )

        try:
            self._process_buffer( statements )
        except Exception as e:
            # clear our data
            self.md5_version = None
            self.joints = None
            self.meshes = None
            raise

    def _process_buffer( self, buffer ):
        """Processes the MD5 Mesh file from the specified buffer.
        """
        # Processes the MD5 Mesh header.
        line = parse_to( buffer, 'MD5Version' )
        values = line.split( None, 1 )
        self.md5_version = int( values[ 1 ] )

        if self.md5_version != MD5.md5_version:
            raise ValueError(
                "MD5 version is incorrect: expected '%i', found '%i'" % (
                    MD5.version,
                    self.md5_version
                    )
                )

        # we ignore command line
        # this is only present in Doom 3 MD5's

        line = parse_to( buffer, 'numJoints' )
        values = line.split( None, 1 )
        num_joints = int( values[ 1 ] )

        line = parse_to( buffer, 'numMeshes' )
        values = line.split( None, 1 )
        num_meshes = int( values[ 1 ] )

        # process joints
        self.joints = MD5_Joints( buffer, num_joints )

        # process meshes
        # each mesh is processed individually
        self.meshes = [
            MD5_SubMesh( buffer )
            for num in range( num_meshes )
            ]
