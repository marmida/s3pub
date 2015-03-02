from __future__ import absolute_import

import boto
import boto.s3.connection
import boto.s3.key
import boto.s3.bucket
import functools
import itertools
import os.path
import posixpath
from six import iteritems, itervalues
import sys

import s3pub.progress

def _upload(bucket, local_path, remote_path, md5, pbar):
    '''
    Upload a file to S3 if etags differ, or the remote doesn't exist.

    Return True if the file was uploaded; false otherwise.
    '''
    pbar.change_file(local_path)
    # begin upload
    boto.s3.key.Key(bucket, remote_path).set_contents_from_filename(
        local_path,
        policy='public-read',
        cb=functools.partial(_xfer_status, pbar),
        md5=md5,
    )

def _xfer_status(pbar, done, _):
    pbar.increment(done)

def _remote_path(dest, local_path, src_root):
    '''
    Return the key corresponding to a local path.

    'os.path' is dynamically mapped to the relevant path module at runtime.
    The 'ntpath' version of 'relpath' returns absolute paths when its second
    argument is omitted; we avoid this by using 'posixpath' and converting
    directory separators, since all s3 paths use forward slashes.
    '''
    local_path = local_path.replace('\\', '/')
    src_root = src_root.replace('\\', '/')
    return (dest and dest + '/' or '') + \
        posixpath.relpath(local_path, src_root)

def _todos(bucket, prefix, paths, check_removed=True):
    '''
    Return information about upcoming uploads and deletions.

    Returns a tuple: (upload, delete) 
    
    'upload' is a dictionary of info about files that need to be uploaded.
    It is keyed on local paths, and maps to a tuple:
    ((hex_md5, base64_md5, filesize), remote_path)

    'delete' is a list of S3 keys that should be removed.  If 'check_removed'
    is False, this list will always be empty.
    '''
    # map rpath -> lpath; we use this to compare md5s for existing keys
    rpath_map = dict((i[1], i[0]) for i in paths)
    
    # Iterate through the BucketListResultSet only once; we'll add elements to
    # two containers and will return them at the end.
    up = {}
    delete = []

    # Create a set of keys in S3 for comparison later
    s3_keys = set()

    # add entries for keys that have different contents
    for key in bucket.list(prefix):
        # Since we're already iterating through the result set, we'll save
        # key names.
        s3_keys.add(key.name)

        if check_removed and key.name not in rpath_map:
            # this key doesn't exist locally, schedule deletion
            delete.append(key.name)
            continue
        
        # file exists in both; compare md5s
        lpath = rpath_map[key.name]
        with open(lpath, 'rb') as fp:
            md5 = boto.s3.key.compute_md5(fp)
        if key.etag.strip('"') != md5[0].strip('"'):
            up[lpath] = (md5, key.name)

    # schedule uploads for new keys
    for rpath in set(i[1] for i in paths) - s3_keys:
        lpath = rpath_map[rpath]
        with open(lpath, 'rb') as fp:
            md5 = boto.s3.key.compute_md5(fp)
        up[lpath] = (md5, rpath)
        
    return up, delete

def _split_dest(dest):
    '''
    Split apart the bucket name and key prefix for uploads.
    '''
    dest = dest.strip()
    if not dest:
        raise ValueError(u'invalid value: {}'.format(dest))

    idx = dest.find(u'/')
    if idx == -1:
        return (dest, u'')
    return (dest[:idx], dest[idx+1:])

def _get_index_doc(bucket):
    '''
    Return the configured index document name for the bucket.
    '''
    try:
        conf = bucket.get_website_configuration()
    except boto.exception.S3ResponseError:
        return

    return conf['WebsiteConfiguration']['IndexDocument']['Suffix']

def do_upload(src, dst, delete, creds):
    '''
    Upload and delete files as necessary to synchronize S3.

    Return a list of remote keys modified.
    '''
    conn = boto.s3.connection.S3Connection(**creds.as_dict())
    # split bucket name from key prefix
    bucket_name, prefix = _split_dest(dst)
    bucket = conn.get_bucket(bucket_name)

    # paths is a list of tuples: (local, remote)
    paths = []
    for root, _, files in os.walk(src):
        for filename in files:
            lpath = os.path.join(root, filename)
            paths.append((lpath, _remote_path(prefix, lpath, src)))
    
    to_upload, to_delete = _todos(bucket, prefix, paths, delete)

    if not to_upload and not to_delete:
        return []
    
    inval_paths = []
    if to_upload: 
        # do upload
        pbar = s3pub.progress.UploadProgressBar(
            dict((lpath, info[2]) for lpath, (info, _) in iteritems(to_upload)))
        for lpath, (md5, rpath) in iteritems(to_upload):
            _upload(bucket, lpath, rpath, md5, pbar)
            inval_paths.append(rpath)
        pbar.finish()

    indexname = _get_index_doc(bucket)
    if indexname:
        inval_paths.extend(
            itertools.chain.from_iterable(
                # add index paths with and without trailing slash
                [os.path.dirname(rpath), os.path.dirname(rpath) + '/'] for 
                    _, rpath in itervalues(to_upload)
                    if os.path.basename(rpath) == indexname
            )
        )

    if delete and to_delete:
        # do deletion
        mdr = bucket.delete_keys(to_delete)
        if mdr.errors:
            sys.stderr.write(
                'ERROR: problems were encountered trying to remove the '
                    'following objects.\n')
            for e in mdr.errors:
                sys.stderr.write(u'  {} - {} - {}\n'.format(
                    e.key, e.code, e.message))
            raise Exception('Errors reported by S3')
        inval_paths.extend(to_delete)

    return inval_paths
