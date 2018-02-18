Usage
-----

Basic usage
===========

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

Complete example of timed stimulation
=====================================

This is a fully working script that ensures the execution of a program designed to deliver 10s of stimulation. The script assumes that program is numbered '100' on the Medoc system internally and configured for external control.

.. code-block:: python

    from pymedoc.devices import Pathway
    import time

    # Get settings from Medoc system
    ip = 'X.X.X.X.X'
    port = 20121

    # We're going to trigger a protocol that stimulates for 10s
    # Stimulation occurs at 46.5 deg but the system baseline is 32 deg
    # The fastest possible ramp up is 10 deg/s so we need to account for
    # ramp up and ramp down time before the trial ends for real
    stimulation_time = 10
    ramp_time = (46.5 - 32) / 10.
    total_time = stimulation_time + ramp_time

    # Establish initial connection test
    medoc = Pathway(ip,port,verbose=False)

    # Pause for a second
    time.sleep(1)

    # Issue the command to load the program
    print("Starting program")
    resp = medoc.program(100)

    # The system has a variable length "pre-test" phase before a trigger can be sent.
    # Any triggers sent during this time will be completely missed by the system.
    # More annoying is that the length of the "pre-test" phase is uknowable ahead of time
    # Here we use a convenient method built specifically for this situation
    # It repeatedly checks the system 'test_state' until its value is'RUNNING'
    # where it can reliably get a trigger
    # Print each poll attempt with the verbose flag 
    ready = medoc.poll_for_change('test_state','RUNNING',verbose=True)

    # Trigger the start of the stimulation
    print("Triggering")
    resp = medoc.trigger()

    # Wait the duration of stimulation
    time.sleep(total_time)

    # Send the stop signal
    print("Stopping")
    resp = medoc.stop()

    # Again check until the system has ACTUALLY stopped to do anything else
    ready = medoc.poll_for_change('test_state','IDLE',verbose=True)

    print("END")
