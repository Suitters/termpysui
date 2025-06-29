=============================================================
tpysui - Pysui TUI application to manage PysuiConfigurations
=============================================================

ALPHA ALPHA ALPHA

A console TUI. Currently supports managing (create/edit)
PysuiConfig.toml, which enable profile management for pysui
GraphQL and gRPC URL, keys, account addresses and aliases.

Features
--------

* Create new or modify existing PysuiConfig.json file
* Save existing PysuiConfig.json to new PysuiConfig.json file
* Add, modify or delete Groups, Profiles and Identities

Installing ``tpysui`` will also install ``pysui`` and ``pysui-fastcrypto``
which requires having Rust installed. See install notes in pysui_.

.. _pysui: https://github.com/FrankC01/pysui/blob/main/README.md#pysui-sdk-install

Install
-------

#. Activate, or create and activate, a virtual environment
#. Install ``tpysui`` using environment install tools (e.g. pip, pipenv, etc.)
#. For pip :code:`pip install tpysui` from PyPi

Clone
-----

``tpusui`` uses pipenv, if you have not installed, do so.

#. Clone the github repo
#. ``cd tpysui``
#. ``pipenv shell``
#. If needed manually install ``pysui-fastcrypto``. See install notes in pysui_
#. ``pipenv install``
#. ``python -m src.tpysui.tpysui``

Documentation
-------------
See Documentation_ for operations help

.. _Documentation: https://github.com/suitters/tpysui/blob/main/docs/tpysui.rst
