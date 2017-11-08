#!/usr/bin/env python3
"""
plan_view.py
Copyright 2017 Steve Palmer
"""

import pyglet
import numpy as np

from utils import traced_methods, do_not_trace
from game_controller import GameView


@traced_methods
class RoomSprite(pyglet.sprite.Sprite):

    def __init__(self, planview, position: np.ndarray, room, *args, **kwargs):
        self.planview = planview
        self.room_position = position
        super().__init__(planview.room_image(room.walls), *args, **kwargs)
        self.view_update()
        room.attach(self)

    def view_update(self):
        self.planview.switch_to()
        self.scale = self.planview.sprite_scale
        self.set_position(*self.planview.position2xy(self.room_position))

    def walls_update(self, _, walls):
        self.planview.switch_to()
        self.image = self.planview.room_image(walls)


@traced_methods
class PlayerSprite(pyglet.sprite.Sprite):

    def __init__(self, planview, player, *args, **kwargs):
        self.planview = planview
        self.player = player
        super().__init__(planview.player_image(player.direction.right_angle_bearing()),
                         *args, **kwargs)
        self.view_update()

    def view_update(self):
        self.planview.switch_to()
        self.scale = self.planview.sprite_scale
        self.direction_update()
        self.position_update()

    def direction_update(self):
        self.planview.switch_to()
        self.image = self.planview.player_image(self.player.direction.right_angle_bearing())

    def position_update(self):
        self.planview.switch_to()
        self.set_position(*self.planview.position2xy(self.player.position))


@traced_methods
class PlanView(GameView):

    def __init__(self, game_controller, label: str=None):
        super().__init__(game_controller, label or "Plan View")

        # Maze Image Stuff
        room_atlas_img = pyglet.image.load('rooms_atlas.png')
        self._tile_size = room_atlas_img.height
        self._room_atlas = pyglet.image.ImageGrid(room_atlas_img, 1, 16, column_padding=2)
        assert self._room_atlas[0].width == self._tile_size

        # Player Image Stuff
        player_atlas_img = pyglet.image.load('player_atlas.png')
        assert self._tile_size == player_atlas_img.height
        assert player_atlas_img.width / self._tile_size == 4
        self._player_atlas = pyglet.image.ImageGrid(player_atlas_img, 1, 4)

        # Scaling stuff
        self.update_scaling()

        # Build the picture
        self.batch = pyglet.graphics.Batch()
        background = pyglet.graphics.OrderedGroup(0)
        self.rooms = []
        for position, room in game_controller.maze.items():
            self.rooms.append(RoomSprite(self, position, room, batch=self.batch, group=background))
        self.player_sprite = None

    def room_image(self, i: int):
        return self._room_atlas[i]

    def player_image(self, i: int):
        return self._player_atlas[i]

    def update_scaling(self):
        window_shape = np.array([self.width, self.height])
        maze_shape = self.game_controller.maze.shape
        self.sprite_scale = max(int((window_shape / maze_shape).min() / self._tile_size), 1)
        self.scale = self.sprite_scale * self._tile_size
        self.offset = (window_shape - maze_shape * self.scale) // 2

    def position2xy(self, position: np.ndarray):
        return tuple((position * self.scale) + self.offset)

    def add_player(self, player):
        super().add_player(player)
        self.switch_to()
        assert self.player_sprite is None
        foreground = pyglet.graphics.OrderedGroup(1)
        self.player_sprite = PlayerSprite(self, player, batch=self.batch, group=foreground)

    def entry(self):
        super().entry()
        self.display_update()

    def on_direction_update(self):
        assert self.player_sprite is not None
        self.player_sprite.direction_update()

    def on_position_update(self):
        assert self.player_sprite is not None
        self.player_sprite.position_update()

    def display_update(self):
        if self.player_sprite is not None:
            self.player_sprite.view_update()

    @do_not_trace
    def on_draw(self):
        if self.active:
            self.switch_to()
            self.clear()
            self.batch.draw()

    def on_resize(self, width: int, height: int):
        if self.active:
            self.switch_to()
            super().on_resize(width, height)
            self.update_scaling()
            for room in self.rooms:
                room.view_update()
            if self.player_sprite is not None:
                self.player_sprite.view_update()


__all__ = ('PlanView')
