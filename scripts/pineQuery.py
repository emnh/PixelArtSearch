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

import urllib
from urllib.parse import urlparse
from urllib.parse import quote, unquote
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
from socket import timeout
import logging
#import httplib2

def downloadFile(url):
    try:
        assert url.startswith('http')
        response = urllib.request.urlopen(url, timeout=10).read()
        return response
    except (HTTPError, URLError) as error:
        logging.error('Data of %s not retrieved because %s\nURL: %s', name, error, url)
    except timeout:
        logging.error('socket timed out - URL %s', url)
    else:
        logging.info('Access successful.')

def main():
    'entry point'
    with open('../local.settings.json') as fd:
        settings = json.load(fd)
    apiKey = settings['Values']['PINECONE']

    db = {}
    with open('database.txt', 'r') as fd:
        lines = fd.readlines()
        for line in lines:
            stripped = line.strip()
            vid, path = stripped.split('\t')
            vid = int(vid)
            db[vid] = path

    reversedb = {}
    with open('reversedb.txt', 'r') as fd:
        lines = fd.readlines()
        for line in lines:
            stripped = line.strip()
            content, file = stripped.split(':', 1)
            file = file.replace('"https://opengameart.org/sites/default/', '')
            content = content.replace('/mnt/data2/opengameart2/', 'https://opengameart.org/')
            content = content.replace('.html', '/')
            reversedb[file.lower()] = content

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
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

        def do_POST(self):
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself
            logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n", str(self.path), str(self.headers), post_data.decode('utf-8'))

            #self._set_response()
            #self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))
            print('HELLO')

            #self._set_response()
            imsi = ''
            data = post_data.decode('utf-8').strip()
            print("Content-type", self.headers['Content-type'])
            count = 10
            if self.headers['Content-type'].lower() == 'application/x-www-form-urlencoded' and 'imsi=' in data:
                query = data #urlparse(self.path).query
                print('QUERY', query)
                query_components = dict(qc.split("=", 1) for qc in query.split("&"))
                imsi = query_components["imsi"]
                imsi = unquote(imsi)
                imsi = imsi.strip()
                ajax = False
            elif self.headers['Content-type'].lower() == 'application/json':
                body = json.loads(data)
                if 'imsi' in body:
                    imsi = body['imsi']
                if 'count' in body:
                    try:
                        count = int(body['count'])
                    except:
                        pass
                ajax = True
            if count < 0:
                count = 10
            elif count > 100:
                count = 100

            print('IMSI', imsi)
#             if not imsi and path.lower().endswith('.png') or path.lower().endswith('.jpg'):
#                 self.send_response(200)
#                 self.send_header('Content-type','image/'  + path.lower()[-3:])
#                 self.end_headers()
#                 dest = '/mnt/data2/opengameart2/' + path
#                 print('Writing image', dest)
#                 with open(dest, 'rb') as infd:
#                     self.wfile.write(infd.read())

            sys.stdout.flush()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            #if imsi != '' and imsi.lower().endswith('.png') or imsi.lower().endswith('.jpg') or imsi.lower().endswith('.jpeg'):
            #self.wfile.write('<h1>Search Results</h1>'.encode('utf-8'))

            def contentLink(url):
                url = re.sub(r'\.zip.*', '.zip', url)
                url = re.sub(r'\.rar.*', '.rar', url)
                url = unquote(url).lower()
                url = url.replace('https://emh.lart.no/opengameart2/extract/', '')
                if url in reversedb:
                    return reversedb[url]
                print("NO MATCH:", url)
                return 'https://opengameart.org/'

            if imsi != '' and imsi.startswith('http') and '.png' in imsi.lower() or '.jpg' in imsi.lower() or '.jpeg' in imsi.lower() or '.gif' in imsi.lower():
                noresults = True
                try:
                    imgdata = downloadFile(imsi)
                    file_imgdata = BytesIO(imgdata)
                    dt = Image.open(file_imgdata)
                    pimg = prepImage(dt)
                    features = feat_extractor.predict(pimg)
                    print("Features", features)
                    print(features.shape, features.dtype)

                    queries = features

                    results = conn.query(queries=queries, top_k=count).collect()
                    print(results)
                    for result in results[0].ids:
                        vid = int(result)
                        if not ajax:
                            link = '<link rel="stylesheet" href="../index.css"></link>'
                        else:
                            link = ''
                        head = '<html><head>' + link + '</head><body>'
                        self.wfile.write(head.encode('utf-8'))
                        if vid in db:
                            noresults = False
                            url = 'https://emh.lart.no/opengameart2/' + quote(db[vid][0:-len('.np')])
                            img = '<img class="searchresult" src="' + url + '"></img>\n'
                            cl = contentLink(url)
                            a = '<a href="' + cl + '">' + img + '</a>'
                            data = a.encode('utf-8')
                            self.wfile.write(data)
                            print(result, db[vid])
                        tail = '</body></html>'
                except:
                    self.wfile.write('<h1>Error: Something went wrong.</h1>'.encode('utf-8'))
                    return
                if noresults:
                    self.wfile.write('<h1>No results</h1>'.encode('utf-8'))
            elif imsi != '' and not 'http' in imsi:
                words = imsi.split(' ')
                words = [x.lower() for x in words]
                noresults = True
                results = []
                for path in db.values():
                    ok = True
                    for word in words:
                        if not word in path.lower():
                            ok = False
                    if ok:
                        results.append(path)
                        if len(results) >= count:
                            break
                for result in results:
                    noresults = False
                    url = 'https://emh.lart.no/opengameart2/' + quote(result[0:-len('.np')])
                    img = '<img class="searchresult" src="' + url + '"></img>\n'
                    cl = contentLink(url)
                    a = '<a href="' + cl + '">' + img + '</a>'
                    data = a.encode('utf-8')
                    self.wfile.write(data)
                if noresults:
                    self.wfile.write('<h1>No results</h1>'.encode('utf-8'))
            else:
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
