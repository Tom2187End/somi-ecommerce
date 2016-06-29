Getting Started with Shuup Development
======================================

.. note::

   If you are planning on using Shuup for developing your own shop,
   read the :doc:`other Getting Started guide <getting_started>` instead.

Installation for Shuup Development
----------------------------------

To start developing Shuup, you'll need a Git checkout of Shuup and a
Github fork of Shuup for creating pull requests.  Github pull requests
are used to get your changes into Shuup Base.

 1. If you haven't done so already, create a fork of Shuup in Github by
    clicking the "Fork" button at https://github.com/shuupio/shuup and
    clone the fork to your computer as usual. See `Github Help about
    forking repos <https://help.github.com/articles/fork-a-repo/>`__ for
    details.

 2. Setup a virtualenv and activate it.  You may use the traditional
    ``virtualenv`` command, or the newer ``python -m venv`` if you're
    using Python 3.  See `Virtualenv User Guide
    <https://virtualenv.pypa.io/en/latest/userguide.html>`__, if you
    don't know virtualenv already.  For example, following commands
    create and activate a virtualenv in Linux:

    .. code-block:: shell

       virtualenv shuup-venv
       . shuup-venv/bin/activate

 3. Finally, you'll need to install Shuup in the activated virtualenv in
    development mode.  To do that, run the following commands in the
    root of the checkout (within the activated virtualenv):

    .. code-block:: shell

       pip install -e .
       python setup.py build_resources

Workbench, the built-in test project
------------------------------------

The Workbench project in the repository is a self-contained Django
project set up to use an SQLite database. It is used by the test suite
and is also useful for development on its own.

Practically the only difference to a normal Django project is that instead
of ``python manage.py``, one uses ``python -m shuup_workbench``.

To get started with Workbench, invoke the following in the Shuup working copy
root.

.. code-block:: shell

   # Migrate database.
   python -m shuup_workbench migrate

   # Import some basic data.
   python -m shuup_workbench shuup_populate_mock --with-superuser=admin

   # Run the Django development server (on port 8000 by default).
   python -m shuup_workbench runserver

You can use the credentials ``admin``/``admin``, that is username ``admin``
and password ``admin`` to log in as a superuser on http://127.0.0.1:8000/ .

Building resources
------------------

Shuup uses JavaScript and CSS resources that are compiled using various
Node.js packages.  These resources are compiled automatically by
``setup.py`` when installing Shuup with pip, but if you make changes to
the source files (e.g. under ``shuup/admin/static_src``), the resources
have to be rebuilt.

This can be done with

.. code-block:: shell

   python setup.py build_resources

The command also accepts couple arguments, see its help for more details:

.. code-block:: shell

   python setup.py build_resources --help

Running tests
-------------

To run tests in the active virtualenv:

.. code-block:: shell

   py.test -v shuup_tests
   # Or with coverage
   py.test -vvv --cov shuup --cov-report html shuup_tests

To run tests for all supported Python versions run:

.. code-block:: shell

   pip install tox  # To install tox, needed just once
   tox

Collecting translatable messages
--------------------------------

To update the PO catalog files which contain translatable (and
translated) messages, issue ``shuup_makemessages`` management command in
the ``shuup`` directory:

.. code-block:: shell

   cd shuup && python -m shuup_workbench shuup_makemessages

Docstring coverage
------------------

The DocCov script is included for calculating some documentation coverage metrics.

.. code-block:: shell

   python _misc/doccov.py shuup/core -o doccov.html
