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
        self.bgp_peer_dict = {}
        self.client_ip = None
        self.client_port = None

    def connectionMade(self):
        """
        TCP Conection made
        """
        self.client_ip = self.transport.getPeer().host
        self.client_port = self.transport.getPeer().port
        LOG.info(
            "BMP Client %s:%s connected.", self.client_ip, self.client_port)
        self.factory.handler.on_connection_made(
            self.client_ip, self.client_port)

    def connectionLost(self, reason):
        """
        TCP conection lost
        :param reason:
        """
        LOG.info(
            "BMP Client %s disconnected,Connection was closed cleanly: %s",
            self.transport.getPeer().host,
            reason.getErrorMessage()
        )
        self.client_ip = self.transport.getPeer().host
        self.client_port = self.transport.getPeer().port
        self.factory.handler.on_connection_lost(
            self.client_ip, self.client_port
        )

    def closeConnection(self):
        """Close the connection"""
        if self.transport.connected:
            self.transport.loseConnection()

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
        """
        """
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
                self.factory.handler.on_message_received(
                    self.client_ip, self.client_port, results, msg_type)
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
