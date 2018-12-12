#!/bin/sh

exec bin/yabmpd --message-write_dir=${bmp_message_write_dir} --bind_port=${bmp_bind_port}