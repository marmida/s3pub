# s3pub

A tiny program for publishing content to [Amazon S3], especially for web hosting.

Given a path to local content on disk, `s3pub` will replicate it in S3, with rsync-like selection for only changed files. The created keys in S3 will resemble those on the local filesystem. If desired, `s3pub` will also trigger an [Amazon CloudFront] invalidation, in order to clear prior caches.

### Example

```
s3pub web-stuff/ mybucket/apath
```

## Credentials

You can provide your Amazon S3 credentials to `s3pub` in two ways:

1. From a file, specified by the `--config-file` option
1. On the command line, via the `--access-key` and `--secret-key` options

In the first case, the contents of the file should look like:

    aws_access_key: YOUR_ACCESS_KEY
    aws_secret_key: YOUR_SECRET_KEY

Credentials specified via the `--access-key` and `--secret-key` options override values read from the credentials file, if any.

You can create a restricted set of credentials for use with `s3pub` via [IAM].

## Installation

1. Download this repository as a zipfile
1. Unpack the archive
1. Create a virtualenv for `s3pub`:

 `python ~/src/virtualenv-1.11.6/virtualenv.py /tmp/v`
1. Install into this virtualenv the dependencies in `requirements/default.txt`:

 `/tmp/v/bin/pip install -r s3pub/requirements/default.txt`

1. Install s3pub:

 `/tmp/v/bin/pip install s3pub/`

1. You can now use `s3pub` from the virtualenv:
  
  `/tmp/v/bin/s3pub --help`
  
In the example commands above, I've used:

1. `/tmp/v` as the path to the virtualenv
1. `~/src/virtualenv-1.11.6/virtualenv.py` as the path to the virtualenv script
1. `s3pub` as the path to the expanded zipfile

## Running tests

[![Build Status](https://travis-ci.org/marmida/s3pub.svg?branch=master)](https://travis-ci.org/marmida/s3pub)

`s3pub` has a fledgling test suite. There are both unit tests and functional tests. To run these:

1. install into your virtualenv the dependencies in `requirements/development.txt`.
1. cd into the s3pub directory.
1. Run `nosetests` for unit tests and `behave` for functional tests. Note that the `behave` test suite requires configuration and write access to S3, as it does actually upload files.

### Notes on behavioral testing

It's hard to test some things under `behave` - namely, invalidations. This is
because they take too long to complete - sometimes up to 15 minutes - and can
hit time limits imposed by CI services.

Second, it's hard to guarantee a sterile environment in which to test
invalidations - unless we communicate exactly which invalidation is
being started, the test can only check for the presence of at least one
pending invalidation, and that can be fooled by a previous or contemporaneous
run, which is extremely problematic in the context of tox.

Since `s3pub` primarily communicates via progress bars, it's not trivial to
recover things like the invalidation ID from stderr.

All of this has led me to avoid testing invalidations via the test suite, for
now.

## Alternatives

Since writing this, I've discovered a more feature-complete analog: [s3_website](https://github.com/laurilehmijoki/s3_website).

...and a less-featureful alternative: [alotofeffort](https://github.com/audreyr/alotofeffort)

[IAM]: http://aws.amazon.com/iam/
[Amazon S3]: http://aws.amazon.com/s3/
[Amazon CloudFront]: http://aws.amazon.com/cloudfront/
