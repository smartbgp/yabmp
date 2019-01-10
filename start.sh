#!/bin/sh

exec bin/yabmpd --bind_port=${BMP_BIND_PORT} --log-file=/root/data/bmp/${BMP_BIND_PORT}/log/yabmp.log
               --message-write_dir=/root/data/bmp/${BMP_BIND_PORT}/msg