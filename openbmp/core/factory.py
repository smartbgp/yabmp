# Copyright 2015 Cisco Systems, Inc.
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

""" BMP Factory"""

import logging

from twisted.internet import protocol

from openbmp.core.protocol import BMP


LOG = logging.getLogger()


class BMPFactory(protocol.Factory):
    """Base factory for creating BMP protocol instances."""

    protocol = BMP

    def __init__(self, msg_path=None):
        LOG.info('Initial BMP Factory!')
        self.msg_path = msg_path

    def buildProtocol(self, addr):
        """Builds a BMPProtocol instance.
        """
        return protocol.Factory.buildProtocol(self, addr)
