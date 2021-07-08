#!/usr/bin/env python3
"""
tunnel_view.py
Copyright 2017 Steve Palmer
"""

import pyglet
import numpy as np

from utils import traced_methods, do_not_trace
from game_controller import GameView


@traced_methods
class TunnelView(GameView):
    def __init__(self, game_controller, label: str = None):
        super().__init__(game_controller, label or "Tunnel View")
        self._step_max = game_controller.maze.shape.max()
        self.indices = []

    def on_resize(self, width: int, height: int):
        self.switch_to()
        super().on_resize(width, height)
        vertices = []
        limits = np.array([width // 2, height // 2])
        centre = limits
        next_offset = limits
        for distance in range(2, self._step_max + 4):
            offset = next_offset
            next_offset = limits // distance
            #  0. Left Bottom Outer
            vertices.extend((centre[0] - offset[0], centre[1] - offset[1]))
            #  1. Left Top Outer
            vertices.extend((centre[0] - offset[0], centre[1] + offset[1]))
            #  2. Right Bottom Outer
            vertices.extend((centre[0] + offset[0], centre[1] - offset[1]))
            #  3. Right Top Outer
            vertices.extend((centre[0] + offset[0], centre[1] + offset[1]))
            #  4. Left Bottom Inner
            vertices.extend((centre[0] - offset[0], centre[1] - next_offset[1]))
            #  5. Left Top Inner
            vertices.extend((centre[0] - offset[0], centre[1] + next_offset[1]))
            #  6. Right Bottom Inner
            vertices.extend((centre[0] + offset[0], centre[1] - next_offset[1]))
            #  5. Right Top Inner
            vertices.extend((centre[0] + offset[0], centre[1] + next_offset[1]))
        self.vertices_count = len(vertices) // 2
        self.vertices = ("v2i", vertices)
        self.vertices_colour = ("c4B", (255, 255, 255, 255) * self.vertices_count)

    def entry(self):
        super().entry()
        self.display_update()

    def display_update(self):
        assert self.player is not None
        self.switch_to()
        direction = self.player.direction
        left = direction.turn_left()
        right = direction.turn_right()
        position = self.player.position.copy()
        indices = []
        for step in range(1, self._step_max + 3):
            if not direction:  # Beyond the far wall
                pass
            elif position not in self.game_controller.maze:  # Maze Exit
                indices.extend(
                    ((step - 1) << 3 | 0, (step - 1) << 3 | 1)
                )  # previous left post
                indices.extend(
                    ((step - 1) << 3 | 2, (step - 1) << 3 | 3)
                )  # previous right post
                indices.extend((step << 3 | 0, step << 3 | 1))  # this left post
                indices.extend((step << 3 | 2, step << 3 | 3))  # this right post
                break
            else:
                room = self.game_controller.maze[position]
                if room.can_move(left):
                    indices.extend(
                        ((step - 1) << 3 | 4, step << 3 | 0)
                    )  # left bottom gap
                    indices.extend(((step - 1) << 3 | 5, step << 3 | 1))  # left top gap
                    left_post = True
                    if step > 0:
                        indices.extend(
                            ((step - 1) << 3 | 0, (step - 1) << 3 | 1)
                        )  # previous left post
                else:
                    indices.extend(
                        ((step - 1) << 3 | 0, step << 3 | 0)
                    )  # left bottom wall
                    indices.extend(
                        ((step - 1) << 3 | 1, step << 3 | 1)
                    )  # left top wall
                    left_post = False
                if room.can_move(right):
                    indices.extend(
                        ((step - 1) << 3 | 6, step << 3 | 2)
                    )  # right bottom gap
                    indices.extend(
                        ((step - 1) << 3 | 7, step << 3 | 3)
                    )  # right top gap
                    right_post = True
                    if step > 0:
                        indices.extend(
                            ((step - 1) << 3 | 2, (step - 1) << 3 | 3)
                        )  # previous right post
                else:
                    indices.extend(
                        ((step - 1) << 3 | 2, step << 3 | 2)
                    )  # right bottom wall
                    indices.extend(
                        ((step - 1) << 3 | 3, step << 3 | 3)
                    )  # right top wall
                    right_post = False
                if room.can_move(direction):
                    if left_post:
                        indices.extend((step << 3 | 0, step << 3 | 1))  # this left post
                    if right_post:
                        indices.extend(
                            (step << 3 | 2, step << 3 | 3)
                        )  # this right post
                    position += direction.offset()
                else:
                    if not left_post:
                        indices.extend((step << 3 | 0, step << 3 | 1))  # this left post
                    if not right_post:
                        indices.extend(
                            (step << 3 | 2, step << 3 | 3)
                        )  # this right post
                    indices.extend((step << 3 | 0, step << 3 | 2))  # end bottom wall
                    indices.extend((step << 3 | 1, step << 3 | 3))  # end top wall
                    break
        self.indices = indices

    def on_direction_update(self):
        self.display_update()

    def on_position_update(self):
        self.display_update()

    @do_not_trace
    def on_draw(self):
        if self.active and self.player is not None:
            self.switch_to()
            self.clear()
            pyglet.graphics.draw_indexed(
                self.vertices_count,
                pyglet.gl.GL_LINES,
                self.indices,
                self.vertices,
                self.vertices_colour,
            )


__all__ = "TunnelView"
