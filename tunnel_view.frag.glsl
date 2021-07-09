#version 300 es

#ifdef GL_ES
precision highp float;
#endif

in vec2 v_texture;
out vec4 FragColor;
uniform sampler2D sampTexture;
void main()
{
	FragColor = texture(sampTexture, v_texture);
}
