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
        print joint
        print joint.name, joint.parent, joint.position, joint.orientation

    print 'meshes'
    for mesh in md5.meshes:
        print 'shader', mesh.shader
        print 'numverts', mesh.num_verts
        #for index in range( mesh.num_verts ):
        #    vert = mesh.vertex( index )
        for vert in mesh.vertices:
            print 'tcs', vert.tcs
            print 'start_weight', vert.start_weight
            print 'weight_count', vert.weight_count

        print 'numtris', mesh.num_tris
        for tri in mesh.tris:
            print tri

        print 'numweights', mesh.num_weights
        #for index in range( mesh.num_weights ):
        #    weight = mesh.weight( index )
        for weight in mesh.weights:
            print 'joint', weight.joint
            print 'bias', weight.bias
            print 'position', weight.position


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

