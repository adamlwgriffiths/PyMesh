import os

from pymesh.md2 import MD2

def load_mesh( filename ):
    print 'Loading Raw', filename
    md2 = MD2()
    md2.load( filename )

    print 'header'
    print '\tident', md2.header.ident
    print '\tversion', md2.header.version
    print '\tskin_width', md2.header.skin_width
    print '\tskin_height', md2.header.skin_height
    print '\tframe_size', md2.header.frame_size
    print '\tnum_skins', md2.header.num_skins
    print '\tnum_vertices', md2.header.num_vertices
    print '\tnum_st', md2.header.num_st
    print '\tnum_tris', md2.header.num_tris
    print '\tnum_glcmds', md2.header.num_glcmds
    print '\tnum_frames', md2.header.num_frames
    print '\toffset_skins', md2.header.offset_skins
    print '\toffset_st', md2.header.offset_st
    print '\toffset_tris', md2.header.offset_tris
    print '\toffset_frames', md2.header.offset_frames
    print '\toffset_glcmds', md2.header.offset_glcmds
    print '\toffset_end', md2.header.offset_end

    print 'skins'
    for skin in md2.skins:
        print '\t', skin

    print 'frames'
    for frame in md2.frames:
        print '\tname', frame.name
        print '\tvertices', frame.vertices
        print '\tnormals', frame.normals

    print 'triangles'
    print '\tvertex_indices', md2.triangles.vertex_indices
    print '\ttc_indices', md2.triangles.tc_indices

    print 'tcs'
    for tc in md2.tcs:
        print '\t', tc


def main():
    # load all files in our data directory
    # get the path relative to our examples file
    path = os.path.join(
        os.path.dirname( __file__ ),
        '../data/md2'
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
            '../data/md2',
            filename
            )

        if extension.lower() == '.md2':
            load_mesh( path )

if __name__ == '__main__':
    main()

