#!/usr/bin/env python3
"""
tunnel_view_2.py
Copyright 2023 Steve Palmer
"""

import pyglet
import pyglet.gl as gl
import numpy as np
import pyrr

from utils import traced_methods, do_not_trace
from direction import Direction
from game_controller import GameView

from gl_utils import GLProgram, GLShader, GLShape, look_at


@traced_methods
class TunnelView2(GameView):
    def __init__(self, game_controller, label: str = None):
        super().__init__(game_controller, label or "Tunnel View 2")

        gl.glClearColor(0.4, 0.65, 0.8, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)

        self.ground_level = 0.0
        self.wall_level = 0.75
        gravel_scale = 3.0
        maze = game_controller.maze
        self.ground = GLShape(
            np.array(
                [
                    ((-1, self.ground_level, 1), (0.0, 0.0)),  # 0
                    (
                        (-1, self.ground_level, -maze.shape[1] - 1),
                        (0.0, gravel_scale * (maze.shape[1] + 2)),
                    ),  # 1
                    (
                        (maze.shape[0] + 1, self.ground_level, -maze.shape[1] - 1),
                        (
                            gravel_scale * (maze.shape[0] + 2),
                            gravel_scale * (maze.shape[1] + 2),
                        ),
                    ),  # 2
                    (
                        (maze.shape[0] + 1, self.ground_level, 0.0),
                        (gravel_scale * (maze.shape[0] + 2), 0.0),
                    ),
                ],  # 3
                dtype=[("position", np.float32, 3), ("texture", np.float32, 2)],
            ),
            np.array([0, 1, 2, 3], dtype=np.uint32),
            gl.GL_QUADS,
            "gravel.jpg",
        )
        self.walls = None
        self.egress = None

        self.program = GLProgram(
            (
                GLShader.from_file(*args)
                for args in (
                    (gl.GL_VERTEX_SHADER, "tunnel_view.vert.glsl"),
                    (gl.GL_FRAGMENT_SHADER, "tunnel_view.frag.glsl"),
                )
            ),
            do_use=True,
        )

        # Uniform
        self.transform_loc = gl.glGetUniformLocation(self.program.gl_id, b"transform")

        self.cummulative_time = 0.0

    def entry(self):
        super().entry()
        self.target_camera = TunnelView2.player_camera(self.player)
        self.target_time = self.cummulative_time
        self.display_update()
        pyglet.clock.schedule_interval(self.scheduled_update, 0.01)

    def exit(self):
        pyglet.clock.unschedule(self.scheduled_update)
        super().exit()

    @staticmethod
    def player_camera(player):
        return np.array(
            [
                player.position[0],
                player.position[1],
                player.direction.right_angle_bearing() * np.pi / 2.0,
            ],
            dtype=np.float32,
        )

    def add_player(self, player):
        super().add_player(player)
        self.target_camera = TunnelView2.player_camera(player)
        self.target_time = self.cummulative_time

    def build_walls(self):
        wall_plan = self.game_controller.maze.wall_2d_vertices(0.075)
        wall_plan_len = wall_plan.shape[0]
        wall_vertices = np.recarray(
            (wall_plan_len * 2,),
            dtype=[("position", np.float32, 3), ("texture", np.float32, 2)],
        )
        wall_vertices["position"][::2, 0] = wall_plan[:, 0]
        wall_vertices["position"][1::2, 0] = wall_plan[:, 0]
        wall_vertices["position"][::2, 2] = -wall_plan[:, 1]
        wall_vertices["position"][1::2, 2] = -wall_plan[:, 1]
        wall_vertices["position"][::2, 1] = self.ground_level
        wall_vertices["position"][1::2, 1] = self.wall_level
        wall_vertices["texture"][0, 0] = 0.0
        wall_vertices["texture"][1, 0] = 0.0
        wall_vertices["texture"][::2, 1] = 0.0
        wall_vertices["texture"][1::2, 1] = 1.0
        distance = np.fabs(wall_plan[1:, 0] - wall_plan[:-1, 0]) + np.fabs(
            wall_plan[1:, 1] - wall_plan[:-1, 1]
        )
        distance = np.cumsum(distance)
        wall_vertices["texture"][2::2, 0] = distance
        wall_vertices["texture"][3::2, 0] = distance
        wall_panels = wall_plan_len - 1
        wall_indices = np.empty((wall_panels * 4), dtype=np.uint32)
        wall_indices[::4] = np.arange(0, wall_panels * 2, 2)
        wall_indices[1::4] = wall_indices[::4] + 1
        wall_indices[2::4] = wall_indices[::4] + 3
        wall_indices[3::4] = wall_indices[::4] + 2
        self.walls = GLShape(wall_vertices, wall_indices, gl.GL_QUADS, "hedge.jpg")

        exit_vertices = np.recarray(
            (4,), dtype=[("position", np.float32, 3), ("texture", np.float32, 2)]
        )
        exit_vertices["position"][:2] = wall_vertices["position"][:2]
        exit_vertices["position"][2:] = wall_vertices["position"][-2:]
        exit_vertices["texture"][0, 0] = 1.0
        exit_vertices["texture"][0, 1] = 0.0
        exit_vertices["texture"][1, 0] = 1.0
        exit_vertices["texture"][1, 1] = 1.0
        exit_vertices["texture"][2, 0] = 0.0
        exit_vertices["texture"][2, 1] = 0.0
        exit_vertices["texture"][3, 0] = 0.0
        exit_vertices["texture"][3, 1] = 1.0
        exit_indices = np.empty((4,), dtype=np.uint32)
        exit_indices[0] = 0
        exit_indices[1] = 1
        exit_indices[2] = 3
        exit_indices[3] = 2
        self.egress = GLShape(exit_vertices, exit_indices, gl.GL_QUADS, "exit2.jpg")

    _target_offset = {
        Direction.North: -pyrr.vector3.create_unit_length_z(dtype=np.float32),
        Direction.East: pyrr.vector3.create_unit_length_x(dtype=np.float32),
        Direction.South: pyrr.vector3.create_unit_length_z(dtype=np.float32),
        Direction.West: -pyrr.vector3.create_unit_length_x(dtype=np.float32),
    }

    def display_update(self):
        assert self.player is not None
        self.switch_to()

        if self.walls is None:
            self.build_walls()

        # view
        if self.cummulative_time >= self.target_time:
            pc = self.target_camera
        else:
            pc = self.target_camera - self.delta_camera * (
                max(self.target_time - self.cummulative_time, 0.0) / self.delta_time
            )

        camera = pyrr.vector3.create(
            pc[0] + 0.5,
            (self.ground_level + self.wall_level) / 2.0,
            -pc[1] - 0.5,
            dtype=np.float32,
        )
        direction = pyrr.vector3.create(-np.sin(pc[2]), 0.0, np.cos(pc[2]))
        view = look_at(camera, direction=direction)
        transform = view

        # then project
        projection = pyrr.matrix44.create_perspective_projection_matrix(
            90.0, self.width / self.height, 0.1, 1000.0, dtype=np.float32
        ).T
        transform = np.dot(projection, transform)

        gl.glUniformMatrix4fv(
            self.transform_loc,  # location
            1,  # count
            gl.GL_TRUE,  # Numpy uses Row-Dominant, OpenGL used Column-Dominant
            (gl.GLfloat * transform.size)(*transform.flatten()),
        )  # value

    def on_resize(self, width: int, height: int):
        self.switch_to()
        gl.glViewport(0, 0, width, height)
        if self.player is not None:
            self.display_update()

    def _calculate_delta(self, duration: float = 0.2):
        if self.cummulative_time >= self.target_time:
            previous_camera = self.target_camera
        else:
            previous_camera = self.target_camera - (
                self.delta_camera
                * (max(self.target_time - self.cummulative_time, 0.0) / self.delta_time)
            )
        self.target_camera = TunnelView2.player_camera(self.player)
        self.delta_time = duration
        self.target_time = self.cummulative_time + self.delta_time
        self.delta_camera = self.target_camera - previous_camera
        theta = self.delta_camera[2]
        if theta > np.pi:
            self.delta_camera[2] -= 2.0 * np.pi
        elif theta < -np.pi:
            self.delta_camera[2] += 2.0 * np.pi

    def on_direction_update(self):
        assert self.player is not None
        self._calculate_delta()
        self.display_update()

    def on_position_update(self):
        assert self.player is not None
        self._calculate_delta()
        self.display_update()

    @do_not_trace
    def on_draw(self):
        if self.active and self.player is not None:
            self.switch_to()
            self.clear()
            self.ground.draw()
            if self.walls is not None:
                self.walls.draw()
            if self.egress is not None:
                self.egress.draw()

    @do_not_trace
    def scheduled_update(self, dt):
        self.cummulative_time += dt
        self.display_update()


if __name__ == "__main__":
    pass
