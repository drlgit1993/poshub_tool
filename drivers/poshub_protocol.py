#_*_ coding:UTF-8 _*_

# !/usr/bin/python
# Python:   3.6.5
# Platform: Windows
# Author:   drl 
# History:  2021-03-15 Ver:1.0 [drl] Initialization

import time
import struct
import serial
import libscrc
import logging
import serial.tools.list_ports
from PyQt5.QtCore import QObject
from ui.poshub import Ui_poshub_tool

BIN_ERR_TIMEOUT = B"\x06"
BIN_ERR_EXCEPTION = B"\xFF"
FRAME_TAIL = b'\xcc\xcc'
FRAME_HEADER = b'U'

def catch_prococol_exception( origin_func ):
    def wrapper( self , *args , **kwargs ):
        try:
            return origin_func( self ,*args , **kwargs )
        except BaseException as err:
            logging.error( str( err ) )
            return BIN_ERR_EXCEPTION
    return wrapper

class poshub_Protocol(Ui_poshub_tool, object ):
    def __init__( self ):
        self.__ser = None
        self.__isopen = False
        self.__stopbits = { "1":serial.STOPBITS_ONE,
                            "1.5":serial.STOPBITS_ONE_POINT_FIVE,
                            "2":serial.STOPBITS_TWO }
        self.__parity = { "None":serial.PARITY_NONE,"ODD":serial.PARITY_ODD,"EVEN":serial.PARITY_EVEN}

    def isopen(self):
        return self.__isopen

    def connect( self, port, baudrate=115200, bytesize=8, parity='None', stopbits='1' ):
        self.ser = serial.serial_for_url( port, do_not_open=True )
        self.ser.port=port
        self.ser.baudrate = baudrate
        self.ser.bytesize = bytesize
        self.ser.parity = self.__parity.get( parity , "None" )
        self.ser.stopbits = self.__stopbits.get( stopbits , "1" )

        try:
            self.ser.open( )
        except BaseException as err:
            #logging.error( str( err ) ) 
            return False , "could not open port {}".format( port )

        self.__isopen = True
        return True , ""

    def close( self ):
        if ( self.__isopen ) and ( self.ser.isOpen() ) :
            self.ser.flushInput()
            self.ser.flushOutput()
            self.ser.close()
            self.__isopen = False


    def write( self , data:bytes ):
        self.ser.write( data )

    def read(self , count = 1 ):
        try:
            return self.ser.read( self.ser.in_waiting or count )
        except serial.SerialException as err:
            logging.error( str( err ) )
            return b''

    def frame_check(self,data,respond):
        header = int.from_bytes(FRAME_HEADER,byteorder='big',signed=False)
        #print(data)
        for index in range(len(data)):
            if data[index] == header :
                #print(index)
                if(data[index:index+6] ==respond ):
                    #print(data[index:index+6])
                    size = struct.unpack('>H' , data[index+6:index+8])[0]
                    #print(size)
                    tail= struct.unpack('>H' , data[index+10+size:index+12+size])[0]
                    #print(tail)
                    n = int.from_bytes(FRAME_TAIL,byteorder='big',signed=False)
                    #print(n)
                    if (tail == n) and ( libscrc.modbus( data[index:index+10+size] ) == 0):
                        print(data[index:index+12+size])
                        return data[index:index+12+size]

        return BIN_ERR_TIMEOUT

                
    @catch_prococol_exception
    def writeWaitAnswer( self , data ,err,type,code , order, timeout = 10 ):
        self.ser.flushInput()
        self.ser.write( data )
        
        loop = 0
        answer = b''
        respond = b"\x55"+err+type+code +order

        while True:
            time.sleep(0.1)
            if self.ser.inWaiting() > 0:
                try:
                    answer += self.ser.read( self.ser.in_waiting )
                except serial.SerialException as err:
                    print(str(err))
                    return BIN_ERR_EXCEPTION
            if len( answer ) >= 14:
                return self.frame_check(answer,respond)

            loop = loop + 1
            if loop > timeout:
                return BIN_ERR_TIMEOUT

    def str2bin(self,string):
        hexcode = []
        for index in string:
            hexcode.append(ord(index))
        return bytes(hexcode)

    def __makeframe( self ,err,type,code , order, data):       
        size = struct.pack( '>H' , len( data ) )
        crc = libscrc.modbus( b'\x55' + err + type + code +  order  + size + data )
        return b'\x55' + err+type + code  +  order  + size + data +struct.pack('<H' ,crc ) + b'\xcc\xcc'
    '''
    @catch_prococol_exception

    def pri_server_set( self ,src):
        hexdata = self.str2bin(src)
        data = self.__makeframe( b'\x00',b'\x00' , b'\x04' ,b'\x00\x00',hexdata)
        return self.writeWaitAnswer( data,b'\x00',b'\x00' , b'\x04' ,b'\x00\x00' )

    def pri_server_read( self ):
        data = self.__makeframe( b'\x00',b'\x00' , b'\x05' ,b'\x00\x00',b'\x00\x00')
        return self.writeWaitAnswer( data,b'\x00',b'\x00' , b'\x05' ,b'\x00\x00' )
    '''

    def msg_server_set(self,src):
        hexdata = self.str2bin(src)
        data = self.__makeframe( b'\x00',b'\x00' , b'\x06' ,b'\x00\x00',hexdata)
        return self.writeWaitAnswer( data,b'\x00',b'\x00' , b'\x06' ,b'\x00\x00' )

    def msg_server_read(self):
        data = self.__makeframe( b'\x00',b'\x00' , b'\x07' ,b'\x00\x00',b'\x00\x00')
        return self.writeWaitAnswer( data,b'\x00',b'\x00' , b'\x07' ,b'\x00\x00' )
    
    def ota_server_set(self,src):
        hexdata = self.str2bin(src)
        data = self.__makeframe( b'\x00',b'\x00' , b'\x08' ,b'\x00\x00',hexdata)
        return self.writeWaitAnswer( data,b'\x00',b'\x00' , b'\x08' ,b'\x00\x00' )

    def ota_server_read(self):
        data = self.__makeframe( b'\x00',b'\x00' , b'\x09' ,b'\x00\x00',b'\x00\x00')
        return self.writeWaitAnswer( data,b'\x00',b'\x00' , b'\x09' ,b'\x00\x00' )
    
    def rtcm_server_set(self,src):
        hexdata = self.str2bin(src)
        data = self.__makeframe( b'\x00',b'\x00' , b'\x0a' ,b'\x00\x00',hexdata)
        return self.writeWaitAnswer( data,b'\x00',b'\x00' , b'\x0a' ,b'\x00\x00' )

    def rtcm_server_read(self):
        data = self.__makeframe( b'\x00',b'\x00' , b'\x0b' ,b'\x00\x00',b'\x00\x00')
        return self.writeWaitAnswer( data,b'\x00',b'\x00' , b'\x0b' ,b'\x00\x00' )

    def open_usb(self):
        data = self.__makeframe( b'\x00',b'\x02' , b'\x00' ,b'\x00\x00',b'\x00\x00')
        return self.writeWaitAnswer( data,b'\x00',b'\x02' , b'\x00' ,b'\x00\x00' )

    def close_usb(self):
        data = self.__makeframe( b'\x00',b'\x02' , b'\x01' ,b'\x00\x00',b'\x00\x00')
        return self.writeWaitAnswer( data,b'\x00',b'\x02' , b'\x01' ,b'\x00\x00' )

    def format_disk(self):
        data = self.__makeframe( b'\x00',b'\x02' , b'\x02' ,b'\x00\x00',b'\x00\x00')
        self.ser.write( data )
        return b'U\x00'

    def read_disk(self):
        data = self.__makeframe( b'\x00',b'\x02' , b'\x03' ,b'\x00\x00',b'\x00\x00')
        return self.writeWaitAnswer( data,b'\x00',b'\x02' , b'\x03' ,b'\x00\x00' )

    def read_mcu(self):
        data = self.__makeframe( b'\x00',b'\x02' , b'\x07' ,b'\x00\x00',b'\x00\x00')
        return self.writeWaitAnswer( data,b'\x00',b'\x02' , b'\x07' ,b'\x00\x00' )




        








    






