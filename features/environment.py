'''
Environment setup for s3pub behave tests.
'''

from __future__ import absolute_import

from boto.s3.connection import S3Connection
import hashlib
import os.path
import random
import requests
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
    def __init__(self):
        self.root = None
        self.registry = {}

    def __enter__(self):
        self.root = tempfile.mkdtemp()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        shutil.rmtree(self.root)

    def create(self, subdirs=0):
        path = rand_path(subdirs)
        self.registry[path] = rand_token()
        with open(os.path.join(self.root, path), 'w') as temp_fp:
            temp_fp.write(self.registry[path])

    def __iter__(self):
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

    context.bucket = context.connect_s3().get_bucket(context.config['bucket'])
    
