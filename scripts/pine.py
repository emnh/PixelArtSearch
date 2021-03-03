#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ft=python ts=4 sw=4 sts=4 et fenc=utf-8
# Original author: "Eivind Magnus Hvidevold" <hvidevold@gmail.com>
# License: GNU GPLv3 at http://www.gnu.org/licenses/gpl.html

'''
'''

import os
import sys
import re
import json
import numpy as np
import pinecone
import pinecone.graph
import pinecone.service
import pinecone.connector
import time
import multiprocessing
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__

class DBC(): pass
downloadBlobContext = DBC()

def main():
    'entry point'
    with open('../local.settings.json') as fd:
        settings = json.load(fd)
    connectionString = settings["Values"]["AzureWebJobsStorage"]
    apiKey = settings['Values']['PINECONE']

    pinecone.init(api_key=apiKey)

    loadData(connectionString)

def downloadBlob(args):
    vid, path = args
    container_name = downloadBlobContext.container_name
    blob_service_client = downloadBlobContext.blob_service_client
    container_client = downloadBlobContext.container_client
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=path)
        filedata = blob_client.download_blob().content_as_bytes()
        return (vid, path, filedata)
    except:
        e = sys.exc_info()[0]
        print('Error on:', path, e, file=sys.stderr)
        raise
        time.sleep(1)

def listFiles(vidStart, batchSize):
    batch = []
    vid = vidStart
    with open('allblobs.txt') as fd:
        for line in fd:
            path = line.strip()
            if '__MACOSX' in path:
                continue
            if path.endswith('.np'):
                dest = '/mnt/data2/opengameart2/' + path
                if os.path.exists(dest):
                    continue
                vid += 1
                batch.append([vid, path])
                if len(batch) >= batchSize:
                    yield batch
                    batch = []
    if len(batch) > 0:
        yield batch

def loadData(connectionString):
    batchSize = 10
    container_name = 'opengameart'
    blob_service_client = BlobServiceClient.from_connection_string(connectionString)
    container_client = blob_service_client.get_container_client("opengameart")

    downloadBlobContext.container_name = container_name
    downloadBlobContext.blob_service_client = blob_service_client
    downloadBlobContext.container_client = container_client

    conn = pinecone.connector.connect("opengameart-search")
    batch = []
    paths = []
    items = []
    pool = multiprocessing.Pool(batchSize)
    if not os.path.exists('database.txt'):
        vidStart = 0
    else:
        with open('database.txt') as fd:
            lines = fd.readlines()
            vidStart, lastPath = lines[-1].split('\t')
            vidStart = int(vidStart)
    for batch in listFiles(vidStart, batchSize):
        for vid, path, filedata in pool.map(downloadBlob, batch):
            try:
                if len(filedata) == 16384:
                    dest = '/mnt/data2/opengameart2/' + path
                    dname = os.path.split(dest)[0]
                    if not os.path.exists(dname):
                        os.makedirs(dname)
                    with open(dest, 'wb') as ofd:
                        ofd.write(filedata)
                    vector = np.frombuffer(filedata)
                    items.append((vid, vector))
                    paths.append((vid, path))
                    print(vid, path)
            except:
                e = sys.exc_info()[0]
                print('Error on:', path, e, file=sys.stderr)
                time.sleep(1)
                #raise
            if len(items) >= 100:
                with open('database.txt', 'a') as ofd:
                    for vid, path in paths:
                        ofd.write(str(vid) + '\t' + path + '\n')
                acks = conn.upsert(items=items).collect()
                print(acks)
                items = []
                paths = []

    if len(items) > 0:
        acks = conn.upsert(items=items).collect()
        print(acks)

def provision():
#     items = []
#     items.extend((f'class-a-{i}', vec) for i, vec in enumerate(np.random.randn(500, 1024) + 0.0))
#     items.extend((f'class-b-{i}', vec) for i, vec in enumerate(np.random.randn(500, 1024) + 1.0))
#     queries = np.random.randn(100, 1024) + 0.0 # the queries belong to class a
#     print(items[0][1].shape)

    graph = pinecone.graph.IndexGraph(engine_type='approximated', metric='cosine', shards=10, replicas=1, node_type=pinecone.utils.constants.NodeType.STANDARD, gateway_replicas=1)
    # you can do things like
    # # graph.add_read_preprocessor('my_item_transformer_image_uri')
    # # graph.add_write_preprocessor('my_query_transformer_image_uri')
    # # graph.add_postprocessor('my_postprocessor_image_uri')o

    pinecone.service.deploy(service_name="opengameart-search", graph=graph)

    conn = pinecone.connector.connect("opengameart-search")

    #acks = conn.upsert(items=items).collect()
    #results = conn.query(queries=queries).collect()
    #print(results[0])

if __name__ == '__main__':
    main()
