from __future__ import absolute_import

import argparse

import s3pub.invalidate
import s3pub.upload

def parse_args():
    parser = argparse.ArgumentParser(
        description='TODO: write me',
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
    return parser.parse_args()

def main():
    args = parse_args()
    inval_keys = s3pub.upload.do_upload(
        args.src.decode('utf-8'),
        args.dest.decode('utf-8'),
        args.delete,
    )
    if args.distrib_id and inval_keys:
        s3pub.invalidate.do_invalidate(args.distrib_id, inval_keys)
