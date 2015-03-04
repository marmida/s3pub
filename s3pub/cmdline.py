'''
Command-line interface routines.
'''

from __future__ import absolute_import

import argparse
import os.path
import yaml
from yaml.error import YAMLError

import s3pub.invalidate
import s3pub.upload

DEFAULT_CONFIG_PATH = os.path.expanduser('~/.s3pub.conf')
DESCRIPTION = '''\
Publish content to S3 for use with web hosting.

Mirrors local directories to S3, uploading only files that have changed or been
added, and optionally removing files that have been deleted.

Also optionally issues CloudFront invalidations for files modified or removed.
'''
EPILOG = '''
With regards to the mirroring of paths: this program does not follow
the rsync convention of trailing slashes; i.e. local paths with and without
trailing slashes are equivalent, and remote paths will be created relative to
the contents of the local path. This may force you to locally create container
directories, sorry.
'''

class Credentials(object):
    '''
    Represents an AWS access key pair.
    '''
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key

    def as_dict(self):
        '''
        Return a dict for use with boto connection objects.
        '''
        return {
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key,
        }

def _find_first(name, containers):
    '''
    Retun the first truthy occurrence of name in containers.
    '''
    for container in containers:
        try:
            val = container[name]
            if val:
                return val
        except (KeyError, TypeError):
            pass
        val = getattr(container, name, False)
        if val:
            return val
    # we didn't find it; return None

def cascade(containers, names):
    '''
    Lookup names in containers, respecting their order of precedence.

    Containers are queried using either [] or getattr. Underscores are
    swapped for dashes when searching for attributes.

    Returns a tuple of the found values; indices correspond to the input.
    None is returned when nothing was found. A value must be truthy in order to
    be considered.
    '''
    return tuple(_find_first(name, containers) for name in names)

def parse_args():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG,
    )
    parser.add_argument('src', help='Path to local content to upload')
    parser.add_argument(
        'dest',
        help='Destination for uploaded content (bucket/key)',
    )
    parser.add_argument(
        '-d',
        '--distrib-id',
        help='If provided, CloudFront distribution ID to invalidate.',
    )
    parser.add_argument(
        '--no-delete',
        dest='delete',
        action='store_false',
        help='Do not remove files from S3 that don\'t exist locally',
    )
    parser.add_argument(
        '--aws-access-key', 
        help='AWS Access Key',
    )
    parser.add_argument(
        '--aws-secret-key', 
        help='AWS Secret Access Key',
    )
    parser.add_argument(
        '--config',
        default=DEFAULT_CONFIG_PATH,
        help='Path to configuration file (optional; default: %(default)s)',
    )
    args = parser.parse_args()

    if args.config and args.config != DEFAULT_CONFIG_PATH \
            and not os.path.isfile(args.config):
        parser.error(
            'Could not read configuration file: {0}'.format(args.config))

    try:
        with open(args.config) as config_fp:
            config = yaml.load(config_fp)
    except IOError:
        # file doesn't exist, just assume creds come from args
        creds = (args.aws_access_key, args.aws_secret_key)
    except YAMLError:
        parser.error(
            'Configuration file is improperly formatted: {}'.format(
                args.config))
    else:
        # file was read properly; conditionally override args over config.
        creds = cascade([args, config], ['aws_access_key', 'aws_secret_key'])
    
    if not all(i for i in creds):
        parser.error(
            'Missing at least one of AWS access key or AWS secret key; use the'
            ' command-line options or a configuration file to provide these.'
        )
    args.creds = Credentials(*creds)

    return args

def main():
    args = parse_args()
    
    inval_keys = s3pub.upload.do_upload(
        args.src.decode('utf-8'),
        args.dest.decode('utf-8'),
        args.delete,
        args.creds,
    )
    if args.distrib_id and inval_keys:
        s3pub.invalidate.do_invalidate(args.distrib_id, inval_keys, args.creds)
