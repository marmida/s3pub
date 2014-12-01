'''
Tests for s3pub.progress.

This isn't a unit test, because we would need to assert the results of
curses-like drawing.  I don't want to bother with that, for now, so the
developer must manually invoke this script and inspect the output.

You will probably need to explicitly set PYTHONPATH to run this script.
'''

import mock
import time

import s3pub.progress

def main():
    print 'Starting UploadProgressBar test'

    files = {
        'something/else/blah/a.foo': 5000,
        'something/not/dumb/stupid/b.foo': 10000,
    }
    pbar1 = s3pub.progress.UploadProgressBar(files)
    assert pbar1.maxval == 15000
    pbar1.change_file(files.keys()[0])
    for i in range(5):
        pbar1.increment(i * 1000)
        time.sleep(0.5)
    pbar1.change_file(files.keys()[1])
    for i in range(10):
        pbar1.increment(i * 1000)
        time.sleep(0.5)
    pbar1.finish()

    print 'Done'

if __name__ == '__main__':
    main()
