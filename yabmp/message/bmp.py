# Copyright 2015 Cisco Systems, Inc.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import struct
import binascii
import logging
import traceback
import itertools

import netaddr
from bitstring import BitArray

from yabgp.message.notification import Notification
from yabgp.message.update import Update
from yabgp.message.route_refresh import RouteRefresh
from yabgp.message.open import Open
from yabgp.common import constants as bgp_cons

from yabmp.common import constants as bmp_cons
from yabmp.common import exception as excp

LOG = logging.getLogger()


class BMPMessage(object):
    """
    BMP message class.
    definition of BMP message and methons used to decode message.
    """

    def __init__(self):

        self.version = None
        self.msg_type = None
        self.raw_body = None
        self.msg_body = None

    @staticmethod
    def parse_per_peer_header(raw_peer_header):
        """
        decode per-peer header.
        every bmp message has this header, and the header length is 42 bytes.
        :param raw_peer_header: hex value of the header
        :return:
        """
        # 0 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |   Peer Type   | Peer Flags   |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |      Peer Distinguisher (present based on peer type)          |
        # |                                                               |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                Peer Address (16 bytes)                        |
        # ~                                                               ~
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                          Peer AS                              |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                         Peer BGP ID                           |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                      Timestamp (seconds)                      |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                    Timestamp (microseconds)                   |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        per_header_dict = {
            'type': None,
            'flags': None,
            'dist': None,
            'addr': None,
            'as': None,
            'bgpID': None,
            'time': None
        }
        LOG.debug('decode per-peer header')
        per_header_dict['type'] = struct.unpack('!B', raw_peer_header[0:1])[0]
        # Peer Type = 0: Global Instance Peer
        # Peer Type = 1: RD Instance Peer
        # Peer Type = 2: Local Instance Peer
        if per_header_dict['type'] not in [0, 1, 2]:
            raise excp.UnknownPeerTypeValue(peer_type=per_header_dict['type'])
        LOG.debug('peer type: %s ' % per_header_dict['type'])

        # Peer Flags
        peer_flags_value = binascii.b2a_hex(raw_peer_header[1:2])
        hex_rep = hex(int(peer_flags_value, 16))
        bit_array = BitArray(hex_rep)
        valid_flags = [''.join(item)+'00000' for item in itertools.product('01', repeat=3)]
        valid_flags.append('0000')
        if bit_array.bin in valid_flags:
            flags = dict(zip(bmp_cons.PEER_FLAGS, bit_array.bin))
            per_header_dict['flags'] = flags
            LOG.debug('Per Peer header flags %s' % flags)
        else:
            raise excp.UnknownPeerFlagValue(peer_flags=peer_flags_value)
        LOG.debug('peer flag: %s ' % per_header_dict['flags'])
        if per_header_dict['type'] in [1, 2]:
            per_header_dict['dist'] = int(binascii.b2a_hex(raw_peer_header[2:10]), 16)

        ip_value = int(binascii.b2a_hex(raw_peer_header[10:26]), 16)
        if int(per_header_dict['flags']['V']):
            per_header_dict['addr'] = str(netaddr.IPAddress(ip_value, version=6))
        else:
            per_header_dict['addr'] = str(netaddr.IPAddress(ip_value, version=4))

        per_header_dict['as'] = int(binascii.b2a_hex(raw_peer_header[26:30]), 16)
        LOG.debug('peer as: %s' % per_header_dict['as'])
        per_header_dict['bgpID'] = str(netaddr.IPAddress(int(binascii.b2a_hex(raw_peer_header[30:34]), 16)))
        LOG.debug('peer bgp id: %s' % per_header_dict['bgpID'])
        per_header_dict['time'] = (int(binascii.b2a_hex(raw_peer_header[34:38]), 16),
                                   int(binascii.b2a_hex(raw_peer_header[38:42]), 16))
        LOG.debug('timestamp: %s.%s' % (per_header_dict['time'][0], per_header_dict['time'][1]))
        return per_header_dict

    @staticmethod
    def parse_route_monitoring_msg(msg):
        """
            Route Monitoring messages are used for initial synchronization of
        ADJ-RIBs-In. They are also used for ongoing monitoring of received
        advertisements and withdraws.
        Following the common BMP header and per-peer header is a BGP Update
        PDU.
        :param msg:
        :return:
        """
        LOG.debug('decode route monitoring message')
        bgp_msg_type = struct.unpack('!B', msg[18])[0]
        LOG.debug('bgp message type=%s' % bgp_msg_type)
        msg = msg[bgp_cons.HDR_LEN:]
        if bgp_msg_type == 2:
            # decode update message
            results = Update().parse(None, msg, asn4=True)
            if results['sub_error']:
                LOG.error('error: decode update message error!, error code: %s' % results['sub_error'])
                LOG.error('Raw data: %s' % repr(results['hex']))
                return None
            return_result = {
                'attr': results['attr'],
                'nlri': results['nlri'],
                'withdraw': results['withdraw']}
            LOG.debug('bgp update message: %s' % return_result)
            return bgp_msg_type, return_result
        elif bgp_msg_type == 5:
            bgp_route_refresh_msg = RouteRefresh().parse(msg=msg)
            LOG.debug('bgp route refresh message: afi=%s,res=%s,safi=%s' % (bgp_route_refresh_msg[0],
                                                                            bgp_route_refresh_msg[1],
                                                                            bgp_route_refresh_msg[2]))
            return bgp_msg_type, {'afi': bgp_route_refresh_msg[0],
                                  'sub_type': bgp_route_refresh_msg[1],
                                  'safi': bgp_route_refresh_msg[2]}

    @staticmethod
    def parse_route_mirroring_msg(msg):
        """
            Route Mirroring messages are used for verbatim duplication of
        messages as received. Following the common BMP header and per-peer
        header is a set of TLVs that contain information about a message
        or set of messages.
        :param msg:
        :return:
        """
        LOG.debug('decode route mirroring message')

        msg_dict = {}
        open_l = []
        update = []
        notification = []
        route_refresh = []
        while msg:
            mirror_type, length = struct.unpack('!HH', msg[0:4])
            mirror_value = msg[4: 4 + length]
            msg = msg[4 + length:]
            if mirror_type == 0:
                # BGP message type
                bgp_msg_type = struct.unpack('!B', mirror_value[18])[0]
                LOG.debug('bgp message type=%s' % bgp_msg_type)
                bgp_msg_body = mirror_value[bgp_cons.HDR_LEN:]
                if bgp_msg_type == 2:
                    # Update message
                    bgp_update_msg = Update().parse(None, bgp_msg_body, asn4=True)
                    if bgp_update_msg['sub_error']:
                        LOG.error('error: decode update message error!, error code: %s' % bgp_update_msg['sub_error'])
                        LOG.error('Raw data: %s' % repr(bgp_update_msg['hex']))
                    else:
                        update.append(bgp_update_msg)
                elif bgp_msg_type == 5:
                    # Route Refresh message
                    bgp_route_refresh_msg = RouteRefresh().parse(msg=bgp_msg_body)
                    LOG.debug('bgp route refresh message: afi=%s,res=%s,safi=%s' % (bgp_route_refresh_msg[0],
                                                                                    bgp_route_refresh_msg[1],
                                                                                    bgp_route_refresh_msg[2]))
                    route_refresh.append(bgp_route_refresh_msg)
                elif bgp_msg_type == 1:
                    # Open message
                    open_msg = Open().parse(bgp_msg_body)
                    open_l.append(open_msg)
                elif bgp_msg_type == 3:
                    # Notification message
                    notification_msg = Notification().parse(bgp_msg_body)
                    notification.append(notification_msg)
            elif mirror_type == 1:
                # Information type.
                # Amount of this TLV is not specified but we can assume
                # only one per mirroring message is present.
                info_code_type = struct.unpack('!H', mirror_value)[0]
                msg_dict['1'] = info_code_type
            else:
                msg_dict[mirror_type] = binascii.unhexlify(binascii.hexlify(mirror_value))
                LOG.info('unknow mirroring type, type = %s' % mirror_type)

        msg_dict['0'] = {
                        'update': update,
                        'route_refresh': route_refresh,
                        'open': open_l,
                        'notification': notification
                        }
        return msg_dict

    @staticmethod
    def parse_statistic_report_msg(msg):
        """
        These messages contain information that could be used by the
        monitoring station to observe interesting events that occur on the
        router.
        :return:
        """
        # 0 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                         Stats Count                           |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # Each counter is encoded as follows,
        # 0 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |           Stat Type           |            Stat Len           |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                           Stat Data                           |
        # ~                                                               ~
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        LOG.info('decode statistic report message')
        count_num = int(binascii.b2a_hex(msg[0:4]), 16)
        count_dict = {}
        msg = msg[4:]
        while count_num:
            stat_type, stat_len = struct.unpack('!HH', msg[0:4])
            stat_data = msg[4:4+stat_len]
            msg = msg[4+stat_len:]
            stat_value = int(binascii.b2a_hex(stat_data), 16)
            count_dict[stat_type] = stat_value
            if stat_type not in bmp_cons.BMP_STAT_TYPE:
                LOG.warning('unknown statistic report type, type=%s' % stat_type)
            else:
                LOG.info('stat_type=%s, stat_value=%s' % (bmp_cons.BMP_STAT_TYPE[stat_type], stat_value))
            count_num -= 1
        return count_dict

    @staticmethod
    def parse_peer_down_notification(msg):
        """
        This message is used to indicate that a peering session was terminated.
        :param msg:
        :return:
        """
        # 0 1 2 3 4 5 6 7 8
        # +-+-+-+-+-+-+-+-+
        # |     Reason    | 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |             Data (present if Reason = 1, 2 or 3)              |
        # ~                                                               ~
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        LOG.info('decode peer down notification')
        reason = int(binascii.b2a_hex(msg[0]), 16)
        LOG.info('reason: %s' % reason)
        data = msg[1:]

        if reason == 1:
            LOG.info('Reason : 1 The local system closed the session. Following the '
                     'Reason is a BGP PDU containing a BGP NOTIFICATION message that'
                     'would have been sent to the peer')
            Notification().parse(message=data)
        elif reason == 2:
            LOG.info('Reason :2 The local system closed the session. No notification'
                     'message was sent. Following the reason code is a two-byte field'
                     'containing the code corresponding to the FSM Event which caused'
                     'the system to close the session (see Section 8.1 of [RFC4271]).'
                     'Two bytes both set to zero are used to indicate that no relevant'
                     'Event code is defined')
        elif reason == 3:
            LOG.info('Reason : 3 The remote system closed the session with a notification'
                     'message. Following the Reason is a BGP PDU containing the BGP'
                     'NOTIFICATION message as received from the peer.')
        elif reason == 4:
            LOG.info('Reason : 4 The remote system closed the session without a notification message')
        else:
            LOG.waring('unknown peer down notification reason')
        return reason

    @staticmethod
    def parse_peer_up_notification(msg, peer_flag):
        """
        The Peer Up message is used to indicate that a peering session has
        come up (i.e., has transitioned into ESTABLISHED state). Following
        the common BMP header and per-peer header is the following:
        :param msg:
        :param peer_flag: see parse_per_peer_header
        :return:
        """
        # 0 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                 Local Address (16 bytes)                      |
        # ~                                                               ~
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |          Local Port           |           Remote Port         |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                    Sent OPEN Message                         #|
        # ~                                                               ~
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                  Received OPEN Message                        |
        # ~                                                               ~
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        LOG.info('decode peer up notification')
        ip_value = int(binascii.b2a_hex(msg[0:16]), 16)
        if int(peer_flag['V']):
            # ipv6 address
            ip_address = str(netaddr.IPAddress(ip_value, version=6))
        else:
            ip_address = str(netaddr.IPAddress(ip_value, version=4))
        LOG.info('local address: %s' % ip_address)
        local_port = int(binascii.b2a_hex(msg[16:18]), 16)
        LOG.info('local port: %s' % local_port)
        remote_port = int(binascii.b2a_hex(msg[18:20]), 16)
        LOG.info('remote port: %s' % remote_port)
        # decode sent and received open message
        open_msg_data = msg[20:]
        length = struct.unpack('!H', open_msg_data[16:18])[0]
        sent_open_msg = Open().parse(open_msg_data[bgp_cons.HDR_LEN: length])
        open_msg_data = open_msg_data[length:]
        received_open_msg = Open().parse(open_msg_data[bgp_cons.HDR_LEN:])
        LOG.info('sent open: %s' % sent_open_msg)
        LOG.info('received open: %s' % received_open_msg)
        return {
            'local_address': ip_address,
            'local_port': local_port,
            'remote_port': remote_port,
            'sent_open_msg': sent_open_msg,
            'received_open_msg': received_open_msg
        }

    @staticmethod
    def parse_initiation_msg(msg):
        """
            The initiation message provides a means for the monitored router to
        inform the monitoring station of its vendor, software version, and so
        on. An initiation message MUST be sent as the first message after
        the TCP session comes up. An initiation message MAY be sent at any
        point thereafter, if warranted by a change on the monitored router.
            The initiation message consists of the common BMP header followed by
        two or more TLVs containing information about the monitored router,
        as follows:
        :return:
        """
        # 0 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |      Information Type         |        Information Length     |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                   Information (variable)                      |
        # ~                                                               ~
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        LOG.info('decode initiation message')
        msg_dict = {}
        while msg:
            info_type, length = struct.unpack('!HH', msg[0:4])
            info_value = msg[4: 4 + length]
            msg = msg[4 + length:]
            if info_type in bmp_cons.INIT_MSG_INFOR_TYPE:
                msg_dict[bmp_cons.INIT_MSG_INFOR_TYPE[info_type]] = binascii.unhexlify(binascii.hexlify(info_value))
            else:
                msg_dict[info_type] = binascii.unhexlify(binascii.hexlify(info_value))
                LOG.info('unknow information type, type = %s' % info_type)
        LOG.info('initiation message = %s' % msg_dict)
        return msg_dict

    @staticmethod
    def parse_termination_msg(msg):
        """
            The termination message provides a way for a monitored router to
        indicate why it is terminating a session. Although use of this
        message is RECOMMENDED, a monitoring station must always be prepared
        for the session to terminate with no message. Once the router has
        sent a termination message, it MUST close the TCP session without
        sending any further messages. Likewise, the monitoring station MUST
        close the TCP session after receiving a termination message.
        The termination message consists of the common BMP header followed by
        one or more TLVs containing information about the reason for the
        termination, as follows:
        :return:
        """
        # 0 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8 1 2 3 4 5 6 7 8
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |        Information Type       |       Information Length      |
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        # |                    Information (variable)                    #|
        # ~                                                               ~
        # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        LOG.info('decode termination message')
        msg_dict = {}
        while msg:
            info_type, length = struct.unpack('!HH', msg[0:4])
            info_value = msg[4: 4 + length]
            msg = msg[4 + length:]
            if info_type in bmp_cons.TERMI_MSG_INFOR_TYPE:
                msg_dict[bmp_cons.TERMI_MSG_INFOR_TYPE[info_type]] = binascii.unhexlify(binascii.hexlify(info_value))
            else:
                msg_dict[info_type] = binascii.unhexlify(binascii.hexlify(info_value))
                LOG.info('unknow information type, type = %s' % info_type)
        LOG.info('termination message = %s' % msg_dict)
        return msg_dict

    def consume(self):

        if self.msg_type in [0, 1, 2, 3, 6]:
            try:
                per_peer_header = self.parse_per_peer_header(self.raw_body[0:42])
                self.msg_body = self.raw_body[42:]
                if self.msg_type == 0:
                    return per_peer_header, self.parse_route_monitoring_msg(self.msg_body)
                elif self.msg_type == 1:
                    return per_peer_header, self.parse_statistic_report_msg(self.msg_body)
                elif self.msg_type == 2:
                    return per_peer_header, self.parse_peer_down_notification(self.msg_body)
                elif self.msg_type == 3:
                    return per_peer_header, self.parse_peer_up_notification(self.msg_body, per_peer_header['flags'])
                elif self.msg_type == 6:
                    return per_peer_header, self.parse_route_mirroring_msg(self.msg_body)
            except Exception as e:
                LOG.error(e)
                error_str = traceback.format_exc()
                LOG.debug(error_str)
                # can not decode this BMP message
                return None

        elif self.msg_type == 4:
            return None, self.parse_initiation_msg(self.raw_body)
        elif self.msg_type == 5:
            return None, self.parse_termination_msg(self.raw_body)
