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

    print(pinecone.service.ls())
    #for service in pinecone.service.ls():
    #    pinecone.service.stop(service)


if __name__ == '__main__':
    main()

