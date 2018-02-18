Usage
=====

To use this package, simply initialize the Pathway device and call its methods to interface with the Medoc system. pyMedoc automatically tries to establish a connection on initialization. Below are some example. See the API for a full list of commands.

.. code-block:: python

    from pymed.devices import Pathway
    # Obviously this is a fake IP
    my_pathway = Pathway(ip='10.10.10.10',port_number=9991)

    # Check status
    response = my_pathway.check_status()

    # Start protocol 18
    response = my_pathway.test_program(18)

    # Stop a running program
    response = my_path.stop()
