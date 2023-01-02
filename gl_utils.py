#!/usr/bin/env python3
"""
gl_utils.py
Copyright 2023 Steve Palmer
"""

import ctypes
import pathlib

import numpy as np
import pyrr
import pyglet
import pyglet.gl as gl

from utils import traced_methods, traced


class GLObjectException(Exception):
    pass


@traced_methods
class GLObject:
    def __init__(self, gl_id):
        self._gl_id = gl_id

    @property
    def gl_id(self):
        return self._gl_id

    def __repr__(self):
        return "GLObject({})".format(self._gl_id)


@traced_methods
class GLShader(GLObject):

    shader_type_name = {
        gl.GL_VERTEX_SHADER: "Vertex Shader",
        gl.GL_GEOMETRY_SHADER: "Geometry Shader",
        gl.GL_FRAGMENT_SHADER: "Fragment Shader",
    }

    def __init__(self, shader_type, source):
        if shader_type not in GLShader.shader_type_name:
            raise ValueError
        self._shader_type = shader_type
        self._source = source
        super().__init__(gl.glCreateShader(shader_type))
        if isinstance(source, str):
            source = source.encode()
        if not isinstance(source, bytes):
            raise TypeError
        c_source = ctypes.create_string_buffer(source)
        c_source = ctypes.cast(
            ctypes.pointer(ctypes.pointer(c_source)),
            ctypes.POINTER(ctypes.POINTER(gl.GLchar)),
        )
        gl.glShaderSource(self.gl_id, 1, c_source, None)
        gl.glCompileShader(self.gl_id)
        rc = gl.GLint(0)
        gl.glGetShaderiv(self.gl_id, gl.GL_COMPILE_STATUS, ctypes.byref(rc))
        if not rc:
            gl.glGetShaderiv(self.gl_id, gl.GL_INFO_LOG_LENGTH, ctypes.byref(rc))
            buffer = ctypes.create_string_buffer(rc.value)
            gl.glGetShaderInfoLog(self.gl_id, rc, None, buffer)
            raise GLObjectException(
                "{}\n{}".format(
                    GLShader.shader_type_name[shader_type], buffer.value.decode()
                )
            )

    def __repr__(self):
        return "GLShader({}, {})".format(
            GLShader.shader_type_name[self._shader_type], repr(self._source)
        )

    def __del__(self):
        gl.glDeleteShader(self.gl_id)

    @classmethod
    def from_file(cls, shader_type, file_):
        result = None
        if isinstance(file_, pathlib.Path):
            with file_.open() as f:
                result = cls(shader_type, f.read())
        elif isinstance(file_, str):
            with open(file_) as f:
                result = cls(shader_type, f.read())
        else:
            result = cls(shader_type, file_.read())
        return result


@traced_methods
class GLProgram(GLObject):
    def __init__(self, shaders=None, *, do_link=None, do_use=None):
        if shaders is None:
            shaders = []
        if do_link is None:
            do_link = True
        if do_use is None:
            do_use = False
        super().__init__(gl.glCreateProgram())
        self._shaders_empty = True
        self._done_link = False
        for shader in shaders:
            self.add(shader)
        if not self._shaders_empty and do_link:
            self.link()
            if self._done_link and do_use:
                self.use()

    def __repr__(self):
        params = []
        if self._shaders:
            params.append(
                "[{}]".format(", ".join([repr(shader) for shader in self.shaders]))
            )
        if not self._done_link:
            params.append("do_link=False")
        return "GLProgram({})".format(", ".join(params))

    def add(self, shader: GLShader):
        if shader is not None:
            if not isinstance(shader, GLShader):
                raise TypeError
            gl.glAttachShader(self.gl_id, shader.gl_id)
            self._shaders_empty = False
            self._done_link = False

    def link(self):
        if self._shaders_empty:
            raise RuntimeError("No shaders attached to program")
        gl.glLinkProgram(self.gl_id)
        rc = gl.GLint(0)
        gl.glGetProgramiv(self.gl_id, gl.GL_LINK_STATUS, ctypes.byref(rc))
        if not rc:
            gl.glGetProgramiv(self.gl_id, gl.GL_INFO_LOG_LENGTH, ctypes.byref(rc))
            buffer = ctypes.create_string_buffer(rc.value)
            gl.glGetProgramInfoLog(self.gl_id, rc, None, buffer)
            raise GLObjectException(buffer.value.decode())
        else:
            self._done_link = True

    def use(self):
        if not self._done_link:
            self.link()
        gl.glUseProgram(self.gl_id)


@traced_methods
class GLShape:
    def __init__(
        self, vertices: np.ndarray, indices: np.ndarray, mode=None, texture=None
    ):
        if mode is None:
            mode = gl.GL_TRIANGLES
        self.vertices = vertices
        self.indices = indices
        self.indices_size = indices.size
        self.mode = mode
        self.texture = texture

        self.vao = gl.GLuint(0)
        gl.glGenVertexArrays(1, ctypes.byref(self.vao))
        gl.glBindVertexArray(self.vao)

        self.vbo = gl.GLuint(0)
        gl.glGenBuffers(1, ctypes.byref(self.vbo))
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,  # target
            vertices.nbytes,  # size
            (gl.GLbyte * vertices.nbytes)(*vertices.tobytes()),  # data
            gl.GL_STATIC_DRAW,
        )  # usage

        self.ebo = gl.GLuint(0)
        gl.glGenBuffers(1, ctypes.byref(self.ebo))
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER,
            indices.nbytes,
            (gl.GLbyte * indices.nbytes)(*indices.tobytes()),
            gl.GL_STATIC_DRAW,
        )

        for ind, fld in enumerate(
            sorted([f for f in vertices.dtype.fields.items()], key=lambda i: i[1][1])
        ):
            gl.glVertexAttribPointer(
                ind,  # index
                vertices[0][fld[0]].size,  # size
                gl.GL_FLOAT,  # type
                gl.GL_FALSE,  # normalized
                vertices.itemsize,  # stride
                ctypes.c_void_p(fld[1][1]),
            )  # pointer
            gl.glEnableVertexAttribArray(ind)

        if texture is not None:
            texture_image = pyglet.image.load(texture)
            self.texture = texture_image.get_texture()

        gl.glBindVertexArray(0)

    def __repr__(self):
        return "GLShape({}, {}, {})".format(self.vertices, self.indices, self.mode)

    def draw(self):
        gl.glBindVertexArray(self.vao)
        if self.texture is not None:
            gl.glEnable(self.texture.target)
            gl.glBindTexture(self.texture.target, self.texture.id)
        gl.glDrawElements(
            self.mode, self.indices_size, gl.GL_UNSIGNED_INT, 0  # mode  # count  # type
        )  # indices
        gl.glBindVertexArray(0)
        if self.texture is not None:
            gl.glBindTexture(self.texture.target, 0)

    def apply_vertex_transform(self, transform):
        return np.array(
            [
                np.dot(transform, pyrr.vector4.create_from_vector3(vertex, 1.0))
                for vertex in self.vertices["position"]
            ]
        )


@traced
def look_at(
    camera: np.ndarray,
    *,
    direction: np.ndarray = None,
    target: np.ndarray = None,
    up: np.ndarray = None
):
    if up is None:
        up = pyrr.vector3.create_unit_length_y(dtype=camera.dtype)
    if direction is None:
        if target is None:
            target = pyrr.vector3.create(dtype=camera.dtype)
        direction = pyrr.vector.normalise(camera - target)
    else:
        direction = pyrr.vector.normalise(direction)
    right = pyrr.vector.normalise(pyrr.vector3.cross(up, direction))
    up = pyrr.vector3.cross(direction, right)
    look_at_1 = pyrr.matrix44.create_identity(dtype=camera.dtype)
    look_at_1[0, 0:3] = right
    look_at_1[1, 0:3] = up
    look_at_1[2, 0:3] = direction
    look_at_2 = pyrr.matrix44.create_identity(dtype=camera.dtype)
    look_at_2[0:3, 3] = -camera
    return np.dot(look_at_1, look_at_2)


__all__ = (
    "GLObjectException",
    "GLObject",
    "GLShader",
    "GLProgram",
    "GLShape",
    "look_at",
)
