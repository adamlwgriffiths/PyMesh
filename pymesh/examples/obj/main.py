import os

from pymesh.obj import OBJ

def load( filename ):
    print 'Loading', filename

    obj = OBJ()
    obj.load( filename )

    print "Mesh"
    print '\tnum vertices:', len(obj.model.vertices)
    print '\tnum normals:', len(obj.model.normals)
    print '\tnum texture_coords:', len(obj.model.texture_coords)
    print '\tnum materials:', len(obj.model.materials)
    print '\tnum meshes:', len(obj.model.meshes)
    print "Sub meshes"
    for mesh in obj.model.meshes:
        print '\tname:', mesh[ 'name' ]
        print '\tgroups:', mesh['groups']

    if obj.shadow:
        print "Shadow"
        for mesh in obj.shadow.meshes:
            print '\tName:', mesh[ 'name' ]
            print '\tGroups:', mesh['groups']

    if obj.trace:
        print "Trace"
        for mesh in obj.trace.meshes:
            print '\tName:', mesh[ 'name' ]
            print '\tGroups:', mesh['groups']

    print "Materials"
    for material in obj.materials:
        for key, layer in material.materials.items():
            print "\tmaterial key:", key
            print "\tname:", layer['name']
            print "\tambient:", layer['ambient']
            print "\tdiffuse:", layer['diffuse']
            print "\tspecular:", layer['specular']
            print "\thalo:", layer['alpha']
            print "\tshine:", layer['shine']
            print "\tillum:", layer['illum']
            print "\tsharpness:", layer['sharpness']
            print "\treflectivity:", layer['reflectivity']
            print "\tdensity:", layer['density']
            print "\tanti-alias:", layer['anti-alias']

            print "\ttexture"
            print "\t\tambient:", layer['textures']['ambient']
            print "\t\tdiffuse:", layer['textures']['diffuse']
            print "\t\tspecular:", layer['textures']['specular']
            print "\t\tshine:", layer['textures']['shine']
            print "\t\tbump:", layer['textures']['bump']
            print "\t\tdisplacement:", layer['textures']['displacement']
            print "\t\tdecal:", layer['textures']['decal']

        print "\ttextures"
        for texture in material.textures:
            print "\t\t", texture

    print "All Textures"
    for texture in obj.textures:
        print "\t", texture


def main():
    # load all .obj files in our data directory
    # get the path relative to our examples file
    path = os.path.join(
        os.path.dirname( __file__ ),
        '../data/obj'
        )
    # get the directory contents
    contents = os.listdir(path)

    # iterate through the contents and load
    # each file that is a .obj file
    for filename in contents:
        name, extension = os.path.splitext( filename )

        # reattach our current directory
        path = os.path.join(
            os.path.dirname( __file__ ),
            '../data/obj',
            filename
            )

        if extension.lower() == '.obj':
            load( path )

if __name__ == '__main__':
    main()

