#_*_ coding:UTF-8 _*_

# !/usr/bin/python
# Python:   3.6.5
# Platform: Windows
# Author:   drl 
# History:  2021-03-16 Ver:1.0 [drl] Initialization

from configparser import ConfigParser

class Poshub_Config_Parser( object ):
    def __init__( self , name = None ):
        super( Poshub_Config_Parser , self ).__init__( )
        self.__name = name
        self.__conf = ConfigParser( )

    def __enter__( self ):
        self.__conf.read( self.__name )
        return self

    def __exit__( self , exc_type , exc_value , traceback ):
        self.__conf.write( open(self.__name , 'w' ) )

    def __section__(self):
        return self.__conf.sections()

    def getValue( self , section , name , value = "" ):
        try:
            return self.__conf.get( section , name ).strip( )
        except BaseException as str:
            print(str)
            pass
        return value

    def setValue( self , section , name , value ):
        try:
            self.__conf.set( section , name , str( value ) )
        except BaseException as err:
            print(str(err))
            self.__conf.add_section( section )
            self.__conf.set( section , name , str( value ) )

    
