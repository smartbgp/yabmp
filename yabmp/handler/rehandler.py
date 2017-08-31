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
import time
import logging
from yabmp.handler import BaseHandler
from oslo_config import cfg
from yabmp.channel.publisher import Publisher

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class ReHandler(BaseHandler):
    """rewrite handler to cast message of peer up and down
    """
    def __init__(self):
        super(ReHandler, self).__init__()
        self.bgp_peer_dict = dict()

    def init(self):
        pass

    def on_connection_made(self, peer_host, peer_port):
        """process for connection made
        """
        print('on_connection')

    def on_connection_lost(self, peer_host, peer_port):
        """process for connection lost
        """
        print('on_lost')

    def on_message_received(self, peer_host, peer_port, msg, msg_type):
        """process for message received
        """
        if msg_type in [4, 5, 6]:
            return
        LOG.info('-------------------msg:%s-------------------', msg)
        peer_ip = msg[0]['addr']
        if peer_ip not in self.bgp_peer_dict:
            self.bgp_peer_dict[peer_ip] = {}
            policy_pub = Publisher(url=cfg.CONF.rabbit_mq.rabbit_url)
            msg_body = {
                'type': msg_type,
                'data': msg
            }
            policy_pub.declare_queue(name=peer_host)
            policy_pub.bind_queue(_exchange='test', _queue=peer_host)
            policy_pub.publish_message(_exchange='test', _routing_key=peer_host, _body=msg_body)
            LOG.info('pub')
        if msg_type == 2:
            LOG.info('2')
            policy_pub.publish_message(_exchange='test', _routing_key=peer_host, _body=msg_body)
            LOG.info('pub2')
        elif msg_type == 3:
            LOG.info('3')
            policy_pub.publish_message(_exchange='test', _routing_key=peer_host, _body=msg_body)
            LOG.info('pub3')
            
        # if msg_type == 1:  # statistic message
        #     msg_list = [time.time(), self.bgp_peer_dict[peer_ip]['msg_seq'], 129, msg[1], (0, 0)]
        #     self.bgp_peer_dict[peer_ip]['file'].write(str(msg_list) + '\n')
        #     self.bgp_peer_dict[peer_ip]['msg_seq'] += 1
        #     self.bgp_peer_dict[peer_ip]['file'].flush()
        # elif msg_type == 2:  # peer down message
        #     msg_list = [time.time(), self.bgp_peer_dict[peer_ip]['msg_seq'], 3, msg[1], (0, 0)]
        #     self.bgp_peer_dict[peer_ip]['file'].write(str(msg_list) + '\n')
        #     self.bgp_peer_dict[peer_ip]['msg_seq'] += 1
        #     self.bgp_peer_dict[peer_ip]['file'].flush()
        # else:
        #     return
