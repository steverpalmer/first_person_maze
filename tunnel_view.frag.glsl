#version 330 core
in vec2 v_texture;
out vec4 gl_FragColor;
uniform sampler2D sampTexture;
void main()
{
	gl_FragColor = texture(sampTexture, v_texture);
}
