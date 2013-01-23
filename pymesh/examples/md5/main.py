import os

from pymesh.md5 import MD5_Mesh, MD5_Anim

def load_mesh( filename ):
    print 'Loading', filename

    md5 = MD5_Mesh()
    md5.load( filename )

    # print the data out for verification
    print 'version', md5.md5_version
    print 'num_joints', md5.num_joints
    print 'num_meshes', md5.num_meshes

    print 'joints'
    for joint in md5.joints:
        print '\tname', joint.name
        print '\tparent', joint.parent
        print '\tposition', joint.position
        print '\torientation', joint.orientation

    print 'meshes'
    for mesh in md5.meshes:
        print '\tshader', mesh.shader

        print '\tnumverts', mesh.num_verts
        for vert in mesh.vertices:
            print '\t\ttcs', vert.tcs
            print '\t\tstart_weight', vert.start_weight
            print '\t\tweight_count', vert.weight_count

        print '\tnumtris', mesh.num_tris
        for tri in mesh.tris:
            print '\t\ttri', tri

        print '\tnumweights', mesh.num_weights
        for weight in mesh.weights:
            print '\t\tjoint', weight.joint
            print '\t\tbias', weight.bias
            print '\t\tposition', weight.position


def load_anim( filename ):
    print 'Loading', filename

    md5 = MD5_Anim()
    md5.load( filename )

    print 'version', md5.md5_version
    print 'frame_rate', md5.frame_rate

    print 'hierarchy'
    print 'num_joints', md5.hierarchy.num_joints
    for joint in md5.hierarchy:
        print '\tname', joint.name
        print '\tparent', joint.parent
        print '\tnum_components', joint.num_components
        print '\tframe', joint.frame

    print 'bounds'
    print 'num_bounds', md5.bounds.num_bounds
    for bounds in md5.bounds:
        print '\tminimum', bounds[ 0 ]
        print '\tmaximum', bounds[ 1 ]

    print 'base frame'
    print 'num_bones', md5.base_frame.num_bones
    for bone in md5.base_frame:
        print '\tposition', bone.position
        print '\torientation', bone.orientation

    print 'frames'
    print 'num_frames', md5.num_frames
    for frame in md5.frames:
        print '\tjoints'
        print '\tnum_joints', frame.num_joints
        for joint in frame:
            print '\t\tposition', joint.position
            print '\t\torientation', joint.orientation


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

