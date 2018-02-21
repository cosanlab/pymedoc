from __future__ import division

"""
Main Pathway Device Class
=========================
"""

__all__ = ['Pathway']
__author__ = ["Cosan Lab"]
__license__ = "MIT"
import socket
import time
import numpy as np
from collections import OrderedDict
import six

class Pathway(object):

    """
    Pathway is a class to communicate with the Medoc Pathway thermal stimulation machine.

    Args:
        ip (str): device ip address
        port_number (int): port the device is listening on
        timeout (float): seconds until connection timeouts; default 5s
        verbose (bool): flag whether to print responses; default True
        buffer_size (int): size of connection buffer; default 1024

    """

    def __init__(self, ip, port_number,timeout = 5.,verbose=True, buffer_size = 1024):

        assert isinstance(ip,six.string_types), "IP address must be a string."
        assert isinstance(port_number,six.integer_types), "Port must be an integer"

        self.ip = ip
        self.port_number = port_number
        self.BUFFER_SIZE = buffer_size
        self.timeout = timeout
        self.verbose = verbose
        self.socket = None
        self.test_states = {
        0: 'IDLE',
        1: 'RUNNING',
        2: 'PAUSED',
        3: 'READY'
        }
        self.state_codes = {
        0: 'IDLE',
        1: 'READY',
        2: 'TEST'
        }
        self.command_codes = {
        0: 'STATUS',
        1: 'TEST_PROGRAM',
        2: 'START',
        3: 'PAUSE',
        4: 'TRIGGER',
        5: 'STOP',
        6: 'ABORT',
        7: 'YES',
        8: 'NO'
        }
        self.response_codes = {
        0: 'RESULT_OK',
        1: 'RESULT_ILLEGAL_ARG',
        2: 'RESULT_ILLEGAL_STATE',
        3: 'RESULT_ILLEGAL_TEST_STATE',
        4096: 'RESULT_DEVICE_COMM_ERROR',
        8192: 'RESULT_SAFETY_WARNING',
        16384: 'RESULT_SAFETY_ERROR'
        }
        self.segmentation_points = OrderedDict({
        'LENGTH_OFFSET': (0,4),
        'TIMESTAMP_OFFSET': (4,8),
        'COMMAND_OFFSET': 8,
        'SYSTEM_STATE_OFFSET':9,
        'TEST_STATE_OFFSET': 10,
        'RESULT_OFFSET': (11,13),
        'TEST_TIME_OFFSET': (13,17),
        'ERROR_MESSAGE_OFFSET': 17
        })
        try:
            _ = self.call('STATUS',verbose=False)
            print('Connection to Pathway successful')
        except:
            raise IOError('Cannot establish connection, check IP and port number is correct and the host computer is on.')

    def _create_connection(self):
        """Create and return new socket connection"""
        socket.setdefaulttimeout(self.timeout)
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((self.ip,self.port_number))
        return s

    def call(self, command, protocol=None, reuse_socket=False, verbose = False):
        """
        Send command to device.

        Args:
            command (str/int): command name or command_id number to send to device
            protocol (str/int): protocol number on device to issue command to (only needed for command TEST_PROGRAM)
            reuse_socket (bool): try to reuse the last created socket connection; *NOT CURRENTLY FUNCTIONAL*
            verbose (bool): whether to print out the device callback

        Returns:
            response (dict): response from Medoc system
        """

        if reuse_socket:
            raise NotImplementedError("Reusing sockets does not currently work.")
            if self.socket:
                s = self.socket
            else:
                raise ValueError("No previous sockets exist")
        else:
            s = self._create_connection()
            self.socket = s

        if isinstance(command,str):
            command = self.command_codes.keys()[self.command_codes.values().index(command)]

        if command ==1 and protocol is None:
            raise ValueError('TEST_PROGRAM command requires a protocol number')

        MESSAGE = self._format_command(command, protocol)
        nbytes = s.send(MESSAGE)
        time.sleep(0.5)
        data = s.recv(self.BUFFER_SIZE)
        response = self._format_response(data,nbytes)
        if not response:
            return self.call(command,protocol,verbose=verbose)
        if verbose:
            print_flag = verbose
        else:
            print_flag = self.verbose
        if print_flag:
            print(response)
        return response

    def _format_command(self, command, protocol):
        """
        Format calls to device.

        Args:
            command (str/int): command name or command_id number to send to device
            protocol (int): protocol number on device to issue command to (only needed for command TEST_PROGRAM)

        Returns:
            message: formatted message to be sent

        """
        bin32 = lambda x : ''.join(reversed( [str((x >> i) & 1) for i in range(32)] ))

        curtime = bin32(int(time.time()))
        timelist = []
        for i in range(1,5):
            timelist.append(int(curtime[(i-1)*8:i*8],2))
        timelist.reverse()

        cmd = [command]

        protocollist = []
        if command==1 and protocol:
            protocol = bin32(protocol)
            for i in range(1,5):
                protocollist.append(int(protocol[(i-1)*8:i*8],2))
            protocollist.reverse()

        MESSAGE =  timelist + cmd + protocollist # first should be time

        sizelist = []
        size = bin32(len(MESSAGE))
        for i in range(1,5):
            sizelist.append(int(size[(i-1)*8:i*8],2))
        sizelist.reverse()

        MESSAGE = np.array(sizelist + MESSAGE)
        MESSAGE = np.getbuffer(MESSAGE.astype(np.uint8),size=len(MESSAGE))
        return MESSAGE

    def _format_response(self, data, nbytes):
        """
        Format responses from device.
        Note: Test time is the time since machine was turned on.

        Args:
            data: data bytes from devices
            nbytes: length of bytes from devices

        Returns:
            response (dict): dictionary of response data

        """
        data_int = [int(elem.encode('hex'),16) for elem in data]

        response_dict = {}
        try:
            response_dict['response_length'] = self._decode(data_int,'LENGTH_OFFSET')
            response_dict['time_stamp'] = time.ctime(self._decode(data_int,'TIMESTAMP_OFFSET'))
            response_dict['command_id'] = self.command_codes[data_int[self.segmentation_points['COMMAND_OFFSET']]]
            response_dict['pathway_state'] = self.state_codes[data_int[self.segmentation_points['SYSTEM_STATE_OFFSET']]]
            response_dict['test_state'] = self.test_states[data_int[self.segmentation_points['TEST_STATE_OFFSET']]]
            response_dict['response'] =  self.response_codes[self._decode(data_int,'RESULT_OFFSET')]
            response_dict['test_time_stamp'] = self._decode_test_time(data_int)

            if response_dict['response_length'] > 13:
                #Covert to uint8 and native?
                response_dict['error_message'] = data[self.segmentation_points['ERROR_MESSAGE_OFFSET']]
        except Exception as e:
            print("ERROR FORMATTING RESPONSE")
            print("data_int: ", data_int)
            print("data: ", data)
            print("nbyes: ", nbytes)
        return response_dict

    def _decode(self,data_int,whichtime):
        """
        Helper function to decode response.
        """
        bin8 = lambda x : ''.join(reversed( [str((x >> i) & 1) for i in range(8)] ))
        dat_int = data_int[self.segmentation_points[whichtime][0]:self.segmentation_points[whichtime][1]]
        dat_bin = [bin8(dat_int[i])for i in range(0,self.segmentation_points[whichtime][1]-self.segmentation_points[whichtime][0])]
        dat_bin.reverse()
        dat_bin = "".join(dat_bin)
        return int(dat_bin,2)

    def _decode_test_time(self,data_int):
        """
        Helper function to decode response time.
        """
        test_time = self._decode(data_int,'TEST_TIME_OFFSET')

        hours = test_time//3600000
        mins = (test_time-(hours*3600000))//60000
        secs = (test_time-(hours*3600000)-(mins*60000))//1000
        msecs = test_time-(hours*3600000)-(mins*60000)-(secs*1000)
        test_time = '%.2d:%.2d:%.2d.%3d' %(hours,mins,secs,msecs)
        return test_time

    def poll_for_change(self,to_watch,desired_value,poll_interval=.5,poll_max=-1,verbose=False,server_lag=1.,reuse_socket=False):
        """
        Poll system for a value change. Useful for waiting until the Medoc system has transitioned to a specific state in order to issue another command, but the transition length is unknowable.

        Args:
            to_watch (str): the response field we should be monitoring; most often 'test_state' or 'pathway_state'
            desired_value (str): the desired value of the field to wait on, i.e. keep checking until response_field has this value
            poll_interval (float): how often to poll; default .5s
            poll_max (int): upper limit on polling attempts; default -1 (unlimited)
            verbose (bool): print poll attempt number and current state
            server_lag (float): sometimes if the socket connection is pinged too quickly after a value change the subsequent command after this method is called can get missed. This adds an additional layer of timing delay before returning from this method to prevent this; default 1s
            reuse_socket (bool): try to reuse the last created socket connection; *NOT CURRENTLY FUNCTIONAL*

        Returns:
            status (bool): whether desired_value was achieved

        """
        val = ''
        count = 1
        while val != desired_value:
            if verbose:
                print("Poll: {}".format(str(count)))
            resp = self.call('STATUS',reuse_socket=False)
            if resp:
                val = resp[to_watch]
            else:
                val = 'RESPONSE_FORMAT_ERROR'
            if verbose:
                print("Current value: {}".format(val))
            time.sleep(poll_interval)
            count += 1
            if poll_max > 0 and count > poll_max:
                print("Polling limit exceeded")
                return False
        time.sleep(server_lag)
        return True

    #Convenience wrappers around call method

    def status(self):
        """ Convenience method."""
        return self.call('STATUS')

    def program(self, protocol):
        """ Convenience method."""
        return self.call('TEST_PROGRAM',protocol=protocol)

    def start(self):
        """ Convenience method."""
        return self.call('START')

    def pause(self):
        """ Convenience method."""
        return self.call('PAUSE')

    def trigger(self):
        """ Convenience method."""
        return self.call('TRIGGER')

    def stop(self):
        """ Convenience method."""
        return self.call('STOP')

    def abort(self):
        """ Convenience method."""
        return self.call('ABORT')

    def yes(self):
        """ Convenience method."""
        return self.call('YES')

    def no(self):
        """ Convenience method."""
        return self.call('NO')
