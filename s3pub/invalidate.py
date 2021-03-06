'''
CloudFront invalidation routines.
'''

from __future__ import absolute_import, print_function

from boto.cloudfront import CloudFrontConnection
import time

import s3pub.progress

def get_distribution(connection, distrib_id):
    '''
    Return a boto Distribution object for a distribution ID.
    '''
    dists = [i for i in connection.get_all_distributions() if
        i.id == distrib_id]
    if dists:
        return dists[0]
    raise ValueError('invalid distribution id: {}'.format(distrib_id))

def do_invalidate(distrib_id, inval_keys, creds):
    '''
    Send a CloudFront invalidation request for the given objects.
    '''
    cf = CloudFrontConnection(**creds.as_dict())
    distrib = get_distribution(cf, distrib_id)
    req = cf.create_invalidation_request(distrib.id, inval_keys)

    pbar = s3pub.progress.InvalidationProgressBar(req.id)
    for _ in pbar(Monitor(cf, distrib_id, req.id)):
        pass
    print('Done.')

class Monitor(object):
    '''
    An iterable that returns True until a CloudFront invalidation completes.
    '''
    # seconds to wait between animation ticks
    ANIMATE_DELAY = 0.2
    # seconds to wait between CloudFront invalidation request status updates
    POLL_DELAY = 5

    def __init__(self, connection, distrib_id, req_id):
        self.connection = connection
        self.distrib_id = distrib_id
        self.req_id = req_id
        self.last_req = 0

    def __iter__(self):
        return self

    def next(self):
        now = time.time()
        if now - self.last_req > self.POLL_DELAY:
            self.last_req = now
            if self.connection.invalidation_request_status(
                    self.distrib_id, self.req_id).status == 'Completed':
                raise StopIteration
        
        time.sleep(self.ANIMATE_DELAY)
        # iterate indefinitely
        return True

