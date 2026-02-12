#!/bin/bash

# This script is used to run import worker in Docker
python workers/worker.py --queue_name sage_desktop_import
