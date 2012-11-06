"""Processes MD5 files and returns mesh data in
an easy to read and process format.
"""

import os
import math
import struct
import re
from collections import namedtuple, OrderedDict

import numpy

import pyrr.vector
import pyrr.quaternion

import utils


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
    w = 1.0 - (x * x) - (y * y) - (z * z)
    if w < 0.0:
        w = 0.0
    else:
        w = -math.sqrt( w )
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


    joint_layout = namedtuple(
        'MD5_Joint',
        [
            'name',
            'parent',
            'position',
            'orientation'
            ]
        )

    
    mesh_layout = namedtuple(
        'MD5_Mesh',
        [
            'shader',
            'numverts',
            # a list of vert_layout namedtules
            'verts',
            'numtris',
            # a list of 3 value lists, each sublist represents a triangle
            # and each value a vertex index
            'tris',
            'numweights',
            # a list of weight_layout namedtuples
            'weights',
            # the following values are calculated after loading
            # the raw MD5 data
            # a list of lists, each sublist contains a vertex
            'position',
            # a list of lists, each sublist contains a normal
            'normals'
            ]
        )

    vert_layout = namedtuple(
        'MD5_Vertex',
        [
            'tu',
            'tv',
            'weight_index',
            'weights_elements'
            ]
        )

    weight_layout = namedtuple(
        'MD5_Weight',
        [
            'joint',
            'weight',
            'position'
            ]
        )

    def __init__( self ):
        super( MD5_Mesh, self ).__init__()

        self.num_joints = None
        self.num_meshes = None

        self.joints = None
        self.meshes = None
    
    def load_from_buffer( self, buffer ):
        """
        Reads the MD5 data from a stream object.

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
            self.num_joints = None
            self.num_meshes = None

            self.joints = None
            self.meshes = None
            raise

    def _process_buffer( self, buffer ):
        """Processes the MD5 Mesh file from the specified buffer.
        """

        # process the header
        self._process_header( buffer )

        # process joints
        self.joints = self._process_joints( buffer )

        # process meshes
        # each mesh is processed individually
        self.meshes = [
            self._process_mesh( buffer )
            for num in range( self.num_meshes )
            ]

    def _process_header( self, buffer ):
        """Processes the MD5 Mesh header.
        """
        line = parse_to( buffer, 'MD5Version' )
        values = line.split( None )
        self.md5_version = int( values[ 1 ] )

        if self.md5_version != MD5.md5_version:
            raise ValueError(
                "MD5 version is incorrect, expected '%i', found '%i'" % (
                    MD5.version,
                    self.md5_version
                    )
                )

        # we ignore command line
        # this is only present in Doom 3 MD5's

        line = parse_to( buffer, 'numJoints' )
        values = line.split( None )
        self.num_joints = int( values[ 1 ] )

        line = parse_to( buffer, 'numMeshes' )
        values = line.split( None )
        self.num_meshes = int( values[ 1 ] )

    def _process_joints( self, buffer, seek_to = True ):
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
        Quaternion is in the format [w, x, y, z].
        """

        def process_joint( buffer ):
            """Processes a single joint statement
            """

            # split on whitespace
            values = buffer.split( None )

            # extract values
            # "boneName" parentIndex ( xPos yPos zPos ) ( xOrient yOrient zOrient )
            name, index, nil, pos_x, pos_y, pos_z, nil, nil, quat_x, quat_y, quat_z, nil = values

            # remove quotes from name
            name = name[ 1:-1 ]

            # convert to appropriate type
            index = int( index )
            pos_x = float(pos_x)
            pos_y = float(pos_y)
            pos_z = float(pos_z)
            quat_x = float(quat_x)
            quat_y = float(quat_y)
            quat_z = float(quat_z)
            quat_w = compute_quaternion_w( quat_x, quat_y, quat_z )

            return MD5_Mesh.joint_layout(
                name,
                index,
                (pos_x, pos_y, pos_z),
                (quat_w, quat_x, quat_y, quat_z)
                )

        # find the 'joints {' line
        if seek_to:
            parse_to( buffer, 'joints' )

        # iterate through our specified number of joints
        return [
            process_joint( buffer.next() )
            for num in range( self.num_joints )
            ]

    def _process_mesh( self, buffer, seek_to = True ):
        """Processes a single 'mesh' block.

        If 'seek_to' is True, the first step will be to seek to the next mesh block
        Otherwise it will begin parsing the mesh block where it is (looking for shader).
        """
        def process_vert( buffer ):
            values = buffer.split( None )

            # vert vertIndex ( texU texV ) weightIndex weightElem
            # we ignore the vertIndex as it is implied by order
            nil, nil, nil, tu, tv, nil, weight_index, weight_elements = values

            tu = float( tu )
            tv = float( tv )
            weight_index = int( weight_index )
            weight_elements = int( weight_elements )

            return MD5_Mesh.vert_layout(
                tu,
                tv,
                weight_index,
                weight_elements
                )

        def process_tri( buffer ):
            values = buffer.split( None )

            # tri triIndex vertIndex1 vertIndex2 vertIndex3
            # we ignore the triIndex as it is implied by order
            nil, nil, v1, v2, v3 = values

            v1 = int( v1 )
            v2 = int( v2 )
            v3 = int( v3 )

            return (v1, v2, v3)

        def process_weight( buffer ):
            values = buffer.split( None )

            # weight weightIndex jointIndex weightValue ( xPos yPos zPos )
            # we ignore the weightIndex as it is implied by order
            nil, nil, joint, weight, nil, pos_x, pos_y, pos_z, nil = values

            joint = int( joint )
            weight = float( weight )
            pos_x = float( pos_x )
            pos_y = float( pos_y )
            pos_z = float( pos_z )

            return MD5_Mesh.weight_layout(
                joint,
                weight,
                ( pos_x, pos_y, pos_z )
                )

        def generate_positions( vertex, weights, joints ):
            """
            C++ pseudo-code
            for ( int j = 0; j < vert.m_WeightCount; ++j )
            {
                Weight& weight = mesh.m_Weights[vert.m_StartWeight + j];
                Joint& joint = m_Joints[weight.m_JointID];
     
                // Convert the weight position from Joint local space to object space
                glm::vec3 rotPos = joint.m_Orient * weight.m_Pos;
     
                vert.m_Pos += ( joint.m_Pos + rotPos ) * weight.m_Bias;
            }
            """
            def process_weight( weight, joint ):
                """Takes the specified weight and joint
                and returns a vector for that joint.
                
                The vector is multiplied by the weight (bias).
                """
                rotated_vector = pyrr.quaternion.apply_to_vector(
                    joint.orientation,
                    weight.position
                    )

                joint_pos = numpy.array( joint.position )
                return (joint_pos + rotated_vector) * weight.weight

            # for each weight and joint (they are linked) that affects
            # the vertex, extract them and pass to our process function
            positions = numpy.array([
                process_weight(
                    weights[ vertex.weight_index + index ],
                    joints[ weights[ vertex.weight_index + index ].joint ]
                    )
                for index in range( vertex.weights_elements )
                ])

            # take all of the weighted values and sum them
            position = list(
                numpy.sum(
                    positions,
                    axis = 0,
                    dtype = 'float32'
                    )
                )

            return position

        def generate_normals( verts, tris ):
            #print verts
            np_verts = numpy.array( verts, dtype = 'float32' )

            # pull our the vertices
            # this will generate a list of vertex triples
            v = np_verts[ tris, : ]

            # we will normalise the result afterward in a single pass
            # for each triple, pull our the 0, 1 and 2 vertex
            # as their own list
            n = pyrr.vector.generate_normals(
                v[ :, 0, : ],
                v[ :, 1, : ],
                v[ :, 2, : ],
                normalise_result = False
                )

            # add our normals to the array
            normals = numpy.zeros( np_verts.shape, dtype = 'float32' )
            # the following line doesn't work due to numpy
            # but it's basically what we're doing
            #normals[ tris, : ] += n
            for tri, normal in zip(tris, n):
                normals[ tri[ 0 ] ] += normal
                normals[ tri[ 1 ] ] += normal
                normals[ tri[ 2 ] ] += normal

            # normalise our normal vectors
            # this will result in the average normal
            # being stored
            pyrr.vector.normalise( normals )

            return list(normals)


        shader = None
        num_verts = None
        num_tris = None
        num_weights = None

        verts = None
        tris = None
        weights = None

        # find the 'mesh {' line
        if seek_to:
            parse_to( buffer, 'mesh' )

        line = parse_to( buffer, 'shader' )
        values = line.split( None )
        # remove quotes
        shader = values[ 1 ][ 1:-1 ]

        line = parse_to( buffer, 'numverts' )
        values = line.split( None )
        num_verts = int( values[ 1 ] )

        # process the vertices
        verts = [
            process_vert( buffer.next() )
            for num in range( num_verts )
            ]

        line = parse_to( buffer, 'numtris' )
        values = line.split( None )
        num_tris = int( values[ 1 ] )
        tris = [
            process_tri( buffer.next() )
            for num in range( num_tris )
            ]

        line = parse_to( buffer, 'numweights' )
        values = line.split( None )
        num_weights = int( values[ 1 ] )
        weights = [
            process_weight( buffer.next() )
            for num in range( num_weights )
            ]

        # generate our vertex positions
        positions = [
            generate_positions( vert, weights, self.joints )
            for vert in verts
            ]

        # use the positions to generate normal data
        normals = generate_normals(
            positions,
            tris
            )

        return MD5_Mesh.mesh_layout(
            shader,
            num_verts,
            verts,
            num_tris,
            tris,
            num_weights,
            weights,
            positions,
            normals
            )


class MD5_Anim( MD5 ):

    joint_layout = namedtuple(
        'MD5_Joint',
        [
            'name',
            'parent',
            'num_components',
            'frame'
            ]
        )


    def __init__( self ):
        super( MD5_Anim, self ).__init__()

        self.num_frames = None
        self.num_joints = None
        self.frame_rate = None
        self.num_animated_components = None
    
    def load_from_buffer( self, buffer ):
        """
        Reads the MD5 data from a stream object.

        Can be called instead of load() if data
        is not present in a file.

        @param f: the stream object, usually a file.
        """
        statements = process_md5_buffer( buffer )

        try:
            self._process_buffer( statements )
        except Exception as e:
            # clear our data
            self.num_frames = None
            self.num_joints = None
            self.frame_rate = None
            self.num_animated_components = None
            raise

    def _process_buffer( self, buffer ):
        """Processes the MD5 Mesh file from the specified buffer.
        """

        # process the header
        self._process_header( buffer )

        # process hierarchy
        self.hierarchy = self._process_hierarchy( buffer )

        # process bounds
        self.bounds = self._process_bounds( buffer )

        # process the base frame
        self.base_frame = self._process_base_frame( buffer )

        # process frames
        # each frame is processed individually
        self.frames = [
            self._process_frame( buffer )
            for num in range( self.num_frames )
            ]

    def _process_header( self, buffer ):
        """Processes the MD5 Mesh header.
        """
        line = parse_to( buffer, 'MD5Version' )
        values = line.split( None )
        self.md5_version = int( values[ 1 ] )

        if self.md5_version != MD5.md5_version:
            raise ValueError(
                "MD5 version is incorrect, expected '%i', found '%i'" % (
                    MD5.version,
                    self.md5_version
                    )
                )

        # we ignore command line
        # this is only present in Doom 3 MD5's

        line = parse_to( buffer, 'numFrames' )
        values = line.split( None )
        self.num_frames = int( values[ 1 ] )

        line = parse_to( buffer, 'numJoints' )
        values = line.split( None )
        self.num_joints = int( values[ 1 ] )

        line = parse_to( buffer, 'frameRate' )
        values = line.split( None )
        self.frame_rate = int( values[ 1 ] )

        line = parse_to( buffer, 'numAnimatedComponents' )
        values = line.split( None )
        self.num_animated_components = int( values[ 1 ] )

    def _process_hierarchy( self, buffer, seek_to = True ):
        """Processes the hierarchy block.
        Will simply iterate over 'self.num_joints' lines.
        This should be valid as any invalid lines or comments will be
        removed by our pre-parser 'process_md5_buffer'.

        Joints follow the format:
        "boneName" parentIndex numComp frameIndex // parentName ( tX tY tZ qX qY qZ )

        Data to the right of the comment indicator is ignored.

        Returns a joint_layout named tuple.
        """

        def process_joint( buffer ):
            """Processes a single joint statement
            """

            # split on whitespace
            values = buffer.split( None )

            # extract values
            # "boneName" parentIndex numComp frameIndex
            name, index, num_components, frame_index = values

            # remove quotes from name
            name = name[ 1:-1 ]

            # convert to appropriate type
            index = int( index )
            num_components = int( num_components )
            frame_index = int( frame_index )

            return MD5_Anim.joint_layout(
                name,
                index,
                num_components,
                frame_index
                )

        # find the 'hierarchy {' line
        if seek_to:
            parse_to( buffer, 'hierarchy' )

        # iterate through our specified number of joints
        return [
            process_joint( buffer.next() )
            for num in range( self.num_joints )
            ]

    def _process_bounds( self, buffer, seek_to = True ):
        """Processes the bounds block.
        Will simply iterate over 'self.num_frames' lines.
        This should be valid as any invalid lines or comments will be
        removed by our pre-parser 'process_md5_buffer'.

        Joints follow the format:
        ( minX minY minZ ) ( maxX maxY maxZ )

        Returns a tuple that contains a 2 vertices.
        Each vertex is a 3 value tuple.
        For example:
        ( (0.0, 0.0, 0.0), (1.0, 1.0, 1.0) )
        """

        def process_bounds( buffer ):
            """Processes a single bounds statement
            """

            # split on whitespace
            values = buffer.split( None )

            # extract values
            # ( minX minY minZ ) ( maxX maxY maxZ )
            nil, x1, y1, z1, nil, nil, x2, y2, z2, nil = values

            # convert to appropriate type
            x1 = float( x1 )
            y1 = float( y1 )
            z1 = float( z1 )
            x2 = float( x2 )
            y2 = float( y2 )
            z2 = float( z2 )

            return (
                (x1, y1, z1),
                (x2, y2, z2)
                )

        # find the 'bounds {' line
        if seek_to:
            parse_to( buffer, 'bounds' )

        # iterate through our specified number of joints
        return [
            process_bounds( buffer.next() )
            for num in range( self.num_frames )
            ]

    def _process_base_frame( self, buffer, seek_to = True ):
        """Processes the baseframe block.
        Will simply iterate over 'self.num_joints' lines.
        This should be valid as any invalid lines or comments will be
        removed by our pre-parser 'process_md5_buffer'.

        Joints follow the format:
        ( xPos yPos zPos ) ( xOrient yOrient zOrient )

        Returns a tuple that contains a vertex and a quaternion.
        The vertex is a 3 value tuple.
        The quaternion is a 4 tuple value
        For example:
        ( (0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0) )
        """

        def process_bone( buffer ):
            """Processes a single bone statement
            """

            # split on whitespace
            values = buffer.split( None )

            # extract values
            # ( xPos yPos zPos ) ( xOrient yOrient zOrient )
            nil, pos_x, pos_y, pos_z, nil, nil, quat_x, quat_y, quat_z, nil = values

            # convert to appropriate type
            pos_x = float( pos_x )
            pos_y = float( pos_y )
            pos_z = float( pos_z )
            quat_x = float( quat_x )
            quat_y = float( quat_y )
            quat_z = float( quat_z )
            quat_w = compute_quaternion_w( quat_x, quat_y, quat_z )

            return (
                (pos_x, pos_y, pos_z),
                (quat_w, quat_x, quat_y, quat_z)
                )

        # find the 'baseframe {' line
        if seek_to:
            parse_to( buffer, 'baseframe' )

        # iterate through our specified number of joints
        return [
            process_bone( buffer.next() )
            for num in range( self.num_joints )
            ]

    def _process_frame( self, buffer, seek_to = True ):
        """Processes a frame block.

        The format specifies that there are 'self.num_animated_components' float
        values. It does not specify how many lines (which would be nicer).
        It is not trivial to perform this. So we will simply iterate until the
        end of a block marked with a line starting with '}'.

        This should be valid as any invalid lines or comments will be
        removed by our pre-parser 'process_md5_buffer'.

        Joints follow the format:
        xPos yPos zPos xOrient yOrient zOrient

        Each value is optional.

        Returns a tuple that contains a vertex and a quaternion.
        The vertex is a 3 value tuple.
        The quaternion is a 4 tuple value
        Be aware, that ANY of these values can be None.
        Once a single None value is found, all proceeding values
        will be None.
        A None value indicates that it should be inherited from
        the baseframe values.
        For example:
        ( (0.0, 0.0, 0.0), (1.0, 1.0, 1.0, 1.0) )
        ( (0.0, 0.0, None), (None, None, None, None) )
        """

        def process_bone( buffer ):
            """Processes a single bone statement
            """

            # split on whitespace
            values = buffer.split( None )

            # convert to float
            # do this to avoid issues converting None to float
            # when we add padding
            values = map( float, values )

            # extract values
            # xPos yPos zPos xOrient yOrient zOrient
            # because the values are optional, we need to use
            # our tuple extraction routine
            values = utils.extract_tuple( values, 6, None )

            # extract
            pos_x, pos_y, pos_z, quat_x, quat_y, quat_z = values

            quat_w = None
            if quat_x and quat_y and quat_z:
                quat_w = compute_quaternion_w( quat_x, quat_y, quat_z )

            return (
                (pos_x, pos_y, pos_z),
                (quat_w, quat_x, quat_y, quat_z)
                )

        # find the 'hierarchy {' line
        if seek_to:
            parse_to( buffer, 'frame' )

        # iterate through our specified number of joints
        bones = []
        while True:
            line = buffer.next()
            if line.startswith( '}' ):
                break
            bones.append( process_bone( line ) )

        return bones


