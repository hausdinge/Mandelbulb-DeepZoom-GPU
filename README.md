# Mandelbulb-DeepZoom-GPU

Simple Python script to explore the Mandelbulb in realtime.
The Mandelbulb should be rendered on a decent GPU.
To render the Mandelbulb in realtime the script uses
OpenGL and a **Fragment Shader** inspired by **Shadertoy:**

https://www.shadertoy.com/

For exploration we also added some features like to move around
using keyboard controls.

## Usage 

- `W`: Move Up
- `S`: Move Down
- `A`: Move Left
- `D`: Move Right
- `Q`: Zoom In
- `SPACE`: Zoom Out

While zooming into the Mandelbulb you have to decrease the zoom 
step size otherwise you will overshoot and end up inside. For this
use:

- `UP KEY`: Increase zoom step size by a factor of two
- `DOWN KEY`: Decrease zoom step size by a factor of two

## Limitations

At some point if you are zooming in deep enough everything
will get pixelated. This is because of the precision limitation
of floating point numbers. For this we also implemented the 
Mandelbulb on an FPGA to get more precision:

https://github.com/hausdinge/mb-fpga
