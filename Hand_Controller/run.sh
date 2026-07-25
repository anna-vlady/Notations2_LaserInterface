#!/bin/bash
export MEDIAPIPE_DISABLE_CLEARCUT_LOGGING=1
export GLOG_minloglevel=3
export TF_CPP_MIN_LOG_LEVEL=3

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"
source venv/bin/activate
python main.py
