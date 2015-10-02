#!/usr/bin/env python
import logging
import sys
import os

logging.basicConfig(stream=sys.stdout, level=os.environ.get('DEBUG_LEVEL') or logging.INFO)

from .cli import main

main()
