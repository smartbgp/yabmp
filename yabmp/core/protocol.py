# Copyright 2015 Cisco Systems, Inc.
# All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
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
import sys
import time
import logging
import struct
import traceback
from twisted.internet import protocol

from yabmp.common import constants as bmp_cons
from yabmp.common import exception as excp
from yabmp.message.bmp import BMPMessage

LOG = logging.getLogger()


class BMP(protocol.Protocol):
    """
    BGP Monitoring Protocol
    """

    def __init__(self):

        LOG.info('Building a new BGP protocol instance')
        self.receive_buffer = ''
        self.message = BMPMessage()
        self.msg_file_path = None
        self.bgp_peer_dict = {}
        self.client_info = None
        self.channel = None

    def connectionMade(self):
        """
        TCP Conection made
        """
        LOG.info("BMP Client %s:%s connected." % (self.transport.getPeer().host, self.transport.getPeer().port))
        self.client_info = '%s:%s' % (self.transport.getPeer().host, self.transport.getPeer().port)
        file_path = os.path.join(self.factory.msg_path, self.transport.getPeer().host)
        if not os.path.exists(file_path):
            try:
                os.makedirs(file_path)
                LOG.info('create directory: %s' % file_path)
            except Exception as e:
                LOG.error(e)
                error_str = traceback.format_exc()
                LOG.debug(error_str)
                sys.exit()

        self.msg_file_path = file_path

    def connectionLost(self, reason):
        """
        TCP conection lost
        :param reason:
        """
        LOG.info("BMP Client %s disconnected,Connection was closed cleanly." % self.transport.getPeer().host)
        self.client_info = '%s:%s' % (self.transport.getPeer().host, self.transport.getPeer().port)

    def closeConnection(self):

        """Close the connection"""
        if self.transport.connected:
            self.transport.loseConnection()

    @staticmethod
    def init_statistic():

        statistic_dict = {}
        for msg_type in bmp_cons.MSG_TYPE_STR:
            statistic_dict[bmp_cons.MSG_TYPE_STR[msg_type]] = 0

        return statistic_dict

    def dataReceived(self, data):
        """ Data has been received.
        :param data:
        """

        self.receive_buffer += data
        try:
            while self.parse_buffer():
                pass
        except Exception as e:
            LOG.error(e)
            error_str = traceback.format_exc()
            LOG.debug(error_str)
            self.closeConnection()

    def parse_buffer(self):

        buf = self.receive_buffer
        if len(buf) < bmp_cons.HEADER_LEN:
            # Every BMP message is at least 44 octets. Maybe the rest
            # hasn't arrived yet.
            return False

        # Parse the header
        # +-+-+-+-+-+-+-+-+
        # |   Version     |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                       Message Length                          |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |   Msg. Type   |
        # +---------------+
        version, length, msg_type = struct.unpack('!BIB', buf[:6])

        if version != bmp_cons.VERSION:
            # close the connection
            raise excp.BMPVersionError(local_version=bmp_cons.VERSION, remote_version=version)
        if msg_type not in bmp_cons.MSG_TYPE_STR.keys():
            raise excp.UnknownMessageTypeError(type=msg_type)
        if length > len(buf):
            # the hold message does not comming yet.
            return False
        msg_value = buf[6:length]
        self.message.msg_type = msg_type
        LOG.debug('Received BMP message, type=%s' % msg_type)
        self.message.raw_body = msg_value
        LOG.debug('Decoding message...')
        try:
            results = self.message.consume()
            if results:
                # write msg file
                self.write_msg_file(msg_type, results)
            else:
                LOG.error('decoding message failed.')

        except Exception as e:
            LOG.error(e)
            error_str = traceback.format_exc()
            LOG.debug(error_str)
        LOG.debug('Finished decoding.')
        self.message = BMPMessage()
        LOG.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
        self.receive_buffer = self.receive_buffer[length:]
        return True

    def write_msg_file(self, msg_type, msg):
        """
        write msg to file
        """
        if msg_type in [4, 5, 6]:
            return
        peer_ip = msg[0]['addr']
        if peer_ip not in self.bgp_peer_dict:
            self.bgp_peer_dict[peer_ip] = {}
            peer_msg_path = os.path.join(self.msg_file_path, peer_ip)
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
            if self.channel:
                self.channel.send_message(exchange='', message={'type': 7, 'msg_type': 2, 'peer_ip': peer_ip})

        elif msg_type == 3:  # peer up message
            msg_list = [time.time(), self.bgp_peer_dict[peer_ip]['msg_seq'], 1, msg[1]['received_open_msg'], (0, 0)]
            self.bgp_peer_dict[peer_ip]['file'].write(str(msg_list) + '\n')
            self.bgp_peer_dict[peer_ip]['msg_seq'] += 1
            self.bgp_peer_dict[peer_ip]['file'].flush()
            if self.channel:
                self.channel.send_message(exchange='', message={'type': 7, 'msg_type': 3, 'peer_ip': peer_ip})

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
