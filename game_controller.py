#!/usr/bin/env python3
"""
game_controller.py
Copyright 2017 Steve Palmer

The Game Control is split into two parts:
 * The GameController
 * Views inheriting from GameView

The GameController is mostly about shared state,
while the GameViews carry most of the behaviour.
"""

import pyglet

from utils import traced_methods, modlog
from player import Player


@traced_methods
class GameView(pyglet.window.Window):
    """
    GameView have:
     * independent GL Context and Object spaces.
     * Methods to pass on events such as on_key_press and on_close to the game_controller
     * an entry method that makes the view visible
     * entry and exit methods with attach and detach the view from the model

    Note that the only the visible view gets updates as the model changes.
    """

    def __init__(self, game_controller, label:str):
        old_caption = game_controller.window_args.get('caption', None)
        if old_caption is None:
            game_controller.window_args['caption'] = label
        else:
            game_controller.window_args['caption'] = old_caption + " - " + label
        display = pyglet.canvas.get_display()
        canvas = pyglet.canvas.Canvas(display, None)
        template = pyglet.gl.Config(double_buffer=True, depth_size=24)
        config = template.match(canvas)[0]
        context = config.create_context(None)
        super().__init__(context=context, **game_controller.window_args)
        game_controller.window_args['caption'] = old_caption

        self.game_controller = game_controller
        self.player = None
        self.active = False

    def add_player(self, player:Player):
        assert player is not None
        self.player = player
        if self.active:
            player.push_handlers(self)
            self.push_handlers(player)

    def entry(self):
        self.active = True
        self.set_visible(True)
        if self.player is not None:
            self.player.push_handlers(self)
            self.push_handlers(self.player)

    def exit(self):
        if self.player is not None:
            self.player.remove_handlers(self)
            self.remove_handlers(self.player)
        self.set_visible(False)
        self.active = False

    def on_key_press(self, key, modifiers):
        try:
            modlog(__name__).debug("=============================================")
            self.dispatch_event(self.game_controller.controls[key])
        except KeyError:
            pass

    def on_next_view(self):
        if self.player is not None:
            self.game_controller.next_view()

    def on_close(self):
        self.game_controller.close()

    def on_maze_exit(self):
        self.game_controller.close()

GameView.register_event_type('on_left_turn')
GameView.register_event_type('on_right_turn')
GameView.register_event_type('on_forwards_step')
GameView.register_event_type('on_backwards_step')
GameView.register_event_type('on_next_view')


@traced_methods
class GameController:

    def __init__(self, **kwargs):
        super().__init__()
        self.maze = kwargs['maze']
        del kwargs['maze']
        self.window_args = kwargs
        self.window_args['visible'] = False
        self.window_args['resizable'] = True
        self.available_views = []
        self._current_view_index = None
        self.player = None

        self.controls = { pyglet.window.key.LEFT : 'on_left_turn'
                        , pyglet.window.key.RIGHT : 'on_right_turn'
                        , pyglet.window.key.UP : 'on_forwards_step'
                        , pyglet.window.key.DOWN : 'on_backwards_step'
                        , pyglet.window.key.SPACE : 'on_next_view'
                        }


    def add_view(self, cls, *args, **kwargs):
        """
        Add the view to the list of available views.
        Return the index for this new view.
        """
        assert issubclass(cls, GameView)
        new_view = cls(self, *args, **kwargs)
        result = len(self.available_views)
        self.available_views.append(new_view)
        return result

    def add_player(self, player:Player):
        """
        Add a player to the game.
        """
        assert player is not None
        assert self.player is None
        for view in self.available_views:
            view.add_player(player)

    @property
    def current_view_index(self):
        return self._current_view_index

    @current_view_index.setter
    def current_view_index(self, index_:int):
        if self._current_view_index is not None:
            self.available_views[self._current_view_index].exit()
        self._current_view_index = index_
        if index_ is not None:
            self.available_views[index_].entry()

    def next_view(self):
        if self._current_view_index is not None and len(self.available_views) > 1:
            self.current_view_index = (self._current_view_index + 1) % len(self.available_views)

    def close(self):
        self.current_view_index = None
        pyglet.app.exit()


__all__ = ('GameView', 'GameController')
