#!/usr/bin/env python
import logging
import sys
import os
from .cli import main

logging.basicConfig(stream=sys.stdout, level=os.environ.get('DEBUG_LEVEL') or logging.INFO)

main()
