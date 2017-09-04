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

import logging

from yabmp import config
from yabmp import version
from yabmp import log
from yabmp.core.factory import BMPFactory
from yabmp.handler.default import DefaultHandler

from twisted.internet import reactor
from oslo_config import cfg

log.early_init_log(logging.DEBUG)

CONF = cfg.CONF

CONF.register_cli_opts(config.bmp_options)

LOG = logging.getLogger(__name__)


def prepare_service(args=None, handler=None):
    """prepare the twisted service

    :param hander: handler object
    """
    if not handler:
        handler = DefaultHandler()
    try:
        CONF(args=args, project='yabmp', version=version,
             default_config_files=['/etc/yabmp/yabmp.ini'])
    except cfg.ConfigFilesNotFoundError:
        CONF(args=args, project='yabmp', version=version)

    log.init_log()
    LOG.info('Log (Re)opened.')
    LOG.info("Configuration:")

    cfg.CONF.log_opt_values(LOG, logging.INFO)

    handler.init()
    # start bmp server
    try:
        reactor.listenTCP(
            CONF.bind_port,
            BMPFactory(handler=handler),
            interface=CONF.bind_host)
        LOG.info(
            "Starting bmpd server listen to port = %s and ip = %s",
            CONF.bind_port, CONF.bind_host)
        reactor.run()
    except Exception as e:
        LOG.error(e)


def main():
    prepare_service(args=None, handler=None)
