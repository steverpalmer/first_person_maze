#!/usr/bin/env python3
"""
maze.py
Copyright 2017 Steve Palmer
"""

import itertools
import collections.abc
import random
import weakref

import numpy as np

from utils import traced_methods, do_not_trace, \
    checked_methods, constructor, query, procedure, invariant_checker

from direction import Direction


class RoomWallError(Exception): pass
class RoomEgressError(Exception): pass
class RoomError(Exception): pass


@checked_methods
@traced_methods
class Room:
    """
    A class that models a room within the maze.

    Rooms have walls, an exit direction (egress) and observers.
    """

    @constructor
    def __init__(self, walls: Direction=Direction.All, egress: Direction=Direction.Unknown):
        """
        >>> Room().walls == Direction.All
        True
        >>> Room().egress == Direction.Unknown
        True
        >>> Room(walls=0).walls
        0
        >>> Room(walls=0, egress=Direction.North).egress == Direction.North
        True
        >>> r = Room()
        >>> r.walls = r.walls & ~Direction.North
        >>> bool(r.walls & Direction.North)
        False
        >>> r = Room()
        >>> r._walls = 2.3
        >>> r._check()
        Traceback (most recent call last):
            ...
        TypeError
        >>> r = Room()
        >>> r._walls = -1
        >>> r._check()
        Traceback (most recent call last):
            ...
        RoomWallError
        >>> r = Room()
        >>> r._egress = 1
        >>> r._check()
        Traceback (most recent call last):
            ...
        TypeError
        >>> r = Room()
        >>> r._egress = Direction.All
        >>> r._check()
        Traceback (most recent call last):
            ...
        RoomEgressError
        >>> r = Room()
        >>> r._egress = Direction.North
        >>> r._check()
        Traceback (most recent call last):
            ...
        RoomError
        >>> r = Room()
        >>> r._check()
        """
        assert isinstance(walls, int)
        assert not (walls & ~Direction.All)
        assert isinstance(egress, Direction)
        assert egress != Direction.All
        assert walls & egress == 0
        self._walls = walls
        self._egress = egress
        self._observers = weakref.WeakSet()

    @do_not_trace
    @invariant_checker
    def _check(self):
        """Logic Error"""
        if not isinstance(self._walls, int): raise TypeError
        if not isinstance(self._egress, Direction): raise TypeError
        if self._walls & ~Direction.All: raise RoomWallError
        if self._egress != Direction.Unknown and not self._egress: raise RoomEgressError
        if self._walls & self._egress: raise RoomError

    # don't check
    def __str__(self):
        """
        >>> str(Room(walls=0))
        'Room()'
        >>> str(Room(walls=Direction.North))
        'Room(walls=N)'
        >>> str(Room())
        'Room(walls=NSEW)'
        >>> str(Room(walls=0, egress=Direction.North))
        'Room(egress=N)'
        """
        fields = []
        try:
            walls = self._walls
            if walls != 0:
                field = "walls="
                if walls & Direction.North: field += "N"
                if walls & Direction.South: field += "S"
                if walls & Direction.East: field += "E"
                if walls & Direction.West: field += "W"
                fields.append(field)
        except Exception:
            pass
        try:
            egress = self._egress
            if egress:
                fields.append("egress=" + str(egress))
        except Exception:
            pass
        try:
            self._check()
        except Exception as excp:
            fields.append("error=" + repr(excp))
        result = "Room(" + ", ".join(fields) + ")"
        return result

    @property
    def walls(self):
        """Walls around the room"""
        return self._walls

    @walls.setter
    def walls(self, walls: int):
        assert isinstance(walls, int)
        assert not (walls & ~Direction.All)
        assert walls & self._egress == 0
        if self._walls != walls:
            self._walls = walls
            for observer in self._observers.copy():
                try:
                    observer.walls_update(self, walls)
                except AttributeError:
                    pass

    @query
    def is_sealed(self):
        """Is the room sealed (i.e. has all 4 walls)

        >>> Room(walls=0).is_sealed()
        False
        >>> Room().is_sealed()
        True
        """
        return self.walls == Direction.All

    @query
    def can_move(self, direction):
        """Is movement allowed in specified direction, or is the way blocked by a wall?

        >>> Room(walls=0).can_move(Direction.North)
        True
        >>> Room().can_move(Direction.North)
        False
        >>> Room().can_move(Direction.East)
        False
        >>> Room().can_move(Direction.South)
        False
        >>> Room().can_move(Direction.West)
        False
        """
        assert direction
        return self._walls & direction == 0

    @procedure
    def remove_wall(self, direction):
        """remove the wall in the specified direction.

        >>> r = Room()
        >>> r.remove_wall(Direction.North)
        >>> r.can_move(Direction.North)
        True
        >>> r = Room()
        >>> r.remove_wall(Direction.North)
        >>> r.can_move(Direction.East)
        False
        >>> r = Room()
        >>> r.remove_wall(Direction.North)
        >>> r.can_move(Direction.South)
        False
        >>> r = Room()
        >>> r.remove_wall(Direction.North)
        >>> r.can_move(Direction.West)
        False
        >>> r = Room()
        >>> r.remove_wall(Direction.East)
        >>> r.can_move(Direction.East)
        True
        >>> r = Room()
        >>> r.remove_wall(Direction.South)
        >>> r.can_move(Direction.South)
        True
        >>> r=Room()
        >>> r.remove_wall(Direction.West)
        >>> r.can_move(Direction.West)
        True
        """
        assert direction
        if self._walls & direction != 0:
            self.walls &= ~direction

    @query
    def exits(self):
        """
        >>> Room().exits()
        []
        >>> r= Room()
        >>> r.remove_wall(Direction.North)
        >>> r.exits() == [Direction.North]
        True
        """
        return Direction.range(~self._walls)

    @property
    def egress(self):
        """Direction to the exit"""
        return self._egress

    @egress.setter
    def egress(self, direction):
        assert direction
        if self._walls & direction != 0:
            self.remove_wall(direction)
        if self._egress != direction:
            self._egress = direction
            for observer in self._observers.copy():
                try:
                    observer.egress_update(self, direction)
                except AttributeError:
                    pass

    def attach(self, observer):
        self._observers.add(observer)

    def detatch(self, observer):
        self._observers.remove(observer)


@traced_methods
class Maze(collections.abc.MutableMapping):
    """
    A class that represents a maze.

    Essentially it is a mapping from positions to Rooms.
    For convenience, many of the methods on Rooms are repeated, parameterised by the room position.
    """

    def __init__(self, shape: np.ndarray):
        super().__init__()
        self._rooms = np.empty(shape, dtype=np.object_)
        for p in self:
            self[p] = Room()

    # Methods to implement the mapping

    def __len__(self):
        return self._rooms.size

    def __getitem__(self, key: np.ndarray):
        return self._rooms[tuple(key)]

    def __setitem__(self, key: np.ndarray, value: Room):
        self._rooms[tuple(key)] = value

    def __delitem__(self, key: np.ndarray):
        raise RuntimeError

    def __iter__(self):
        for position in itertools.product(*[range(limit) for limit in self._rooms.shape]):
            yield np.array(position)

    def __contains__(self, key: np.ndarray):
        return np.all(0 <= key) and np.all(key < self._rooms.shape)

    # Other Features

    @property
    def shape(self):
        """shape of maze"""
        return np.array(self._rooms.shape)

    def is_sealed(self, position: np.ndarray):
        return self[position].is_sealed()

    def can_move(self, position: np.ndarray, direction: Direction):
        return self[position].can_move(direction)

    def remove_wall(self, position: np.ndarray, direction: Direction):
        self[position].remove_wall(direction)

    def exits(self, position: np.ndarray):
        return self[position].exits()

    # maze processes

    def build(self):
        """
        Building the maze is implemented as a coroutine
        to allow the visualization of the build progress.
        """
        self._start = np.zeros_like(self._rooms.shape)
        self._start[0] = random.randrange(self._rooms.shape[0])
        position = self._start
        egress = Direction.South
        while (position in self):
            room = self[position]
            room.egress = egress
            yield position
            options = {}
            for direction in Direction.range():
                if direction != egress:
                    new_position = position + direction.offset()
                    if new_position in self:
                        if self.is_sealed(new_position):
                            options[direction] = new_position
            if options:
                direction = random.choice(tuple(options.keys()))
                room.remove_wall(direction)
                position = options[direction]
                egress = direction.reverse()
            else:
                position += egress.offset()
                if position in self:
                    egress = self[position].egress

    def random_pose(self):
        """
        Random player start position.
        Does not start player facing the wall.
        """
        position = np.array([random.randrange(limit) for limit in self._rooms.shape])
        direction = random.choice(self.exits(position))
        return (position, direction)

    def wall_2d_vertices(self, thickness=0.1):
        """
        Walk the maze building a 2D description of the wall, starting from the exit.

        The result is first built up in the positions list.
        The Walker follows the left hand wall.
        """
        wall_offset = {Direction.North: np.array([thickness, 1.0 - thickness]),
                       Direction.East: np.array([1.0 - thickness, 1.0 - thickness]),
                       Direction.South: np.array([1.0 - thickness, thickness]),
                       Direction.West: np.array([thickness, thickness])}
        walker_position = self._start.copy()
        walker_direction = Direction.North
        positions = [walker_position + np.array([thickness, 0.0])]
        while walker_position in self:
            room = self[walker_position]
            left = walker_direction.turn_left()
            if room.can_move(left):
                positions.append(walker_position + wall_offset[left])
                walker_direction = left
            elif room.can_move(walker_direction):
                pass
            else:
                positions.append(walker_position + wall_offset[walker_direction])
                right = walker_direction.turn_right()
                if room.can_move(right):
                    walker_direction = right
                else:
                    positions.append(walker_position + wall_offset[right])
                    walker_direction = walker_direction.reverse()
            walker_position += walker_direction.offset()
        positions.append(self._start + np.array([1.0 - thickness, 0.0]))
        return np.array(positions, dtype=np.float32)


__all__ = ('Room', 'Maze')

if __name__ == '__main__':
    import doctest
    doctest.testmod()
