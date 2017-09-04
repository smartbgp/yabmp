YABMP
=====

|Python Version| |Version| |License| |Build Status| |Code Climate|

Overview
~~~~~~~~

`YABMP` is a receiver-side implementation of the `BMP` (BGP Monitoring Protocol) in the Python language. It serves as a reference for how to step through the messages and write their contents to files.

This implementation covers RFC 7854 BGP Monitoring Protocol version 3.

RFCs to read to help you understand the code better:

* RFC1863 - A BGP/IDRP Route Server alternative to a full mesh routing
* RFC1997 - BGP Communities Attribute
* RFC2042 - Registering New BGP Attribute Types
* RFC2858 - Multiprotocol Extensions for BGP-4
* RFC4271 - A Border Gateway Protocol 4 (BGP-4)
* RFC4893 - BGP Support for Four-octet AS Number Space
* Other BGP related RFCs.

Quick Start
~~~~~~~~~~~

.. code:: bash

Use `pip install yabmp` or install from source.

   $ virtualenv yabmp-virl
   $ source yabmp-virl/bin/activate
   $ git clone https://github.com/smartbgp/yabmp
   $ cd yabmp
   $ pip install -r requirements.txt
   $ cd bin
   $ python yabmpd -h


.. code:: bash

   $ python yabmpd &

Will starting bmpd server listen to port = 20000 and ip = 0.0.0.0

Support
~~~~~~~

Send email to xiaoquwl@gmail.com, or use GitHub issue system/pull request.


.. |License| image:: https://img.shields.io/hexpm/l/plug.svg
   :target: https://github.com/smartbgp/yabmp/blob/master/LICENSE
.. |Build Status| image:: https://travis-ci.org/smartbgp/yabmp.svg
   :target: https://travis-ci.org/smartbgp/yabmp
.. |Code Climate| image:: https://codeclimate.com/github/smartbgp/yabmp/badges/gpa.svg
   :target: https://codeclimate.com/github/smartbgp/yabmp
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/Django.svg
    :target: https://github.com/smartbgp/yabbmp
.. |Version| image:: https://img.shields.io/pypi/v/yabmp.svg?
   :target: http://badge.fury.io/py/yabmp