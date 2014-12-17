'''
Step implementations.
'''

from __future__ import absolute_import

from behave import given, when, then
from nose.tools import assert_equal

import s3pub.upload

@given('that no files exist in the bucket')
def init_empty_bucket(context):
    context.bucket.delete_keys([key.name for key in context.bucket.list()])

@when('I publish new test content to the bucket')
def init_content_and_publish(context):
    context.tempfiles.create()
    context.tempfiles.create(subdirs=1)
    context.tempfiles.create(subdirs=2)
    s3pub.upload.do_upload(
        context.tempfiles.root,
        context.config['bucket'],
        True,
        (context.config['access-key'], context.config['secret-access-key']),
    )

@then('the test content should be available from the bucket\'s S3 URL')
def assert_s3_web(context):
    for path, content in context.tempfiles:
        resp = context.request(path)
        resp.raise_for_status()
        assert_equal(content, resp.text)

@given('that previous test content exists in the bucket')
def init_non_empty_bucket(context):
    assert False

@then('the previous test content should not be available from the bucket\'s S3 URL')
def assert_old_s3_web(context):
    to_assert = [
        path for path in context.old_content
            if not path.endswith('index.html')]
    assert to_assert
    for path in to_assert:
        assert_equal(404, context.request(path))
            
