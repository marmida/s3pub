'''
Step implementations.
'''

from __future__ import absolute_import



@given('that no files exist in the bucket')
def init_empty_bucket(context):
    conn = context.connect_s3()
    bucket = conn.get_bucket(context.config['bucket'])
    bucket.delete_keys([key.name for key in bucket.list()])

@when('I publish new test content to the bucket')
def init_content_and_publish(context):
    assert False

@then('the test content should be available from the bucket\'s S3 URL')
def assert_s3_web(context):
    assert False

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
            
