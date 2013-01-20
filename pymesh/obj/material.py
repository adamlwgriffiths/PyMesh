from common import OBJ_Loader


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