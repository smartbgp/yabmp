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

from yabmp import config
from yabmp import version
from yabmp import log
from yabmp.core.factory import BMPFactory
from yabmp.channel.factory import PikaFactory

from twisted.internet import reactor
from oslo_config import cfg

log.early_init_log(logging.DEBUG)

CONF = cfg.CONF

CONF.register_cli_opts(config.bmp_options, group='bmp')

LOG = logging.getLogger(__name__)


def prepare_service(args=None):
    try:
        CONF(args=args, project='yabmp', version=version,
             default_config_files=['/etc/yabmp/yabmp.ini'])
    except cfg.ConfigFilesNotFoundError:
        CONF(args=args, project='yabmp', version=version)

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
    # start bmp server and rabbitmq connection
    try:
        standalone = os.environ.get("YABMP_STANDALONE", False)
        if not standalone:
            # rabbitmq factory
            LOG.info('Try to connect to rabbitmq server')
            url = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/%2F')
            rabbit_mq_factory = PikaFactory(url=url, routing_key='%s:%s' % (CONF.bmp.bind_host, CONF.bmp.bind_port))
            rabbit_mq_factory.connect()
        reactor.listenTCP(
            CONF.bmp.bind_port,
            BMPFactory(msg_path=CONF.bmp.write_dir, rabbit_mq_factory=rabbit_mq_factory),
            interface=CONF.bmp.bind_host)
        LOG.info("Starting bmpd server listen to port = %s and ip = %s" % (
            CONF.bmp.bind_port, CONF.bmp.bind_host))
        reactor.run()
    except Exception as e:
        LOG.error(e)


def main():
    prepare_service()
