'''
Tests for s3pub.upload.
'''

from __future__ import absolute_import

import boto.exception
import mock
from nose.tools import assert_equals, raises

from s3pub import upload

def test_split_dest():
    args_ls = [
        ('bucket/a/b/c', ('bucket', 'a/b/c')),
        ('bucket/a/b/c/', ('bucket', 'a/b/c/')),
        ('bucket/', ('bucket', '')),
        ('bucket', ('bucket', '')),
        (u'bucket/\u767e\u5ea6\u4e91\uff08\u7f51\u76d8\uff09', (u'bucket', u'\u767e\u5ea6\u4e91\uff08\u7f51\u76d8\uff09')),
    ]
    for args in args_ls:
        yield (_test_split_dest,) + args

@raises(ValueError)
def test_split_dest_error():
    upload._split_dest('')

def _test_split_dest(dst, expected):
    assert_equals(upload._split_dest(dst), expected)

def test_remote_path():
    args_ls = [
        (('', 'a', ''), 'a'),
        (('a', 'b', ''), 'a/b'),
        (('a', 'b/c', 'b'), 'a/c'),
        (('a', 'b/c/d/e', 'b'), 'a/c/d/e'),
        (('a', 'b/c/d/e', 'b/c/d'), 'a/e'),
        (('', './b', ''), 'b'),
        (('', './b', './'), 'b'),
        (('a', './b', './'), 'a/b'),
        (('', 'b\\c\\d', ''), 'b/c/d'),
        (('', '.\\b\\c\\d', '.\\'), 'b/c/d'),
        (('a/b', 'c\\d', '.'), 'a/b/c/d'),
        (('a/b', 'c\\d\\e', 'c\\d'), 'a/b/e'),
    ]
    for args in args_ls:
        yield (_test_remote_path,) + args

def _test_remote_path(args, expected):
    assert_equals(upload._remote_path(*args), expected)

def test_todos():
    args_ls = [
        (
            # case #1: both files already exist and need to be overwritten
            # local
            {
                'src/f1': 'abcd1234',
                'src/f2': 'bcde2345',
            },
            # remote
            {
                'dst/f1': 'xyz',
                'dst/f2': 'abc',
            },
            # expected
            (
                {
                    'src/f1': (('"abcd1234"', 'blah==', 1000), 'dst/f1'),
                    'src/f2': (('"bcde2345"', 'blah==', 1000), 'dst/f2'),
                },
                []
            )
        ),
        (
            # case #2: one file is already up-to-date
            # local
            {
                'src/f1': 'abcd1234',
                'src/f2': 'bcde2345',
            },
            # remote
            {
                'dst/f1': 'xyz',
                'dst/f2': 'bcde2345',
            },
            # expected
            (
                {
                    'src/f1': (('"abcd1234"', 'blah==', 1000), 'dst/f1'),
                },
                []
            )
        ),
        (
            # case #3: one file is missing from s3
            # local
            {
                'src/f1': 'abcd1234',
                'src/f2': 'bcde2345',
            },
            # remote
            {
                'dst/f1': 'abcd1234',
            },
            # expected
            (
                {
                    'src/f2': (('"bcde2345"', 'blah==', 1000), 'dst/f2'),
                },
                []
            )
        ),
        (
            # case #4: one file has been removed locally
            # local
            {
                'src/f2': 'xyz',
            },
            # remote
            {
                'dst/f1': 'abc',
                'dst/f2': 'xyz',
            },
            # expected
            (
                {},
                ['dst/f1']
            )
        )
    ]
    for args in args_ls:
        yield (_test_todos, ) + args

def _test_todos(local, remote, expected):
    paths = [(lpath, lpath.replace('src/', 'dst/')) for lpath in local.keys()]

    # Mocking strategy: replace 'open' with a side_effect-driven Mock;
    # this will return a mock File object with an extra attrib, 'md5',
    # which will be inspected by the mocked 'compute_md5' function.

    def _mock_open(lpath, _):
        m = mock.MagicMock(name='open()')
        m.__enter__.return_value = m
        m.md5 = local[lpath]
        return m
    mock_open = mock.MagicMock(side_effect=_mock_open)

    def _list(_):
        for rpath, retag in remote.iteritems():
            m = mock.MagicMock(etag='"' + retag + '"')
            # 'name' is a special kwarg for mocks; must use assignment
            m.name = rpath
            yield m
    
    def compute_md5(mock_fp):
        return ('"' + mock_fp.md5 + '"', 'blah==', 1000)
    
    bucket = mock.MagicMock(list=mock.MagicMock(side_effect=_list))
    with mock.patch('boto.s3.key.compute_md5', side_effect=compute_md5):
        with mock.patch('s3pub.upload.open', _mock_open, create=True):
            assert_equals(upload._todos(bucket, 'src', paths), expected)

def test_do_upload_nochanges():
    '''
    do_upload: does nothing when there are no changes.
    '''
    with mock.patch('s3pub.upload._todos', return_value=([], [])), \
            mock.patch('boto.connect_s3'):
        assert_equals(upload.do_upload('bogus', 'bogus', False), [])

def test_get_index_doc():
    '''
    _get_index_doc: correctly interprets website configurations.
    '''
    def raise_s3error(*args):
        raise boto.exception.S3ResponseError(None, None, None)

    mock_bucket = mock.MagicMock()
    mock_bucket.get_website_configuration.side_effect = raise_s3error
    assert_equals(upload._get_index_doc(mock_bucket), None)

    mock_bucket = mock.MagicMock()
    mock_bucket.get_website_configuration.return_value = {
        'WebsiteConfiguration': {
            'IndexDocument': {
                'Suffix': 'index.html'
            },
            'ErrorDocument': {
                'Key': '50x.html'
            }
        }
    }
    assert_equals(upload._get_index_doc(mock_bucket), 'index.html')

def _start_progressbar(bucket, local_path, remote_path, md5, pbar):
    '''
    Ensure we call the ProgressBar's "change_file".

    Meant to be used as a side_effect to a mock s3pub.upload._upload.
    '''
    pbar.change_file(local_path)

def test_do_upload_no_website():
    '''
    do_upload: returns only modified keys when there is no website.
    '''
    with mock.patch('s3pub.upload._todos') as mock_todos, \
            mock.patch('boto.connect_s3') as mock_connect, \
            mock.patch(
                's3pub.upload._upload', side_effect=_start_progressbar), \
            mock.patch('s3pub.upload._get_index_doc'):
        mock_todos.return_value = (
            {
                'path1': (('abcd', 'abcd==', 1234), '/path1'),
                'hello/index.html': 
                    (('abcd', 'abcd==', 1234), '/hello/index.html'),
            },
            ['/path2'],
        )
        assert_equals(
            upload.do_upload('bogus', 'bogus', False),
            ['/path1', '/hello/index.html'],
        )

        mock_bucket = mock_connect.return_value.get_bucket.return_value
        mock_bucket.delete_keys.return_value.errors = []
        assert_equals(
            upload.do_upload('bogus', 'bogus', True),
            ['/path1', '/hello/index.html', '/path2'],
        )
        mock_bucket.delete_keys.assert_called_once_with(['/path2'])

def test_do_upload_with_website():
    '''
    do_upload: adds directory paths when index documents are invalidated.
    '''
    with mock.patch('s3pub.upload._todos') as mock_todos, \
            mock.patch('boto.connect_s3'), \
            mock.patch(
                's3pub.upload._upload', side_effect=_start_progressbar), \
            mock.patch('s3pub.upload._get_index_doc') as mock_get_index_doc:
        mock_get_index_doc.return_value = 'index.html'
        mock_todos.return_value = (
            {
                'hello/index.html':
                    (('abcd', 'abcd==', 1234), '/hello/index.html'),
            },
            ['/path2'],
        )
        assert_equals(
            upload.do_upload('bogus', 'bogus', False),
            ['/hello/index.html', '/hello/'],
        )
