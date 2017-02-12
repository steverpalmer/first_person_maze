#!/usr/bin/env python3
"""
player.py
Copyright 2017 Steve Palmer
"""

import pyglet

from utils import traced_methods
from maze import Maze


@traced_methods
class Player(pyglet.event.EventDispatcher):
    """
    Trivial model of a player.

    A Player has a position and direction within the maze.
    The Player model receives events from the GameController,
    specifically on_left_turn, on_right_turn, on_forwards_step and
    on_backwards_step.  It implements the business logic to determine
    whether such events are allowed.

    The player in turn may generate other events, specifically
    on_direction_update, on_position_update and on_maze_exit.
    """
    def __init__(self, maze:Maze):
        super().__init__()
        self.maze = maze
        self._position, self._direction = maze.random_pose()
        self.step_count = 0

    @property
    def direction(self):
        return self._direction

    @property
    def position(self):
        return self._position

    def on_left_turn(self):
        self._direction = self._direction.turn_left()
        self.dispatch_event('on_direction_update')

    def on_right_turn(self):
        self._direction = self._direction.turn_right()
        self.dispatch_event('on_direction_update')

    def on_forwards_step(self):
        self.step_count += 1
        if self.maze.can_move(self._position, self._direction):
            self._position += self._direction.offset()
            self.dispatch_event('on_position_update')
            if self._position not in self.maze:
                self.dispatch_event('on_maze_exit')

    def on_backwards_step(self):
        self.step_count += 1
        if self.maze.can_move(self._position, self._direction.reverse()):
            self._position -= self.direction.offset()
            self.dispatch_event('on_position_update')
            if self._position not in self.maze:
                self.dispatch_event('on_maze_exit')


Player.register_event_type('on_direction_update')
Player.register_event_type('on_position_update')
Player.register_event_type('on_maze_exit')

__all__ = ('Player')
