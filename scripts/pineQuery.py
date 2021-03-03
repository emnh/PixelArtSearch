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

from urllib.parse import urlparse
from urllib.parse import quote
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import decode_predictions, preprocess_input
from tensorflow.keras.models import Model
from tensorflow.compiler import xla
import numpy as np
import PIL
import math
import multiprocessing
from glob import glob
from PIL import Image
from io import BytesIO
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import httplib2

class DBC(): pass
downloadBlobContext = DBC()

def downloadFile(URL=None):
    h = httplib2.Http(".cache")
    resp, content = h.request(URL, "GET")
    return content

def main():
    'entry point'
    with open('../local.settings.json') as fd:
        settings = json.load(fd)
    connectionString = settings["Values"]["AzureWebJobsStorage"]
    apiKey = settings['Values']['PINECONE']

    db = {}
    with open('database.txt', 'r') as fd:
        lines = fd.readlines()
        for line in lines:
            stripped = line.strip()
            vid, path = stripped.split('\t')
            vid = int(vid)
            db[vid] = path

    pinecone.init(api_key=apiKey)
    conn = pinecone.connector.connect("opengameart-search2")

    model = VGG16(weights='imagenet', include_top=True)
    feat_extractor = Model(inputs=model.input, outputs=model.get_layer("fc2").output)

    def prepImage(img):
        x = np.array(img.resize((224, 224)).convert('RGB'))
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        return x

    class S(BaseHTTPRequestHandler):
        def _set_response(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        def do_GET(self):
            logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
            #self._set_response()
            imsi = ''
            path = str(self.path)
            if '=' in self.path and 'imsi' in self.path:
                query = urlparse(self.path).query
                query_components = dict(qc.split("=") for qc in query.split("&"))
                imsi = query_components["imsi"]

            print('IMSI', imsi)
#             if not imsi and path.lower().endswith('.png') or path.lower().endswith('.jpg'):
#                 self.send_response(200)
#                 self.send_header('Content-type','image/'  + path.lower()[-3:])
#                 self.end_headers()
#                 dest = '/mnt/data2/opengameart2/' + path
#                 print('Writing image', dest)
#                 with open(dest, 'rb') as infd:
#                     self.wfile.write(infd.read())

            if imsi and imsi.lower().endswith('.png') or imsi.lower().endswith('.jpg'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                imgdata = downloadFile(imsi)
                file_imgdata = BytesIO(imgdata)
                dt = Image.open(file_imgdata)
                pimg = prepImage(dt)
                features = feat_extractor.predict(pimg)
                print("Features", features)
                print(features.shape, features.dtype)

                queries = features

                results = conn.query(queries=queries).collect()
                print(results)
                for result in results[0].ids:
                    vid = int(result)
                    if vid in db:
                        url = 'http://emh.lart.no/opengameart2/' + quote(db[vid][0:-len('.np')]) + '\n'
                        img = '<img src="' + url + '"></img>'
                        data = img.encode('ascii')
                        self.wfile.write(data)
                        print(result, db[vid])
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write('Nothing'.encode('ascii'))
                self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))


        def do_POST(self):
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself
            logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                    str(self.path), str(self.headers), post_data.decode('utf-8'))

            self._set_response()
            self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

    def run(server_class=HTTPServer, handler_class=S, port=7899):
        logging.basicConfig(level=logging.INFO)
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        logging.info('Starting httpd...\n')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
        logging.info('Stopping httpd...\n')

    return run

if __name__ == '__main__':
    from sys import argv

    run = main()
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
