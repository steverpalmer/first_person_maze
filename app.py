#!/usr/bin/env python3
"""
app.py
Copyright 2017 Steve Palmer
"""

import logging.config

import pyglet
import numpy as np

from utils import traced_methods
from maze import Maze
from player import Player
from game_controller import GameController
from plan_view import PlanView
from tunnel_view import TunnelView
from tunnel_view_2 import TunnelView2


@traced_methods
class Main:
    def __init__(self, size_x:int=None, size_y:int=None):
        if size_x is None:
            size_x = 10
        if size_y is None:
            size_y = size_x * 8 // 10
        self.maze = Maze(np.array([size_x, size_y]))
        self.build = self.maze.build()
        self.game_controller = GameController(maze=self.maze, caption="Maze 3D")
        start_view = self.game_controller.add_view(PlanView)
        self.game_controller.add_view(TunnelView)
        self.game_controller.add_view(TunnelView2)
        self.game_controller.current_view_index = start_view

    def update(self, dt):
        try:
            next(self.build)
        except StopIteration:
            pyglet.clock.unschedule(self.update)
            self.player = Player(self.maze)
            self.game_controller.add_player(self.player)

    def go(self):
        pyglet.clock.schedule_interval(self.update, 0.02)
        pyglet.app.run()


if __name__ == '__main__':
    from pathlib import Path
    logging_config = Path('logging.conf')
    if logging_config.exists():
        logging.config.fileConfig(logging_config.open())
    Main().go()
