import glfw
import OpenGL.GL as gl
import time

# Shadertoy like.
# https://www.shadertoy.com/
render = """
#define MAX_DIST 100.0
#define MAX_STEPS 256
#define MB_ITER 24
#define pi 3.1415926

#define Power 8.0

float zoomFunc(float x, float speed) {
    return -0.9*pow(2.7181,-speed*x)-1.054975;
}

mat2 Rot(float b)
{
    float a = b*pi/180.;
    float s = sin(a);
    float c = cos(a);
    return mat2(c,-s,s,c);
}

float SDF(vec3 pos, out int steps) {
pos.xz*= Rot(-90.0);
 pos.yz*=Rot(90.0);
	vec3 z = pos;
	float dr = 1.0;
	float r = 0.0;
	for (int i = 0; i < MB_ITER ; i++) {
		r = length(z);
        steps = i;
		if (r>1.5) break;
		
		// convert to polar coordinates
		float theta = acos(z.z/r);
		float phi = atan(z.y,z.x);
		dr =  pow( r, Power-1.0)*Power*dr + 1.0;
		
		// scale and rotate the point
		float zr = pow( r,Power);
		theta = theta*Power;
		phi = phi*Power;
		
		// convert back to cartesian coordinates
		z = zr*vec3(sin(theta)*cos(phi), sin(phi)*sin(theta), cos(theta));
		z+=pos;
	}

	return 0.5*log(r)*r/dr;
}

float trace(vec3 ro, vec3 rd, out int steps) {
  float depth = 0.0;
  int zz;
  float EPSILON = SDF(ro,zz)/2048.0;

  for (int i = 0; i < MAX_STEPS; ++i) {
    float dist = SDF(ro + depth * rd, steps);

    if (dist < EPSILON) return depth;

    depth += dist;

    if (depth > MAX_DIST) return MAX_DIST;
  }

  return MAX_DIST;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
  float mf = uMovement.w;
  
  vec2 xy = (fragCoord - iResolution.xy / 2.0)/iResolution.y;
  vec3 ro = vec3(-0.02 + uMovement.x*mf, 0.156 + uMovement.y*mf, 1.6 - uMovement.z*mf);
  vec3 rd = (vec3(xy, -1));
  int steps = 0;


  float dist = trace(ro, rd, steps);

  if (dist < MAX_DIST) {
    fragColor = vec4(vec3(clamp((MB_ITER - float(steps)) / MB_ITER, 0.0, 1.0)), 1.0);

    return;
  }

  fragColor = vec4(vec3(0.0), 1.0);
}
"""

# ============================================================================================== #

# Vertex shader: creates a full-screen triangle using gl_VertexID.
vertex_shader_source = """
#version 330 core
void main() {
    vec2 pos[3] = vec2[3](
        vec2(-1.0, -1.0),
        vec2( 3.0, -1.0),
        vec2(-1.0,  3.0)
    );
    gl_Position = vec4(pos[gl_VertexID], 0.0, 1.0);
}
"""

# Fragment shader with iResolution and iTime uniforms.
fragment_shader_source = """
#version 330 core
uniform vec3 iResolution; // viewport resolution (in pixels)
uniform float iTime;      // shader playback time (in seconds)
uniform vec4 uMovement;
out vec4 FragColor;

""" + render + """

void main() {
    mainImage(FragColor, gl_FragCoord.xy);
}
"""

# Global variable for tracking movement
movement = [0.0, 0.0, 0.0, 1/16]  # x, y, z directions | w is for the zoom step size

# W: move up
# S: move down
# A: move left
# D: move right
# Q: zoom in
# SPACE: zoom out
# UP KEY: increase zoom step size by half
# DOWN KEY: decrease zoom step size by a factor of two
def key_callback(window, key, scancode, action, mods):
    global movement
    if action == glfw.PRESS or action == glfw.REPEAT:
        if key == glfw.KEY_W:
            movement[1] += 1.0
        elif key == glfw.KEY_S:
            movement[1] -= 1.0
        elif key == glfw.KEY_A:
            movement[0] -= 1.0
        elif key == glfw.KEY_D:
            movement[0] += 1.0
        elif key == glfw.KEY_SPACE:
            movement[2] -= 1.0
        elif key == glfw.KEY_Q:
            movement[2] += 1.0
        elif key == glfw.KEY_UP:
            movement[3] *= 2
            movement[0] /=2
            movement[1] /=2 
            movement[2] /=2
        elif key == glfw.KEY_DOWN:
            movement[3] /= 2
            movement[0] *=2
            movement[1] *=2 
            movement[2] *=2
                    
def compile_shader(source, shader_type):
    shader = gl.glCreateShader(shader_type)
    gl.glShaderSource(shader, source)
    gl.glCompileShader(shader)
    
    # Check for compilation errors
    success = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
    if not success:
        info_log = gl.glGetShaderInfoLog(shader).decode()
        shader_type_name = "VERTEX" if shader_type == gl.GL_VERTEX_SHADER else "FRAGMENT"
        print(f"ERROR::{shader_type_name}_SHADER_COMPILATION_ERROR\n{info_log}")
        return None
    return shader

def create_shader_program(vertex_src, fragment_src):
    vertex_shader = compile_shader(vertex_src, gl.GL_VERTEX_SHADER)
    fragment_shader = compile_shader(fragment_src, gl.GL_FRAGMENT_SHADER)
    if vertex_shader is None or fragment_shader is None:
        return None

    program = gl.glCreateProgram()
    gl.glAttachShader(program, vertex_shader)
    gl.glAttachShader(program, fragment_shader)
    gl.glLinkProgram(program)
    
    # Check for linking errors
    success = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)
    if not success:
        info_log = gl.glGetProgramInfoLog(program).decode()
        print(f"ERROR::PROGRAM_LINKING_ERROR\n{info_log}")
        return None

    # Shaders can be deleted after linking
    gl.glDeleteShader(vertex_shader)
    gl.glDeleteShader(fragment_shader)
    return program

def main():
    # Initialize GLFW
    if not glfw.init():
        print("Failed to initialize GLFW")
        return

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(800, 600, "GLSL in Python", None, None)
    if not window:
        glfw.terminate()
        print("Failed to create GLFW window")
        return

    glfw.make_context_current(window)
    
    # Create shader program
    shader_program = create_shader_program(vertex_shader_source, fragment_shader_source)
    if shader_program is None:
        glfw.terminate()
        return
    
    # Set keyboard callback
    glfw.set_key_callback(window, key_callback)
    uMovement_location = gl.glGetUniformLocation(shader_program, "uMovement")

    # Get uniform locations
    iResolution_location = gl.glGetUniformLocation(shader_program, "iResolution")
    iTime_location = gl.glGetUniformLocation(shader_program, "iTime")

    start_time = time.time()

    # Render loop
    while not glfw.window_should_close(window):
        # Get framebuffer size (in case of window resizing)
        width, height = glfw.get_framebuffer_size(window)
        gl.glViewport(0, 0, width, height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(shader_program)
        
        # Update uniforms
        
        gl.glUniform4f(uMovement_location, movement[0], movement[1], movement[2], movement[3]) 
        gl.glUniform3f(iResolution_location, float(width), float(height), 1.0)
        
        current_time = time.time()
        gl.glUniform1f(iTime_location, current_time - start_time)

        # Draw the full-screen triangle (no VAO/VBO required)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()
