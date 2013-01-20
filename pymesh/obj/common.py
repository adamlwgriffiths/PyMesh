import re


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
