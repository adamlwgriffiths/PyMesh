from collections import namedtuple

import numpy

import pymesh.utils as utils
from common import MD5, process_md5_buffer, parse_to, compute_quaternion_w


class MD5_Hierarchy( object ):

    joint_layout = namedtuple(
        'MD5_Joint',
        [
            'name',
            'parent',
            'flags',
            'start_index'
            ]
        )

    def __init__( self, buffer, num_joints, seek_to = True ):
        super( MD5_Hierarchy, self ).__init__()

        self.names = None
        self.parent_indices = None
        self.flags = None
        self.start_indices = None

        self._process_hierarchy( buffer, num_joints, seek_to )

    @property
    def num_joints( self ):
        return len( self.names )

    def joint( self, index ):
        return MD5_Hierarchy.joint_layout(
            self.names[ index ],
            self.parent_indices[ index ],
            self.flags[ index ],
            self.start_indices[ index ]
            )

    def __iter__( self ):
        return self.next()

    def next( self ):
        for index in range( self.num_joints ):
            yield self.joint( index )

    def _process_hierarchy( self, buffer, num_joints, seek_to ):
        """Processes the hierarchy block.
        Will simply iterate over 'self.num_joints' lines.
        This should be valid as any invalid lines or comments will be
        removed by our pre-parser 'process_md5_buffer'.

        Joints follow the format:
        "boneName" parentIndex flags start_index // parentName ( tX tY tZ qX qY qZ )

        Data to the right of the comment indicator is ignored.

        Returns a joint_layout named tuple.
        """

        def process_joint( buffer ):
            """Processes a single joint statement
            """
            # split on whitespace
            values = buffer.split( None )

            # extract values
            # "boneName" parentIndex flags startIndex
            name, parent_index, flags, start_index = values

            # remove quotes from name
            name = name[ 1:-1 ]

            # convert to appropriate type
            parent_index = int( parent_index )
            flags = int( flags )
            start_index = int( start_index )

            return (
                name,
                parent_index,
                flags,
                start_index
                )

        # find the 'hierarchy {' line
        if seek_to:
            parse_to( buffer, 'hierarchy' )

        #
        # TODO: convert this to a single N * 3 array and then extract using slices
        #
        self.names = []
        self.parent_indices = numpy.empty( num_joints, dtype = 'int' )
        self.flags = numpy.empty( num_joints, dtype = 'int' )
        self.start_indices = numpy.empty( num_joints, dtype = 'int' )

        # iterate through our specified number of joints
        for index in range( num_joints ):
            name, parent_index, flags, start_index = process_joint( buffer.next() )

            self.names.append( name )
            self.parent_indices[ index ] = parent_index
            self.flags[ index ] = flags
            self.start_indices[ index ] = start_index


class MD5_Bounds( object ):

    def __init__( self, buffer, num_frames, seek_to = True ):
        super( MD5_Bounds, self ).__init__()

        self.bounds = None

        self._process_bounds( buffer, num_frames, seek_to )

    @property
    def num_bounds( self ):
        return len( self.bounds )

    def bounds( self, index ):
        return self.bounds[ index ]

    def __iter__( self ):
        return self.next()

    def next( self ):
        for index in range( self.num_bounds ):
            yield self.bounds[ index ]

    def _process_bounds( self, buffer, num_frames, seek_to ):
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
            x1, y1, z1 = float( x1 ), float( y1 ), float( z1 )
            x2, y2, z2 = float( x2 ), float( y2 ), float( z2 )

            return (
                (x1, y1, z1),
                (x2, y2, z2)
                )

        # find the 'bounds {' line
        if seek_to:
            parse_to( buffer, 'bounds' )

        # iterate through our specified number of joints
        self.bounds = numpy.array(
            [
                process_bounds( buffer.next() )
                for num in range( num_frames )
                ],
            dtype = 'float'
            )


class MD5_BaseFrame( object ):

    bone_layout = namedtuple(
        'MD5_Bone',
        [
            'position',
            'orientation'
            ]
        )

    def __init__( self, buffer, num_joints, seek_to = True ):
        super( MD5_BaseFrame, self ).__init__()

        self.positions = None
        self.orientations = None

        self._process_base_frame( buffer, num_joints, seek_to )

    @property
    def num_bones( self ):
        return len( self.positions )

    def bone( self, index ):
        return MD5_BaseFrame.bone_layout(
            self.positions[ index ],
            self.orientations[ index ]
            )

    def __iter__( self ):
        return self.next()

    def next( self ):
        for index in range( self.num_bones ):
            yield self.bone( index )

    def _process_base_frame( self, buffer, num_joints, seek_to = True ):
        """Processes the baseframe block.
        Will simply iterate over 'self.num_joints' lines.
        This should be valid as any invalid lines or comments will be
        removed by our pre-parser 'process_md5_buffer'.

        Joints follow the format:
        ( xPos yPos zPos ) ( xOrient yOrient zOrient )

        Returns a tuple that contains a vertex and a quaternion.
        The vertex is a 3 value tuple.
        The quaternion is a 4 tuple value (x,y,z,w)
        The W component is calculated based on the x,y,z values.
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
            pos_x, pos_y, pos_z = float( pos_x ), float( pos_y ), float( pos_z )
            quat_x, quat_y, quat_z = float( quat_x ), float( quat_y ), float( quat_z )

            # calculate quaternion W value
            quat_w = compute_quaternion_w( quat_x, quat_y, quat_z )

            return (
                (pos_x, pos_y, pos_z),
                (quat_x, quat_y, quat_z, quat_w)
                )

        # find the 'baseframe {' line
        if seek_to:
            parse_to( buffer, 'baseframe' )

        self.positions = numpy.empty( (num_joints, 3 ), dtype = 'float' )
        self.orientations = numpy.empty( (num_joints, 4 ), dtype = 'float' )

        # iterate through our specified number of joints
        for position, orientation in zip( self.positions, self.orientations ):
            position[:], orientation[:] = process_bone( buffer.next() )


class MD5_Frame( object ):

    def __init__( self, buffer, seek_to = True ):
        super( MD5_Frame, self ).__init__()

        self.values = None

        self._process_frame( buffer, seek_to )

    @property
    def num_animated_components( self ):
        return self.values.size

    def value( self, index ):
        return self.values[ index ]

    def _process_frame( self, buffer, seek_to = True ):
        """Processes a frame block.

        The format specifies that there are 'self.num_animated_components' float
        values. It does not specify how many lines (which would be nicer).
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

            return values

        # find the 'hierarchy {' line
        if seek_to:
            parse_to( buffer, 'frame' )

        # iterate through our specified number of joints
        values = []

        while True:
            line = buffer.next()
            if line.startswith( '}' ):
                break
            values += list( process_bone( line ) )

        self.values = numpy.array( values, dtype = 'float' )


class MD5_Anim( MD5 ):


    def __init__( self ):
        super( MD5_Anim, self ).__init__()

        self.frame_rate = None
        self.hierarchy = None
        self.bounds = None
        self.base_frame = None
        self.frames = None

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
            self.frame_rate = None
            self.hierarchy = None
            self.bounds = None
            self.base_frame = None
            self.frames = None
            raise

    @property
    def num_frames( self ):
        return len( self.frames )

    def frame( self, index ):
        return self.frames[ index ]

    def _process_buffer( self, buffer ):
        """Processes the MD5 Mesh file from the specified buffer.
        """
        # Processes the MD5 Anim header.
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
        num_frames = int( values[ 1 ] )

        line = parse_to( buffer, 'numJoints' )
        values = line.split( None )
        num_joints = int( values[ 1 ] )

        line = parse_to( buffer, 'frameRate' )
        values = line.split( None )
        self.frame_rate = int( values[ 1 ] )

        # this value is basically useless
        # it is the number of floats that are provided per frame
        # as we read line-by-line, it's useless
        line = parse_to( buffer, 'numAnimatedComponents' )
        values = line.split( None )
        num_animated_components = int( values[ 1 ] )

        # process hierarchy
        self.hierarchy = MD5_Hierarchy( buffer, num_joints )

        # process bounds
        self.bounds = MD5_Bounds( buffer, num_frames )

        # process the base frame
        self.base_frame = MD5_BaseFrame( buffer, num_joints )

        # process frames
        # each frame is processed individually
        self.frames = [
            MD5_Frame( buffer )
            for index in range( num_frames )
            ]

        # validate our frame data
        for frame in self.frames:
            if frame.num_animated_components != num_animated_components:
                raise ValueError("Number of animated components doesn't match")

