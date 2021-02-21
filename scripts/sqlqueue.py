#!/usr/bin/env python
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
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
from azure.storage.queue import (
    QueueClient,
    BinaryBase64EncodePolicy,
    BinaryBase64DecodePolicy
)

def main():
    'entry point'


def step3():
    with open('../local.settings.json') as fd:
        settings = json.load(fd)
    connectionString = settings["Values"]["AzureWebJobsStorage"]
    #os.environ["AZURE_STORAGE_CONNECTION_STRING"] = connectionString

    container_name = "opengameart"

    with open('putToSqlQueue.txt') as fd:
        files = [fname.strip() for fname in fd.readlines()]
        #files = [fname for fname in files if fname.lower().endswith('.jpg') or fname.lower().endswith('.png')]
    files = files[282000:]

    # Retrieve the connection string from an environment
    # variable named AZURE_STORAGE_CONNECTION_STRING
    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    # Create a unique name for the queue
    #q_name = "queue-" + str(uuid.uuid4())
    q_name = 'sqlqueue'

    # Instantiate a QueueClient object which will
    # be used to create and manipulate the queue
    #queue_client = QueueClient.from_connection_string(connectionString, q_name)

    # Setup Base64 encoding and decoding functions
    base64_queue_client = QueueClient.from_connection_string(
        conn_str=connectionString, queue_name=q_name,
        message_encode_policy = BinaryBase64EncodePolicy(),
        message_decode_policy = BinaryBase64DecodePolicy()
    )

    for i, message in enumerate(files):
        if i % 1000 == 0:
            print(i)
        base64_queue_client.send_message(message.encode('ascii'))

if __name__ == '__main__':
    step3()
