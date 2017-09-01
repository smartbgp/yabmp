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
        self.puber = None

    def init(self):
        self.puber = Publisher(url=cfg.CONF.rabbit_mq.rabbit_url)

    def on_connection_made(self, peer_host, peer_port):
        """process for connection made
        """
        try:
            self.puber.declare_queue(name='yabmp_%s' % peer_host)
            self.puber.declare_exchange(_exchange='yabmp_%s' % peer_host, _type='direct')
            self.puber.bind_queue(_exchange='yabmp_%s' % peer_host, _queue='yabmp_%s' % peer_host)
            msg_body = {
                "type": 0,
                "data": {
                    "time": time.time(),
                    "client_host": peer_host,
                    "client_port": peer_port
                }
            }
            self.puber.publish_message(_exchange='yabmp_%s' % peer_host, _routing_key='yabmp_%s' % peer_host, _body=msg_body)
            LOG.info('connection made')
        except Exception as e:
            LOG.info(e)

    def on_connection_lost(self, peer_host, peer_port):
        """process for connection lost
        """
        try:
            self.puber.declare_queue(name=peer_host)
            self.puber.declare_exchange(_exchange='yabmp_%s' % peer_host, _type='direct')
            self.puber.bind_queue(_exchange='yabmp_%s' % peer_host, _queue='yabmp_%s' % peer_host)
            msg_body = {
                "type": 1,
                "data": {
                    "time": time.time(),
                    "client_host": peer_host,
                    "client_port": peer_port
                }
            }
            self.puber.publish_message(_exchange='yabmp_%s' % peer_host, _routing_key='yabmp_%s' % peer_host, _body=msg_body)
            LOG.info('connection lost')
        except Exception as e:
            LOG.info(e)

    def on_message_received(self, peer_host, peer_port, msg, msg_type):
        """process for message received
        """
        if msg_type in [0, 1, 4, 5, 6]:
            return
        elif msg_type in [2, 3]:
            peer_ip = msg[0]['addr']
            LOG.info('peer_ip')
            LOG.info(peer_ip)
            msg_body = {
                "type": msg_type,
                "data": {
                    "time": time.time(),
                    "client_ip": peer_host,
                    "client_port": peer_port,
                    "bgp_peer_ip": peer_ip
                }
            }
            self.puber.publish_message(_exchange='yabmp_%s' % peer_host, _routing_key='yabmp_%s' % peer_host, _body=msg_body)
        else:
            return
