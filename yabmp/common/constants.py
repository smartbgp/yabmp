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

"""BMP constants"""

# The length of the fixed header part of a BMP message.
HEADER_LEN = 6

# Version of the protocol, as specified in the header.
VERSION = 3

# Message types.

MSG_TYPE_ROUTE_MONITORING = 0
MSG_TYPE_STATISTICS_REPORT = 1
MSG_TYPE_PEER_DOWN_NOTIFICATION = 2
MSG_TYPE_PEER_UP_NOTIFICATION = 3
MSG_TYPE_INITIATION = 4
MSG_TYPE_TERMINATION = 5
MSG_TYPE_ROUTE_MIRRORING = 6
MSG_TYPE_STR = {
    MSG_TYPE_ROUTE_MONITORING: "Route Monitoring",
    MSG_TYPE_STATISTICS_REPORT: "Statistics Report",
    MSG_TYPE_PEER_DOWN_NOTIFICATION: "Peer Down Notification",
    MSG_TYPE_PEER_UP_NOTIFICATION: "Peer Up Notification",
    MSG_TYPE_INITIATION: "Initiation Message",
    MSG_TYPE_TERMINATION: "Termination Message",
    MSG_TYPE_ROUTE_MIRRORING: "Route Mirroring"
}

# Peer types.
PEER_TYPE_GLOBAL = 0
PEER_TYPE_RD_INSTANCE = 1
PEER_TYPE_LOCAL = 2
PEER_TYPE_STR = {PEER_TYPE_GLOBAL: "Global",
                 PEER_TYPE_RD_INSTANCE: "RD Instance",
                 PEER_TYPE_LOCAL: "Local Instance"}

PEER_FLAGS = ['V', 'L', 'A']

BMP_STAT_TYPE = {
    0: 'Number of prefixes rejected by inbound policy',
    1: 'Number of (known) duplicate prefix advertisements',
    2: 'Number of (known) duplicate withdraws',
    3: 'Number of updates invalidated due to CLUSTER_LIST loop',
    4: 'Number of updates invalidated due to AS_PATH loop',
    5: 'Number of updates invalidated due to ORIGINATOR_ID',
    6: 'Number of updates invalidated due to AS_CONFED loop',
    7: 'Number of routes in Adj-RIBs-In',
    8: 'Number of routes in Loc-RIB',
    9: 'Number of routes in per-AFI/SAFI Adj-RIB-In',
    10: 'Number of routes in per-AFI/SAFI Loc-RIB',
    11: 'Number of updates subjected to treat-as-withdraw',
    12: 'Number of prefixes subjected to treat-as-withdraw',
    13: 'Number of duplicate update messages received',
    32767: 'SRTT',
    32768: 'RTTO',
    32769: 'RTV',
    32770: 'KRTT',
    32771: 'minRTT',
    32772: 'maxRTT',
    32773: 'ACK hold',
    32774: 'Datagrams'
}

INIT_MSG_INFOR_TYPE = {
    0: 'String',
    1: 'sysDescr',
    2: 'sysName'
}

TERMI_MSG_INFOR_TYPE = {
    0: 'String',
    1: 'Reason'
}

TERMI_MSG_INFOR_TYPE_REASON_TYPE = {
    0: 'Session administratively closed',
    1: 'Unspecified reason',
    2: 'Out of resources',
    3: 'Redundant connection',
    4: 'Permanently administratively closed'
}

ROUTE_MIRRORING_TLV_TYPE = {
    0: 'BGP Message TLV',
    1: 'Information TLV'
}

ROUTE_MIRRORING_INFORMATION_TYPE_CODE = {
    0: 'Errored PDU',
    1: 'Message Lost'

}
