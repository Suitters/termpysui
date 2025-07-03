=============================================================
tpysui - Pysui TUI application to manage PysuiConfigurations
=============================================================

ALPHA ALPHA ALPHA

A console TUI. Currently supports managing (create/edit)
PysuiConfig.json as well as Mysten SUI client.yaml.

Features
--------

* Create new or modify existing PysuiConfig.json file
* Modify existing Mysten Sui client.yaml
* Save existing PysuiConfig.json to new PysuiConfig.json file
* Add, modify or delete Groups, Profiles and Identities

Installing ``tpysui`` will also install ``pysui`` and ``pysui-fastcrypto``
which requires having Rust installed. If you do not have Rust and don't want
to, or can't, install Rust see install notes in pysui_.

.. _pysui: https://github.com/FrankC01/pysui/blob/main/README.md#pysui-sdk-install

Install
-------

#. Activate, or create and activate, a virtual environment
#. Install ``tpysui`` using environment install tools (e.g. pip, pipenv, etc.)
#. For pip :code:`pip install tpysui` from PyPi. See install notes in pysui_
#. Run :code:`tpysui` from command line

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
