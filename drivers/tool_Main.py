#_*_ coding:UTF-8 _*_

# !/usr/bin/python
# Python:   3.6.5
# Platform: Windows
# Author:   drl 
# History:  2020-09-15 Ver:1.0 [drl] Initialization

import os
import json
import queue
import struct
import logging
import threading
import binascii
from datetime import datetime
import time

#from drivers.update_thread import update_thread
from ui.poshub import Ui_poshub_tool
from drivers.poshub_protocol import poshub_Protocol


from PyQt5.QtGui  import QColor
from PyQt5.QtGui  import QIcon

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHeaderView, QAbstractItemView
from PyQt5.QtWidgets import QMenu, QTableWidgetItem, QDialog, QLineEdit, QPushButton
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QComboBox
from PyQt5.QtWidgets import QDesktopWidget
import serial.tools.list_ports
import re
from drivers.poshub_configparser import Poshub_Config_Parser

RETRY_COUNT = 3
poshub_Error = {1:'group error',2:'function error',3:'order error',4:'length error',5:'invalid config',6:'time out',7:'CRC16 error'}

def mainWindowsException( origin_func ):
    def wrapper( self, *args, **kwargs ):
        try:
            return origin_func( self, *args, **kwargs )
        except BaseException as err:
            logging.error( str(err) )
    return wrapper
    

def ip_port_get(str):
    str_len=len(str)
    for index in range(0,str_len):
        if str[index] == 44:
            break

    if index==str_len:
        return None,None

    for index1 in range(index+1,str_len):
        if str[index1] == 44:
            break

    if index1==str_len:
        return None,None

    for index2 in range(index1+1,str_len):
        if str[index2] == 59:
            return str[index+1:index1],str[index1+1:index2]
    
    return None,None

def rtcm_info_get(string):
    str_len=len(string)
    for index0 in range(string.index(b'_'),str_len):
        if string[index0] == 44:
            break

    if index0==str_len:
        return None

    for index1 in range(index0+1,str_len):
        if string[index1] == 44:
            break

    if index1==str_len:
        return None

    for index2 in range(index1+1,str_len):
        if string[index2] == 44:
            break

    if index2==str_len:
        return None

    for index3 in range(index2+1,str_len):
        if string[index3] == 44:
            break

    if index3==str_len:
        return None

    for index4 in range(index3+1,str_len):
        if string[index4] == 44:
            break
    if index4==str_len:
        return None  
    for index5 in range(index4+1,str_len):
        if string[index5] == 59:
            return string[index0+1:index1],string[index1+1:index2],string[index2+1:index3],string[index3+1:index4],string[index4+1:index5]
    
    return None

def disk_capacity_get(string):
    str_len=len(string)
    for index0 in range(0,str_len):
        if string[index0] == 44:
            break
    if index0==str_len:
        return None 

    for index1 in range(index0+1,str_len):
        if string[index1] == 59:
            used = int(string[8:index0]) - int(string[index0+1:index1])
            return str(string[8:index0],'utf-8'),str(used),str(string[index0+1:index1],'utf-8')

    return None

def mcu_info_get(string):
    str_len=len(string)
    for index1 in range(7,str_len):
        if string[index1] == 59:
            return str(string[8:index1],'utf-8')

    return None

class tool_main( Ui_poshub_tool , QMainWindow ):
    def __init__( self , parent = None ):
        super( tool_main,self ).__init__( )
        self.setupUi( self )

        self.setWindowTitle( "poshub tool V1.0" )
        self.center()
        self.setFixedSize(self.width(),self.height())
        self.protocol = poshub_Protocol()
        self.Set_Disabled_PushButton(True)
    

        for item in ("ini","logs"):
            if not os.path.exists(item):
                os.makedirs(item)

        level = dict(DEBUG=logging.DEBUG, INFO=logging.INFO, ERROR=logging.ERROR)
        log_level = logging.DEBUG
        with Poshub_Config_Parser("./ini/conf.ini") as cfg:
            
            if 'LOG' in cfg.__section__():
                log_level = level.get(cfg.getValue("LOG","LEVEL").upper,logging.DEBUG)
            else:
                cfg.setValue("LOG","LEVEL","DEBUG")

        path =os.getcwd() + "\logs\\{}.log".format(datetime.now().strftime('%Y%m%d'))


        try:
            logging.basicConfig( filename=path,
                        filemode='a',
                        level=log_level,
                        format='[%(filename)s,%(funcName)s,%(lineno)d],[%(levelname)s,%(message)s],%(asctime)s',
                        datefmt='%Y/%m/%d %H:%M:%S %p')
        except BaseException as err:
            logging.error(str(err))
            pass

        for com in list( serial.tools.list_ports.comports( ) ):
            self.comboBox_port.addItem(com[0])

        if self.comboBox_port.count() > 0:
            self.pushButton_ctrlport.setDisabled(False)
            self.textBrowser_logout.append("<font color=\"#0000FF\">检测到设备,请选择设备.</font>")
        else:
            self.pushButton_ctrlport.setDisabled(True)
            self.comboBox_port.clear()
            self.pushButton_ctrlport.setText("打开串口")
            #self.pushButton_ctrlport.setStyleSheet("color: rgb(0, 0, 0);")
            self.textBrowser_logout.append('<font color=\"#FF0000\">未检测到设备,请插入设备.</font>')

    def Set_Disabled_PushButton(self,disabled=False):
        self.pushButton_clearn.setDisabled(disabled)
        '''
        self.pushButton_pri_read.setDisabled(disabled)
        self.pushButton_pri_set.setDisabled(disabled)
        '''
        self.pushButton_msg_read.setDisabled(disabled)
        self.pushButton_msg_set.setDisabled(disabled)
        
        self.pushButton_ota_read.setDisabled(True)
        self.pushButton_ota_set.setDisabled(True)
        self.pushButton_ota_enable.setDisabled(True)
        
        self.pushButton_rtcm_read.setDisabled(disabled)
        self.pushButton_rtcm_set.setDisabled(disabled)

        self.pushButton_conn_usb.setDisabled(disabled)
        self.pushButton_close_usb.setDisabled(disabled)
        self.pushButton_mk_disk.setDisabled(disabled)
        self.pushButton_read_disk.setDisabled(disabled)
        self.pushButton_read_mcu.setDisabled(disabled)

    def PushButton_en_check(self):
            PRI_EN={"ON":False,"OFF":True}
            MSG_EN={"ON":False,"OFF":True}
            OTA_EN={"ON":False,"OFF":True}
            RTCM_EN={"ON":False,"OFF":True}

            with Poshub_Config_Parser("./ini/conf.ini") as cfg: 
                section_list =cfg.__section__()     
                #print(section_list)
            
                if 'PRI' in section_list:
                    pri_state = PRI_EN.get(cfg.getValue("PRI","EN"),True)
                else:
                    cfg.setValue("PRI","EN","OFF")
                    pri_state=True

                if 'MSG' in section_list:
                    msg_state = MSG_EN.get(cfg.getValue("MSG","EN"),True)
                else:
                    cfg.setValue("MSG","EN","OFF")
                    msg_state=True

                if 'OTA' in section_list:
                    ota_state = OTA_EN.get(cfg.getValue("OTA","EN"),True)
                else:
                    cfg.setValue("OTA","EN","OFF")
                    ota_state=True

                if 'RTCM' in section_list:
                    rtcm_state = RTCM_EN.get(cfg.getValue("RTCM","EN"),True)
                else:
                    cfg.setValue("RTCM","EN","OFF")
                    rtcm_state=True

            self.pushButton_pri_read.setDisabled(pri_state)
            self.pushButton_pri_set.setDisabled(pri_state)

            self.pushButton_msg_read.setDisabled(msg_state)
            self.pushButton_msg_set.setDisabled(msg_state)

            self.pushButton_ota_read.setDisabled(ota_state)
            self.pushButton_ota_set.setDisabled(ota_state)

            self.pushButton_rtcm_read.setDisabled(rtcm_state)
            self.pushButton_rtcm_set.setDisabled(rtcm_state)

            self.pushButton_conn_usb.setDisabled(False)
            self.pushButton_close_usb.setDisabled(False)
            self.pushButton_mk_disk.setDisabled(False)
            self.pushButton_read_disk.setDisabled(False)
            self.pushButton_read_mcu.setDisabled(False)

    def center(self):
        screen=QDesktopWidget().screenGeometry()
        size=self.geometry()
        self.move((screen.width()-size.width())/2,(screen.height()-size.height())/2)

    def poshub_log_out(self,ret,ok="执行成功",err="执行失败"):
        if ret == 0:
            message = ok

        else:
            message = err
            logging.warning(poshub_Error.get(ret,'other error' ) )  
        
        self.textBrowser_logout.append(message)

    @pyqtSlot()
    def on_pushButton_scanport_clicked(self):
        self.comboBox_port.clear()
        for com in list( serial.tools.list_ports.comports( ) ):
            self.comboBox_port.addItem(com[0])

        if self.comboBox_port.count() > 0:
            self.pushButton_ctrlport.setDisabled(False)
            self.textBrowser_logout.append("<font color=\"#0000FF\">检测到设备,请选择设备.</font>")
        else:
            self.pushButton_ctrlport.setDisabled(True)
            self.comboBox_port.clear()
            self.pushButton_ctrlport.setText("打开串口")
            self.textBrowser_logout.append('<font color=\"#FF0000\">未检测到设备,请插入设备.</font>')

    @pyqtSlot()
    def on_pushButton_ctrlport_clicked(self):
        if not self.protocol.isopen():
            ret,message = self.protocol.connect(self.comboBox_port.currentText(),115200,8,'None',"1")

            if ret is False:
                QMessageBox.warning(self,"警告",message,QMessageBox.Yes,QMessageBox.Yes)
                return

            self.Set_Disabled_PushButton(False)
            self.pushButton_ctrlport.setText("关闭串口")
            self.textBrowser_logout.append("<font color=\"#00FF00\">串口打开成功.</font>")
            self.pushButton_ctrlport.setStyleSheet("background-color:rgb(0,255,0);")
            logging.info('串口%s打开成功'%self.comboBox_port.currentText())

        else:
            self.protocol.close()
            self.textBrowser_logout.append("<font color=\"#00FF00\">串口关闭成功.</font>")
            self.pushButton_ctrlport.setText("打开串口")
            self.pushButton_ctrlport.setStyleSheet("background-color:rgb(225,225,225);")
            self.Set_Disabled_PushButton(True)
            logging.info('串口%s关闭成功'%self.comboBox_port.currentText())
    '''
    @pyqtSlot()
    def on_pushButton_pri_set_clicked(self):
        pri_state = {0:'PRI_OFF,',1:'PRI_ON,'}

        if (self.lineEdit_pri_ip.text() and self.lineEdit_pri_port.text()) == "":
            QMessageBox.information(self,"错误","无效参数",QMessageBox.Yes,QMessageBox.Yes)
            self.textBrowser_logout.append("<font color=\"#FF0000\">无效参数,请输入有效参数....</font>")
            return 

        state_index =self.comboBox_pri_state.currentIndex()
        cmd_str=pri_state.get(state_index,'PRI_OFF,') + self.lineEdit_pri_ip.text() +','+ self.lineEdit_pri_port.text()+';'
        print(cmd_str)

        for index in range(RETRY_COUNT):          
            ret =self.protocol.pri_server_set(cmd_str)
            if ret[0] == 0:
                break

        self.poshub_log_out(ret[0],'一级服务器配置成功','一级服务器配置失败')

    @pyqtSlot()
    def on_pushButton_pri_read_clicked(self):
        for index in range(RETRY_COUNT):
            ret =self.protocol.pri_server_read()
            if ret[0]==0:
                if(ret[7:13] == b"PRI_ON"):
                    self.comboBox_pri_state.setCurrentIndex(1)
                else:
                    self.comboBox_pri_state.setCurrentIndex(0)
                    
                ip,port=ip_port_get(ret)
                print("ip:%s,port:%s"%(str(ip,"utf-8"),str(port,"utf-8")))
                self.lineEdit_pri_ip.setText(str(ip,"utf-8"))
                self.lineEdit_pri_port.setText(str(port,"utf-8"))
                break

        if  ret[0] == 5:
                self.textBrowser_logout.append("一级服务器参数未配置!")
                return

        self.poshub_log_out(ret[0],'一级服务器配置读取成功','一级服务器配置读取失败')
    '''
    @pyqtSlot()
    def on_pushButton_msg_set_clicked(self):
        msg_state = {0:'MSG_OFF,',1:'MSG_ON,'}

        if (self.lineEdit_msg_ip.text() and self.lineEdit_msg_port.text()) == "":
            QMessageBox.information(self,"错误","无效参数",QMessageBox.Yes,QMessageBox.Yes)
            return 

        state_index =self.comboBox_msg_state.currentIndex()
        cmd_str=msg_state.get(state_index,'MSG_OFF,') + self.lineEdit_msg_ip.text() +','+ self.lineEdit_msg_port.text()+';'

        for index in range(RETRY_COUNT):
            ret =self.protocol.msg_server_set(cmd_str)
            if ret[1] == 0:
                break

        self.poshub_log_out(ret[1],'MSG服务器配置成功','MSG服务器配置失败')

    @pyqtSlot()
    def on_pushButton_msg_read_clicked(self):
        for index in range(RETRY_COUNT):
            ret =self.protocol.msg_server_read()
            if ret[1] == 0:
                if(ret[8:14] == b"MSG_ON"):
                    self.comboBox_msg_state.setCurrentIndex(1)
                else:
                    self.comboBox_msg_state.setCurrentIndex(0)
                    
                ip,port=ip_port_get(ret)
                self.lineEdit_msg_ip.setText(str(ip,"utf-8"))
                self.lineEdit_msg_port.setText(str(port,"utf-8"))
                break

            if  ret[1] == 5:
                self.textBrowser_logout.append("MSG服务器参数未配置!")
                return

        self.poshub_log_out(ret[1],'MSG服务器配置读取成功','MSG服务器配置读取失败')
    
    @pyqtSlot()
    def on_pushButton_ota_set_clicked(self):
        ota_state = {0:'OTA_OFF,',1:'OTA_ON,'}

        if (self.lineEdit_ota_ip.text() and self.lineEdit_ota_port.text()) == "":
            QMessageBox.information(self,"错误","无效参数",QMessageBox.Yes,QMessageBox.Yes)
            return 

        state_index =self.comboBox_ota_state.currentIndex()
        cmd_str=ota_state.get(state_index,'OTA_OFF,') + self.lineEdit_ota_ip.text() +','+ self.lineEdit_ota_port.text()+';'
        print(cmd_str)

        for index in range(RETRY_COUNT):
            ret =self.protocol.ota_server_set(cmd_str)
            if ret[1] == 0:
                break

        self.poshub_log_out(ret[1],'OTA服务器配置成功','OTA服务器配置失败')

    @pyqtSlot()
    def on_pushButton_ota_read_clicked(self):       
        for index in range(RETRY_COUNT):
            ret =self.protocol.ota_server_read()
            if ret[1] == 0:
                if(ret[8:14] == b"OTA_ON"):
                    self.comboBox_ota_state.setCurrentIndex(1)
                else:
                    self.comboBox_ota_state.setCurrentIndex(0)
                    
                ip,port=ip_port_get(ret)
                print("ip:%s,port:%s"%(str(ip,"utf-8"),str(port,"utf-8")))
                self.lineEdit_ota_ip.setText(str(ip,"utf-8"))
                self.lineEdit_ota_port.setText(str(port,"utf-8"))
                break

            if  ret[1] == 5:
                self.textBrowser_logout.append("OTA服务器参数未配置!")
                return

        self.poshub_log_out(ret[1],'OTA服务器配置读取成功','OTA服务器配置读取失败')
    

    @pyqtSlot()
    def on_pushButton_rtcm_set_clicked(self):
        rtcm_state = {0:'RTCM_OFF,',1:'RTCM_ON,'}

        if (self.lineEdit_rtcm_ip.text() and self.lineEdit_rtcm_port.text() and self.lineEdit_rtcm_name.text() and self.lineEdit_rtcm_pwd.text()) == "":
            QMessageBox.information(self,"错误","无效参数",QMessageBox.Yes,QMessageBox.Yes)
            return 

        state_index =self.comboBox_rtcm_state.currentIndex()
        cmd_str=rtcm_state.get(state_index,'RTCM_OFF,') + self.lineEdit_rtcm_ip.text() +','+ self.lineEdit_rtcm_port.text()+','+self.comboBox_rtcm_point.currentText()+','+self.lineEdit_rtcm_name.text()+','+self.lineEdit_rtcm_pwd.text()+';'

        for index in range(RETRY_COUNT):
            ret =self.protocol.rtcm_server_set(cmd_str)
            if ret[1] ==0:
                break

        self.poshub_log_out(ret[1],'RTCM服务器配置成功','RTCM服务器配置失败')

    @pyqtSlot()
    def on_pushButton_rtcm_read_clicked(self):
        RTCM_Point={b"RTCM32_GGB":0,b"BJJZ1":1,b"GUDN1":2,b"RTCM30_GG":3,b"AUTO":4}
        for index in range(RETRY_COUNT):
            ret =self.protocol.rtcm_server_read()
            if ret[1] == 0:
                if(ret[8:15] == b"RTCM_ON"):
                    self.comboBox_rtcm_state.setCurrentIndex(1)
                else:
                    self.comboBox_rtcm_state.setCurrentIndex(0)
                    
                ip,port,point,name,pwd=rtcm_info_get(ret)
                
                self.comboBox_rtcm_point.setCurrentIndex(int(RTCM_Point.get(point,0)))
                
                self.lineEdit_rtcm_ip.setText(str(ip,"utf-8"))
                self.lineEdit_rtcm_port.setText(str(port,"utf-8"))
                self.lineEdit_rtcm_name.setText(str(name,"utf-8"))
                self.lineEdit_rtcm_pwd.setText(str(pwd,"utf-8"))
                
                break
            
            if  ret[1] == 5:
                self.textBrowser_logout.append("RTCM服务器参数未配置!")
                return 

        self.poshub_log_out(ret[1],'RTCM服务器配置读取成功','RTCM服务器配置读取失败')

    @pyqtSlot()
    def on_pushButton_conn_usb_clicked(self):
        self.pushButton_read_disk.setDisabled(True)
        self.pushButton_mk_disk.setDisabled(True)
        for index in range(RETRY_COUNT):
            ret =self.protocol.open_usb()
            if ret[1] == 0:
                break

        self.poshub_log_out(ret[1],'USB连接成功','USB连接失败')

    @pyqtSlot()
    def on_pushButton_close_usb_clicked(self):
        self.pushButton_read_disk.setDisabled(False)
        self.pushButton_mk_disk.setDisabled(False)
        for index in range(RETRY_COUNT):
            ret =self.protocol.close_usb()
            if ret[1] == 0:
                break

        self.poshub_log_out(ret[1],'USB关闭成功','USB关闭失败')
    
    @pyqtSlot()
    def on_pushButton_clearn_clicked(self):
        self.textBrowser_logout.clear()

    @pyqtSlot()
    def on_pushButton_mk_disk_clicked(self):      
        for index in range(RETRY_COUNT):
            ret =self.protocol.format_disk()
            if ret[1] ==0:
                break

        self.poshub_log_out(ret[1],'设备格式化成功','设备格式化失败')

    @pyqtSlot()
    def on_pushButton_read_disk_clicked(self):
        for index in range(RETRY_COUNT):
            ret =self.protocol.read_disk()
            if ret[1] ==0:
                total,used,available = disk_capacity_get(ret)
                self.textBrowser_logout.append("Total:{} MB,Used:{} MB,Available:{} MB".format(total,used,available))
                break

        if ret[1] != 0:
            logging.warning(poshub_Error.get(ret,'other error' ) )  
            self.textBrowser_logout.append('设备容量获取失败')

    @pyqtSlot()
    def on_pushButton_read_mcu_clicked(self):

        for index in range(RETRY_COUNT):
            ret =self.protocol.read_mcu()
            if ret[1] ==0:
                info = mcu_info_get(ret)
                self.textBrowser_logout.append(info)
                break

        if ret[1] != 0:
            logging.warning(poshub_Error.get(ret,'other error') )  
            self.textBrowser_logout.append('设备信息获取失败')


    





