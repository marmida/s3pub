'''
Environment setup for s3pub behave tests.
'''

from __future__ import absolute_import

from boto.s3.connection import S3Connection
import os.path
import requests
import types
import yaml
import yurl

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'test_config.yaml')

def before_all(context):
    with open(CONFIG_PATH) as config_fp:
        context.config = yaml.safe_load(config_fp)
    context.base_url = yurl.URL(context.config['s3-url'])

    def request(self, path):
        return requests.get(
            self.base_url.replace(path=path).as_string()).status_code
    context.request = types.MethodType(request, context)

    def connect_s3(self):
        return S3Connection(
            context.config['access-key'], context.config['secret-access-key'])
    context.connect_s3 = types.MethodType(connect_s3, context)
