Maze 3D
=======

5 February 2017

Navigate a generated (2D) maze using a First-Person 3D view from
inside the maze.

Dependencies
------------

* python3
* pyglet
* pyrr

Game Play
---------

Start game with `python3 app.py`

A new maze is generated and displayed in Plan View. Press <Space> to
toggle between available views.  Use the arrow keys to move forwards,
backwards, turn left and turn right.

Implementation Notes
--------------------

The implementation uses a MVC paradigm with a single controller a 3
distinct views:

The first view is the Plan View giving a 2D (top-down) representation
of the maze and player position.  The image is generated using pyglet
Sprites.

The second view is the re-implementation of the 3D view that I first
implemented on my old Acorn Atom.  The image is black and white
line-art picture giving an approximation of what might be seen by the
player.  The player jumps from one position to the next and the image
does not attempt to show what could be seen in side passages, but
merely indicates that the side passage it there.  It is crude, but I
could implement it on a small Atom with the screen redraw taking about
0.5 seconds.  Here it is rather quicker based on pyglet vertex
buffers.

The third view is the extension of the 3D view trying to give a much
more realistic model.  The sky is blue, the ground is gravel, and
walls are hedges.  This view uses OpenGL shaders with the heavy
lifting being done on the GPU.
