#!/usr/bin/env python3
"""
direction.py
Copyright 2017 Steve Palmer
"""

import random
import enum
import collections

import numpy as np

from utils import traced_methods


@traced_methods
@enum.unique
class Direction(enum.IntEnum):
    """
    This class encodes and provides utilities for the normal four cardinal directions:
    North, East, South and West.

    The directions are encoded so that the integer values correspond to different bit positions.
    Therefore, they can be OR'ed to form new directions that are distinctive, such as Direction.North | Direction.West
    Or, as in this case, a simple integer can be used as a set of directions.
    """

    Unknown = 0
    North = 1
    East = 2
    South = 4
    West = 8
    All = 15

    def __str__(self):
        """
        An abbreviated output for the directions.

        >>> str(Direction.Unknown)
        ''
        >>> str(Direction.North)
        'N'
        >>> str(Direction.East)
        'E'
        >>> str(Direction.South)
        'S'
        >>> str(Direction.West)
        'W'
        >>> str(Direction.All)
        'NSEW'
        """
        result = ""
        if self & Direction.North:
            result += "N"
        if self & Direction.South:
            result += "S"
        if self & Direction.East:
            result += "E"
        if self & Direction.West:
            result += "W"
        if self & ~Direction.All:
            result += "?"
        return result

    def __bool__(self):
        """A direction is True if it is one of North, East, South or West

        >>> bool(Direction.Unknown)
        False
        >>> bool(Direction.North)
        True
        >>> bool(Direction.East)
        True
        >>> bool(Direction.South)
        True
        >>> bool(Direction.West)
        True
        >>> bool(Direction.All)
        False
        """
        return Direction.Unknown < self < Direction.All

    def turn_left(self):
        """Turn left.

        >>> Direction.Unknown.turn_left() == Direction.Unknown
        True
        >>> Direction.North.turn_left() == Direction.West
        True
        >>> Direction.East.turn_left() == Direction.North
        True
        >>> Direction.South.turn_left() == Direction.East
        True
        >>> Direction.West.turn_left() == Direction.South
        True
        >>> Direction.All.turn_left() == Direction.All
        True
        """
        result = self >> 1
        if self & 1:
            result |= 8
        result = Direction(result)
        assert not self or result
        return result

    def turn_right(self):
        """Turn right.

        >>> Direction.Unknown.turn_right() == Direction.Unknown
        True
        >>> Direction.North.turn_right() == Direction.East
        True
        >>> Direction.East.turn_right() == Direction.South
        True
        >>> Direction.South.turn_right() == Direction.West
        True
        >>> Direction.West.turn_right() == Direction.North
        True
        >>> Direction.All.turn_right() == Direction.All
        True
        """
        result = (self & 7) << 1
        if self & 8:
            result |= 1
        result = Direction(result)
        assert not self or result
        return result

    def reverse(self):
        """Turn around.

        >>> Direction.Unknown.reverse() == Direction.Unknown
        True
        >>> Direction.North.reverse() == Direction.South
        True
        >>> Direction.East.reverse() == Direction.West
        True
        >>> Direction.South.reverse() == Direction.North
        True
        >>> Direction.West.reverse() == Direction.East
        True
        >>> Direction.All.reverse() == Direction.All
        True
        """
        result = Direction(self >> 2 | (self & 3) << 2)
        assert not self or result
        return result

    @staticmethod
    def range(mask: int = None):
        """
        >>> len(Direction.range())
        4
        >>> Direction.range().index(Direction.North)
        0
        >>> Direction.range().index(Direction.East)
        1
        >>> Direction.range().index(Direction.South)
        2
        >>> Direction.range().index(Direction.West)
        3
        """
        if mask is None:
            result = tuple(_DATA.keys())
        else:
            result = [direction for direction in _DATA if mask & direction]
        return result

    @classmethod
    def random(cls):
        result = random.choice(Direction.range())
        assert result
        return result

    def right_angle_bearing(self):
        """
        >>> Direction.North.right_angle_bearing()
        0
        >>> Direction.East.right_angle_bearing()
        1
        >>> Direction.South.right_angle_bearing()
        2
        >>> Direction.West.right_angle_bearing()
        3
        """
        try:
            result = _DATA[self].bearing
        except KeyError:
            result = None
        return result

    def offset(self):
        """
        >>> Direction.North.offset()
        array([0, 1])
        >>> Direction.East.offset()
        array([1, 0])
        >>> Direction.South.offset()
        array([ 0, -1])
        >>> Direction.West.offset()
        array([-1,  0])
        """
        return _DATA[self].offset


_DataItem = collections.namedtuple("DataItem", ["bearing", "offset"])


_DATA = collections.OrderedDict(
    [
        (Direction.North, _DataItem(0, np.array([0, 1]))),
        (Direction.East, _DataItem(1, np.array([1, 0]))),
        (Direction.South, _DataItem(2, np.array([0, -1]))),
        (Direction.West, _DataItem(3, np.array([-1, 0]))),
    ]
)


__all__ = ["Direction"]

if __name__ == "__main__":
    import doctest

    doctest.testmod()
