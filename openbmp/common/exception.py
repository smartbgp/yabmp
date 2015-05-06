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

"""
BMP base exception handling.
"""

_FATAL_EXCEPTION_FORMAT_ERRORS = False


class BMPException(Exception):
    """Base BMP Exception.
    """
    message = "An unknown exception occurred."

    def __init__(self, **kwargs):
        try:
            super(BMPException, self).__init__(self.message % kwargs)
            self.msg = self.message % kwargs
        except Exception:
            if _FATAL_EXCEPTION_FORMAT_ERRORS:
                raise
            else:
                # at least get the core message out if something happened
                super(BMPException, self).__init__(self.message)

    def __unicode__(self):
        return unicode(self.msg)


class BMPVersionError(BMPException):
    message = 'Bad BMP version, local version:%(local_version)s, remote version:%(remote_version)s'


class UnknownMessageTypeError(BMPException):
    message = 'unknown message type, type=%(type)s'


class BadMessageHeaderLength(BMPException):
    message = 'Bad message header length'


class UnknownPeerTypeValue(BMPException):
    message = 'unknown peer type value, value=%(peer_type)s'


class UnknownPeerFlagValue(BMPException):
    message = 'unknown peer flag value, value=%(peer_flags)s'
