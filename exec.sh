#!/bin/bash
python image_generator.py -f --count=30 -a --rate=10 & 
python qtui.py   &
python processor-gst.py -o gst_pipe 
