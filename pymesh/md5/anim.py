from collections import namedtuple

import numpy

import pymesh.utils as utils
from common import MD5, process_md5_buffer, parse_to, compute_quaternion_w


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
        The quaternion is a 4 tuple value (x,y,z,w)
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
                (quat_x, quat_y, quat_z, quat_w)
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
        The quaternion is a 4 tuple value (x,y,z,w)
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
                (quat_x, quat_y, quat_z, quat_w)
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

