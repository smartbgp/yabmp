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

import abc
import logging

import six

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseHandler(object):
    """basic yabmp handler
    """

    def __init__(self):
        pass

    @abc.abstractmethod
    def init(self):
        """init some configuration
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def on_connection_made(self, peer_host, peer_port):
        """process for connection made
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def on_connection_lost(self, peer_host, peer_port):
        """process for connection lost
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def on_message_received(self, peer_host, peer_port, msg, msg_type, data_type, length):
        """process for message received
        """
        raise NotImplementedError()
