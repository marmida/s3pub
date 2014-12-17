'''
Environment setup for s3pub behave tests.
'''

from __future__ import absolute_import

from boto.s3.connection import S3Connection
import hashlib
import os
import os.path
import random
import requests
import shutil
import tempfile
import types
import yaml
import yurl

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'test_config.yaml')

def rand_token():
    '''
    Generate a string of random hex chars.
    '''
    h = hashlib.sha1()
    h.update(str(random.random()))
    return h.hexdigest()[:10]

def rand_path(subdirs=0):
    '''
    Return a path of randomized components.
    '''
    return '/'.join([rand_token()] + [rand_token() for _ in xrange(subdirs)])

class TempFileManager(object):
    '''
    Create temporary files and directories with random names and content.

    Remove them all on exit.
    '''
    def __init__(self):
        self.registry = {}
        self.root = tempfile.mkdtemp()

    def cleanup(self):
        '''
        Remove all temporary files on disk.
        '''
        shutil.rmtree(self.root)
        self.registry = {}
        self.root = None

    def create(self, subdirs=0):
        '''
        Create a new file with random content and a random filename.

        If subdirs > 0, add that many layers of directories with random names.
        '''
        path = rand_path(subdirs)
        temp_path = os.path.join(self.root, path)
        if subdirs:
            os.makedirs(os.path.dirname(temp_path))
        self.registry[path] = rand_token()
        with open(temp_path, 'w') as temp_fp:
            temp_fp.write(self.registry[path])

    def __iter__(self):
        '''
        Return an iterable of (path, contents) tuples for all temp files.
        '''
        return self.registry.iteritems()

    def iterkeys(self):
        return self.__iter__()

def before_all(context):
    with open(CONFIG_PATH) as config_fp:
        context.config = yaml.safe_load(config_fp)
    context.base_url = yurl.URL(context.config['s3-url'])

    def request(self, path):
        return requests.get(self.base_url.replace(path=path).as_string())
    context.request = types.MethodType(request, context)

    context.connection = S3Connection(
        context.config['access-key'], context.config['secret-access-key'])
    context.bucket = context.connection.get_bucket(context.config['bucket'])
    
def before_scenario(context, _):
    context.tempfiles = TempFileManager()

def after_scenario(context, _):
    context.tempfiles.cleanup()
