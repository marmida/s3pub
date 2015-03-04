'''
Tests for s3pub.cmdline.
'''

from __future__ import absolute_import

from nose.tools import assert_equal
from six import iteritems

from s3pub import cmdline

class Struct(object):
    '''
    A dumb container for attributes.

    We use this instead of MagicMock, to allow AtttributeError to be raised.
    '''
    def __init__(self, **kwargs):
        '''
        Assign attributes from kwargs.
        '''
        for name, val in iteritems(kwargs):
            setattr(self, name, val)

def test_find_first():
    args_ls = [
        # (name, containers, expected)
        ('a', [Struct(a=1, c=0), Struct(a=2, c=0)], 1),
        ('b', [Struct(a=1, c=0), Struct(a=2, c=0)], None),
        ('a', [{'a': 2, 'c': 0}, Struct(a=1, c=0)], 2),
        ('a_b', [Struct(c=0), {'a_b': 2, 'c': 0}], 2),
        ('a_b', [{'a_b': 2, 'c': 0}, Struct(a_b=1, c=0)], 2),
        ('a_b', [{'c': 0}, Struct(a_b=1, c=0)], 1),
    ]
    for args in args_ls:
        yield (_test_find_first, ) + args

def _test_find_first(name, containers, expected):
    assert_equal(expected, cmdline._find_first(name, containers))

def test_cascade():
    args_ls = [
        # (containers, names, expected)
        (
            [Struct(a=1, c=3), Struct(a=2, b=9, e=False)],
            ['a', 'b', 'c', 'd', 'e'],
            (1, 9, 3, None, None),
        ),
        (
            [{'a': 1, 'c': 3, 'e': False}, Struct(a=2, b=9)],
            ['a', 'b', 'c', 'd', 'e'],
            (1, 9, 3, None, None),
        )
    ]
    for args in args_ls:
        yield (_test_cascade, ) + args

def _test_cascade(containers, names, expected):
    assert_equal(expected, cmdline.cascade(containers, names))
