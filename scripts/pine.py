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

def main():
    'entry point'
    with open('../local.settings.json') as fd:
        settings = json.load(fd)
    apiKey = settings['Values']['PINECONE']

    pinecone.init(api_key=apiKey)

    items = []
    items.extend((f'class-a-{i}', vec) for i, vec in enumerate(np.random.randn(500, 1024) + 0.0))
    items.extend((f'class-b-{i}', vec) for i, vec in enumerate(np.random.randn(500, 1024) + 1.0))
    queries = np.random.randn(100, 1024) + 0.0 # the queries belong to class a

    graph = pinecone.graph.IndexGraph()
    # you can do things like
    # # graph.add_read_preprocessor('my_item_transformer_image_uri')
    # # graph.add_write_preprocessor('my_query_transformer_image_uri')
    # # graph.add_postprocessor('my_postprocessor_image_uri')o

    pinecone.service.deploy(service_name="hello-pinecone", graph=graph)

    conn = pinecone.connector.connect("hello-pinecone")

    acks = conn.upsert(items=items).collect()

    results = conn.query(queries=queries).collect()
    print(results[0])

if __name__ == '__main__':
    main()

