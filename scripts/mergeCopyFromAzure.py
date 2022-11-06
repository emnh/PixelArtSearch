#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ft=python ts=4 sw=4 sts=4 et fenc=utf-8
# Original author: "Eivind Magnus Hvidevold" <hvidevold@gmail.com>
# License: GNU GPLv3 at http://www.gnu.org/licenses/gpl.html

'''
'''

import sys
import re
import json
import os, uuid
import urllib.parse
import shutil
import time
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
from collections import defaultdict
from pprint import pprint
# from azure.storage.queue import (
#     QueueClient,
#     BinaryBase64EncodePolicy,
#     BinaryBase64DecodePolicy
# )

def main():
    'entry point'


def step3():
    with open('../local.settings.json') as fd:
        settings = json.load(fd)
    connectionString = settings["Values"]["AzureWebJobsStorage"]
    #os.environ["AZURE_STORAGE_CONNECTION_STRING"] = connectionString

    container_name = "opengameart"

    with open('allblobs2.txt') as fd:
        files = []
        sizes = []
        for line in fd.readlines():
            fname, size = line.split('\t')
            files.append(fname.strip())
            sizes.append(int(size))
        #files = [fname for fname in files if fname.lower().endswith('.jpg') or fname.lower().endswith('.png')]

    # Retrieve the connection string from an environment
    # variable named AZURE_STORAGE_CONNECTION_STRING
    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    # Create a unique name for the queue
    #q_name = "queue-" + str(uuid.uuid4())
    #q_name = 'sqlqueue'

    # Instantiate a QueueClient object which will
    # be used to create and manipulate the queue
    #queue_client = QueueClient.from_connection_string(connectionString, q_name)

    # Setup Base64 encoding and decoding functions
#     base64_queue_client = QueueClient.from_connection_string(
#         conn_str=connectionString, queue_name=q_name,
#         message_encode_policy = BinaryBase64EncodePolicy(),
#         message_decode_policy = BinaryBase64DecodePolicy()
#     )

    class Vars(): pass
    lvars = Vars()
    lvars.counts = defaultdict(lambda: 0)

    unpacked = []
    byfilename = {}
    byfilenameAndSize = defaultdict(lambda: [])
    with open('unpacked.txt') as fd:
        for line in fd.readlines():
            path = line.strip()
            unpacked.append(path)
            key = os.path.split(path)[-1]
            byfilename[key] = path
            try:
                key2 = (key, os.path.getsize(path))
            except:
                lvars.counts['failsize'] += 1
                pass
            byfilenameAndSize[key2].append(path.lower())

    lvars.existCount = 0
    lvars.existSize = 0
    lvars.notExistCount = 0
    lvars.notExistSize = 0
    lvars.prc = 0
    lvars.unpacked = set(unpacked)

    def updateExists(localpath, lvars):
        lvars.existCount += 1
        lvars.existSize += size
        lvars.counts['exist' + filetype] += 1
        if filetype == 'extracted':
            try:
                lvars.unpacked.remove(localpath)
            except:
                lvars.counts['unpackedRemoveFail'] += 1
                pass
    def linkfile(src, dest2):
        dest = '/mnt/data2/opengameart2/' + dest2
        dirname = os.path.split(dest)[0]
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if not os.path.exists(dest):
            shutil.copyfile(src, dest)

    ofd = open('copyFromAzure.txt', 'w')
    for i, (path, size) in enumerate(zip(files, sizes)):
        if i % 1000 == 0:
            print(i)
        if size == 0:
            continue
        if path.startswith('extract/files'):
            localpath = path[len('extract/files/'):]
            prefix = '/mnt/data/opengameart/unpacked/'
            unq = urllib.parse.unquote_plus
            localpath = unq(localpath)
            #print("UNQUOTED", localpath)
            #localpath = os.path.split(localpath)
            localpath = localpath.split('/')
            parts = [urllib.parse.quote(localpath[0])] + [unq(x) for x in localpath[1:]]
            parts2 = [urllib.parse.quote(localpath[0])] + [os.path.splitext(urllib.parse.quote(localpath[0]))[0]] + [unq(x) for x in localpath[1:]]
            #print("PARTS", parts)
            localpath = prefix + os.path.join(*parts)
            localpath2 = prefix + os.path.join(*parts2)
            filetype = 'extracted'
        elif path.startswith('files'):
            localpath = path[len('files'):]
            localpath2 = None
            prefix = '/mnt/data/opengameart/files'
            localpath = prefix + localpath
            filetype = 'file'
        else:
            localpath = path
            localpath2 = None
            prefix = ''
            filetype = 'other'

        #if i >= 1000:
        #    break
        key = (os.path.split(localpath)[-1], size)
        key2 = (os.path.split(localpath2)[-1], size) if localpath2 != None else None
        if os.path.exists(localpath) and os.path.getsize(localpath) == size:
            updateExists(localpath, lvars)
            linkfile(localpath, path)
        elif localpath2 != None and os.path.exists(localpath2) and os.path.getsize(localpath2) == size:
            updateExists(localpath2, lvars)
            linkfile(localpath2, path)
#         elif key in byfilenameAndSize and localpath.lower() in byfilenameAndSize[key]:
#             updateExists(localpath, lvars)
#             localpath3 = [x for x in byfilenameAndSize[key] if x == localpath.lower()][0]
#             linkfile(localpath3, path)
#         elif localpath2 != None and key2 in byfilenameAndSize and localpath2.lower() in byfilenameAndSize[key2]:
#             updateExists(localpath2, lvars)
#             localpath4 = [x for x in byfilenameAndSize[key2] if x == localpath2.lower()][0]
#             linkfile(localpath4, path)
        else:
            ofd.write(path + '\n')
#             if filetype == 'extracted':
#                 if key in byfilenameAndSize:
#                     byfname = byfilenameAndSize[key]
#                     print("LOCALPATH_EXPECTED:", localpath)
#                     print("LOCALPATH_FOUND___:", byfname)
#                     print("PARTS_____________:", '¤'.join(parts))
            if localpath.endswith('.png') and lvars.prc < 10:
                print(localpath)
                lvars.prc += 1
                #if prc == 10:
                #    break
            lvars.counts['notexist' + filetype] += 1
            lvars.notExistCount += 1
            lvars.notExistSize += size
        #base64_queue_client.send_message(message.encode('ascii'))
    print('exists', lvars.existCount, lvars.existSize / 1024 / 1024 / 1024, 'GiB')
    print('notExists', lvars.notExistCount, lvars.notExistSize / 1024 / 1024 / 1024, 'GiB')
    print("NOMATCH:")
    #for fname in unpacked:
    #    print(fname)
    pprint(lvars.counts)
    ofd.close()

def step4():
    with open('../local.settings.json') as fd:
        settings = json.load(fd)
    connectionString = settings["Values"]["AzureWebJobsStorage"]

    # Create the BlobServiceClient object which will be used to create a container client
    blob_service_client = BlobServiceClient.from_connection_string(connectionString)
    container_client = blob_service_client.get_container_client("opengameart")

    with open('allblobs.txt') as fd:
        paths = [x.strip() for x in fd.readlines()]

    container_name = 'opengameart'
    for i, path in enumerate(paths):
        if i % 1000 == 0:
            print(i, i * 100 // len(paths))
        dest = '/mnt/data2/opengameart2/' + path
        if '__MACOSX' in path:
            continue
        if not os.path.exists(dest):
            print(path)
            try:
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=path)
                filedata = blob_client.download_blob().readall()

                dirname = os.path.split(dest)[0]
                if not os.path.exists(dirname):
                    os.makedirs(dirname)
                if not os.path.exists(dest):
                    with open(dest, 'wb') as dofd:
                        dofd.write(filedata)
            except:
                e = sys.exc_info()[0]
                print('Error on:', path, e, file=sys.stderr)
                time.sleep(1)

if __name__ == '__main__':
    step4()
