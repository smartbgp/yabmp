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
import os
import sys

from openbmp import version
from openbmp import config
from openbmp.core.factory import BMPFactory
from openbmp.common import log

log.early_init_log(logging.DEBUG)

from twisted.internet import reactor
from oslo.config import cfg

CONF = cfg.CONF

CONF.register_cli_opts(config.bmp_options, group='bmp')

LOG = logging.getLogger(__name__)


def prepare_service(args=None):
    try:
        CONF(args=args, project='openbmp', version=version,
             default_config_files=['/etc/openbmp/openbmp.ini'])
    except cfg.ConfigFilesNotFoundError:
        CONF(args=args, project='openbmp', version=version)

    log.init_log()
    LOG.info('Log (Re)opened.')
    LOG.info("Configuration:")
    cfg.CONF.log_opt_values(LOG, logging.INFO)

    # check BMP message output path
    if not os.path.exists(CONF.bmp.write_dir):
        try:
            os.makedirs(CONF.bmp.write_dir)
            LOG.info('Create message output path: %s' % CONF.bmp.write_dir)
        except Exception as e:
            LOG.error(e, exc_info=True)
            sys.exit()
    # start bmp server
    try:
        reactor.listenTCP(
            CONF.bmp.bind_port, BMPFactory(msg_path=CONF.bmp.write_dir), interface=CONF.bmp.bind_host)
        LOG.info("Starting bmpd server listen to port = %s and ip = %s" % (
            CONF.bmp.bind_port, CONF.bmp.bind_host))
        reactor.run()
    except Exception as e:
        LOG.error(e)


def main():
    prepare_service()
