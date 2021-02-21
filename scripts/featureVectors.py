#!/usr/bin/env python3

# Preparation:
# conda create -n tensorflow-gpu tensorflow-gpu
# conda install -c conda-forge azure-storage-blob
# conda install -c anaconda pillow
# conda install -c anaconda cudatoolkit
# cd ~/.keras/models
# wget https://storage.googleapis.com/tensorflow/keras-applications/vgg16/vgg16_weights_tf_dim_ordering_tf_kernels.h5
# sudo apt install nvidia-cuda-dev
# 
# New instructions:
# https://medium.com/analytics-vidhya/install-tensorflow-gpu-2-4-0-with-cuda-11-0-and-cudnn-8-using-anaconda-8c6472c9653f
# conda create -n cudatoolkit cudatoolkit
# conda install -c conda-forge azure-storage-blob
# conda install -c anaconda pillow
# pip3 install tensorflow-gpu

import json
import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
import os

with open('../local.settings.json') as fd:
    settings = json.load(fd)
connectionString = settings["Values"]["AzureWebJobsStorage"]
#os.environ["AZURE_STORAGE_CONNECTION_STRING"] = connectionString

container_name = "opengameart"

def step1():
    try:
        print("Azure Blob Storage v" + __version__ + " - Python quickstart sample")

        # Quick start code goes here

        # Create the BlobServiceClient object which will be used to create a container client
        blob_service_client = BlobServiceClient.from_connection_string(connectionString)
        container_client = blob_service_client.get_container_client(container_name)

        print("\nListing blobs...")

        # List the blobs in the container
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob.name)
            properties = blob_client.get_blob_properties()
            #length = BlockBlobService.get_blob_properties(blob_service_client, container_name, blob.name).properties.content_length
            print(blob.name + '\t' + str(properties.size))

    except Exception as ex:
        print('Exception:')
        print(ex)

def step2():
    with open('allblobs.txt') as fd:
        files = [fname.strip() for fname in fd.readlines()]
        files = [fname for fname in files if fname.lower().endswith('.jpg') or fname.lower().endswith('.png')]

    from tensorflow.keras.applications.vgg16 import VGG16
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.applications.vgg16 import decode_predictions, preprocess_input
    from tensorflow.keras.models import Model
    from tensorflow.compiler import xla
    #from keras.applications.vgg16 import VGG16
    #from keras.preprocessing import image
    #from keras.applications.vgg16 import decode_predictions, preprocess_input
    #from keras.models import Model
    #from tensorflow.compiler import xla
    import numpy as np
    import time
    import os
    import sys
    import PIL
    import json
    import math
    import multiprocessing
    from glob import glob
    from PIL import Image
    from io import BytesIO

    model = VGG16(weights='imagenet', include_top=True)
    feat_extractor = Model(inputs=model.input, outputs=model.get_layer("fc2").output)

    def prepImage(img):
        x = np.array(img.resize((224, 224)).convert('RGB'))
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        return x

    logfd = open('log.txt', 'a')

    print("Azure Blob Storage v" + __version__ + " - Python quickstart sample")

    # Create the BlobServiceClient object which will be used to create a container client
    blob_service_client = BlobServiceClient.from_connection_string(connectionString)
    container_client = blob_service_client.get_container_client("opengameart")

    print("\nProcessing blobs...")

    # List the blobs in the container
    for fname in files:
        try:
            # Create a blob client using the local file name as the name for the blob
            print("Reading blob", fname)
            starts = []
            starts.append(time.time())
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=fname)
            imgdata = blob_client.download_blob().readall()

            print("Preparing image", fname)
            starts.append(time.time())
            file_imgdata = BytesIO(imgdata)
            dt = Image.open(file_imgdata)
            pimg = prepImage(dt)

            print("Computing feature vector", fname)
            starts.append(time.time())
            features = feat_extractor.predict(pimg)
            print("Features", features)

            print("Uploading feature vector", fname + ".np")
            starts.append(time.time())
            blob_writer = blob_service_client.get_blob_client(container=container_name, blob=fname + ".np")
            blob_writer.upload_blob(features.flatten().tobytes(), overwrite=True)
            
            end = time.time()
            print(["read", "prep", "feature", "upload"], [end - start for start in starts])

            print("Done with", fname)

            logfd.write(fname + '\n')

        except Exception as ex:
            print('Exception:')
            print(ex)
            time.sleep(10)

    logfd.close()

if __name__ == '__main__':
    step1()
