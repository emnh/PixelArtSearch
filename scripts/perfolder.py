#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ft=python ts=4 sw=4 sts=4 et fenc=utf-8
# Original author: "Eivind Magnus Hvidevold" <hvidevold@gmail.com>
# License: GNU GPLv3 at http://www.gnu.org/licenses/gpl.html

'''
'''

import os
import sys
import re

def main():
    'entry point'
    perfolder = {}
    for line2 in sys.stdin.readlines():
        line = line2.strip()
        if 'extract/' in line:
            folders = line.split('/')
            if len(folders) < 3:
                print('WARN', line)
                pass
            else:
                folder = folders[2]
                if folder in perfolder:
                    perfolder[folder].append(line)
                else:
                    perfolder[folder] = [line]
    for key, value in sorted(perfolder.items(), key=lambda x: len(x[1])):
        print(key, len(value))

if __name__ == '__main__':
    main()

