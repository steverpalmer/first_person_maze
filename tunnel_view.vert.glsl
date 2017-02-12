#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texture;
uniform mat4 transform;

out vec2 v_texture;

void main()
{
	gl_Position = transform * vec4(position, 1.0f);
	v_texture = texture;
}
