# Copyright 2015-2017 Cisco Systems, Inc.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import logging
import sys
import time

from oslo_config import cfg

from yabmp.handler import BaseHandler

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

MSG_PROCESS_OPTS = [
    cfg.StrOpt(
        'write_dir',
        default=os.path.join(os.environ.get('HOME', './'), 'data/bmp/'),
        help='The BMP messages storage path'),
    cfg.IntOpt(
        'write_msg_max_size',
        default=500,
        help='The Max size of one BMP message file, the unit is MB')
]


class DefaultHandler(BaseHandler):
    """default handler
    """
    def __init__(self):
        super(DefaultHandler, self).__init__()
        CONF.register_cli_opts(MSG_PROCESS_OPTS, group='message')
        self.bgp_peer_dict = dict()

    def init(self):
        if not os.path.exists(CONF.message.write_dir):
            try:
                os.makedirs(CONF.message.write_dir)
                LOG.info('Create message output path: %s', CONF.message.write_dir)
            except Exception as e:
                LOG.error(e, exc_info=True)
                sys.exit()

    def on_connection_made(self, peer_host, peer_port):
        """process for connection made
        """
        file_path = os.path.join(CONF.message.write_dir, peer_host)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
            LOG.info('Create directory: %s for peer %s', file_path, peer_host)

    def on_connection_lost(self, peer_host, peer_port):
        """process for connection lost
        """
        pass

    def on_message_received(self, peer_host, peer_port, msg, msg_type):
        """process for message received
        """
        if msg_type in [4, 5, 6]:
            return
        peer_ip = msg[0]['addr']
        if peer_ip not in self.bgp_peer_dict:
            self.bgp_peer_dict[peer_ip] = {}
            peer_msg_path = os.path.join(
                os.path.join(CONF.message.write_dir, peer_host), peer_ip)
            if not os.path.exists(peer_msg_path):
                # this peer first come out
                # create a peer path and open the first message file
                os.makedirs(peer_msg_path)
                LOG.info('Create directory for peer: %s' % peer_msg_path)
                msg_file_name = os.path.join(peer_msg_path, '%s.msg' % time.time())
                self.bgp_peer_dict[peer_ip]['msg_seq'] = 1
            else:
                # this peer is not first come out
                # find the latest message file and get the last message sequence number
                file_list = os.listdir(peer_msg_path)
                file_list.sort()
                msg_file_name = os.path.join(peer_msg_path, file_list[-1])
                self.bgp_peer_dict[peer_ip]['msg_seq'] = self.get_last_seq(msg_file_name)
            self.bgp_peer_dict[peer_ip]['file'] = open(msg_file_name, 'a')
        if msg_type == 0:  # route monitoring message
            if msg[0]['flags']['L']:
                # pos-policy RIB
                msg_list = [time.time(), self.bgp_peer_dict[peer_ip]['msg_seq'], 130, msg[1], (1, 1)]
            else:
                # pre-policy RIB
                msg_list = [time.time(), self.bgp_peer_dict[peer_ip]['msg_seq'], msg[1][0], msg[1][1], (1, 1)]
            self.bgp_peer_dict[peer_ip]['file'].write(str(msg_list) + '\n')
            self.bgp_peer_dict[peer_ip]['msg_seq'] += 1
            self.bgp_peer_dict[peer_ip]['file'].flush()
        elif msg_type == 1:  # statistic message
            msg_list = [time.time(), self.bgp_peer_dict[peer_ip]['msg_seq'], 129, msg[1], (0, 0)]
            self.bgp_peer_dict[peer_ip]['file'].write(str(msg_list) + '\n')
            self.bgp_peer_dict[peer_ip]['msg_seq'] += 1
            self.bgp_peer_dict[peer_ip]['file'].flush()
        elif msg_type == 2:  # peer down message
            msg_list = [time.time(), self.bgp_peer_dict[peer_ip]['msg_seq'], 3, msg[1], (0, 0)]
            self.bgp_peer_dict[peer_ip]['file'].write(str(msg_list) + '\n')
            self.bgp_peer_dict[peer_ip]['msg_seq'] += 1
            self.bgp_peer_dict[peer_ip]['file'].flush()

        elif msg_type == 3:  # peer up message
            msg_list = [time.time(), self.bgp_peer_dict[peer_ip]['msg_seq'], 1, msg[1]['received_open_msg'], (0, 0)]
            self.bgp_peer_dict[peer_ip]['file'].write(str(msg_list) + '\n')
            self.bgp_peer_dict[peer_ip]['msg_seq'] += 1
            self.bgp_peer_dict[peer_ip]['file'].flush()

    @staticmethod
    def get_last_seq(file_name):

        """
        Get the last sequence number in the log file.
        """

        lines_2find = 1
        f = open(file_name)
        f.seek(0, 2)  # go to the end of the file
        bytes_in_file = f.tell()
        lines_found, total_bytes_scanned = 0, 0
        while (lines_2find + 1 > lines_found and
                bytes_in_file > total_bytes_scanned):
            byte_block = min(1024, bytes_in_file - total_bytes_scanned)
            f.seek(-(byte_block + total_bytes_scanned), 2)
            total_bytes_scanned += byte_block
            lines_found += f.read(1024).count('\n')
        f.seek(-total_bytes_scanned, 2)
        line_list = list(f.readlines())
        last_line = line_list[-lines_2find:][0]
        try:
            last_line = eval(last_line)
            return last_line[1] + 1
        except Exception as e:
            LOG.info(e)
            return 1
