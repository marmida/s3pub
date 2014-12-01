'''
Progress bar customizations.
'''

import progressbar

# Notes about progressbar: each ProgressBar has only one maximum, but we
# ideally want two (files and bytes).  Trying to animate two bars
# simultaneously just confuses progressbar.  We can work around this by
# changing text widgets in the bar during each update.

TMPL = '{filename} ({cur}/{max}) '

class UploadProgressBar(progressbar.ProgressBar):
    def __init__(self, files):
        '''
        Ctor.  'files' is a dictionary mapping local paths to file sizes.
        '''
        self.files = files
        self.upload_num = 0
        # 'uploaded_bytes' stores the number of bytes uploaded as of the last
        # completed file.  This is important because 'update' expects the
        # number of bytes towards the entire file set.
        self.uploaded_bytes = 0
        self.last_file = None
        widgets = [
            'placeholder',
            progressbar.Percentage(),
            ' ',
            progressbar.Bar(left='[', right=']'),
            ' ',
            progressbar.ETA(),
            ' ',
            progressbar.FileTransferSpeed()
        ]
        super(UploadProgressBar, self).__init__(
            widgets=widgets, maxval=sum(i for i in files.values()))

    def change_file(self, path):
        '''
        Must be called before each 'update' call for a new file.
        '''
        if self.last_file:
            self.uploaded_bytes += self.files[self.last_file]
        self.last_file = path
        self.upload_num += 1
        self.widgets[0] = TMPL.format(
            filename=path, cur=self.upload_num, max=len(self.files))

        # first call to this function should run the parent class's 'start'
        if not self.start_time:
            super(UploadProgressBar, self).start()

    def increment(self, val):
        self.update(self.uploaded_bytes + val)

    def start(self):
        raise NotImplementedError('use change_file instead')

class InvalidationProgressBar(progressbar.ProgressBar):
    '''
    Display an animated spinner, and periodically poll for completion.
    '''
    def __init__(self, req_id):
        super(InvalidationProgressBar, self).__init__(widgets=[
            'Invalidation request {}: '.format(req_id),
            progressbar.AnimatedMarker()
        ])
