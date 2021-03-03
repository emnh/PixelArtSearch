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

class DBC(): pass
downloadBlobContext = DBC()

def main():
    'entry point'
    with open('../local.settings.json') as fd:
        settings = json.load(fd)
    connectionString = settings["Values"]["AzureWebJobsStorage"]
    apiKey = settings['Values']['PINECONE']

    pinecone.init(api_key=apiKey)
    conn = pinecone.connector.connect("opengameart-search")

    model = VGG16(weights='imagenet', include_top=True)
    feat_extractor = Model(inputs=model.input, outputs=model.get_layer("fc2").output)

    def prepImage(img):
        x = np.array(img.resize((224, 224)).convert('RGB'))
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        return x

    dt = Image.open(sys.argv[1])
    pimg = prepImage(dt)
    features = feat_extractor.predict(pimg)
    print("Features", features)
    print(features.shape, features.dtype)

    queries = features

    results = conn.query(queries=queries).collect()

    print(results)


if __name__ == '__main__':
    main()
