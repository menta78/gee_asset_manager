#! /usr/bin/env python

import argparse
import json
import logging
import logging.config
import os

import ee

import batch_uploader


def setup_logging(path):
    with open(path, 'rt') as f:
        config = json.load(f)
    logging.config.dictConfig(config)


def delete_collection(id):
    logging.info('Attempting to delete collection %s', id)
    if 'users' not in id:
        root_path_in_gee = ee.data.getAssetRoots()[0]['id']
        id = root_path_in_gee + '/' + id
    params = {'id': id}
    items_in_collection = ee.data.getList(params)
    for item in items_in_collection:
        ee.data.deleteAsset(item['id'])
    ee.data.deleteAsset(id)
    logging.info('Collection %s removed', id)


def cancel_all_running_tasks():
    logging.info('Attempting to cancel all running tasks')
    running_tasks = [task for task in ee.data.getTaskList() if task['state'] == 'RUNNING']
    for task in running_tasks:
        ee.data.cancelTask(task['id'])
    logging.info('Cancel all request completed')


def get_filename_from_path(path):
    return os.path.splitext(os.path.basename(os.path.normpath(path)))[0]


def cancel_all_running_tasks_from_parser(args):
    cancel_all_running_tasks()
    

def delete_collection_from_parser(args):
    delete_collection(args.id)


def upload_from_parser(args):
    batch_uploader.upload(user=args.user,
                          path_for_upload=args.directory,
                          metadata_path=args.metadata,
                          collection_name=args.collection or get_filename_from_path(args.directory))


def main(args=None):
    setup_logging(path=os.path.join(os.path.dirname(__file__), 'logconfig.json'))
    parser = argparse.ArgumentParser(description='Google Earth Engine Batch Asset Manager')

    subparsers = parser.add_subparsers()
    parser_delete = subparsers.add_parser('delete', help='Deletes collection and all items inside.')
    parser_delete.add_argument('id', help='ID of the collection, either fully qualified or abbreviated (no need to pass users/username).')
    parser_delete.set_defaults(func=delete_collection_from_parser)

    parser_upload = subparsers.add_parser('upload', help='Batch Asset Uploader.')
    required_named = parser_upload.add_argument_group('Required named arguments.')
    required_named.add_argument('-u', '--user', help='Google account name (gmail address).', required=True)
    required_named.add_argument('-d', '--directory', help='Path to the directory with images.', required=True)
    optional_named = parser_upload.add_argument_group('Optional named arguments')
    optional_named.add_argument('-m', '--metadata', help='Path to CSV with metadata.')
    optional_named.add_argument('-c', '--collection', help='Name of the collection to create. If not provided, '
                                                           'directory name will be used.')
    parser_upload.set_defaults(func=upload_from_parser)

    parser_cancel = subparsers.add_parser('cancel', help='Cancel all running tasks')
    parser_cancel.set_defaults(func=cancel_all_running_tasks_from_parser)

    args = parser.parse_args()
    ee.Initialize()
    args.func(args)

if __name__ == '__main__':
    main()