PyMesh
======

PyMesh provides functions to process a number of mesh formats and return data in a format that is simple to read and
process.

__PyMesh helps you get up and running quickly.__

Using a single data structure to represent all loaded mesh formats is not just a headache for us, but one for you.

Many times I've found myself wanting to load a simple mesh, and finding the data caught up in a scene graph with lights, camera and complex materials which are all irrelevant.

This also means that as new mesh formats and features are added, existing code will not be affected.


__PyMesh is a good foundation for a 3D library.__

PyMesh processes mesh formats and exposes them in a format that is easy for you to process.
Because PyMesh doesn't do any 3D graphics, it is platform and library independent.


Features
--------

   * MD2 (.md2).
   * MD5 (.md5mesh, .md5anim).
   * Wavefront OBJ (.obj).

Dependencies
------------

PyMesh requires the following software:

   * Python 2
   * Numpy

Source Installation
-------------------

Install PyMesh
```
git clone git@github.com:adamlwgriffiths/PyMesh.git
```

Install dependencies
```
pip install requirements.txt
```

Development
-----------------------

<img src="http://twistedpairdevelopment.files.wordpress.com/2010/10/twisted_pair-0086.png">

PyMesh is developed by [Twisted Pair Development](http://twistedpairdevelopment.wordpress.com).

Contributions are welcome.


License
---------------

PyMesh is released under the BSD 2-clause license (a very relaxed licence), but it is encouraged that any modifications are submitted back to the master for inclusion.

Created by Adam Griffiths.

Copyright (c) 2012, Twisted Pair Development.
All rights reserved.

twistedpairdevelopment.wordpress.com
@twistedpairdev

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies, 
either expressed or implied, of the FreeBSD Project.
