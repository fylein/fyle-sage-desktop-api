#!/bin/bash

# This script is used to run export P1 worker in Docker
python workers/worker.py --queue_name sage_desktop_export.p1
