# -*- coding: utf-8 -*-
import wx
from IQWave import  WaveIQ
from Spectrum import Spec
from WaterFall import Water 
from DemodEye import Eye
from DemodConstel import Constel
from DemodCCDF import CCDF

from GlobalList import *
import matplotlib 
import os
import AllDialog
from HardwareAccess import *
from Package import *
from MyThread import *
from ThreadStation import *
import usb
import time

class MainWindow(wx.MDIParentFrame):
    def __init__(self):
        wx.MDIParentFrame.__init__(self,None,-1,u"频谱监测",style=wx.DEFAULT_FRAME_STYLE)
        self.SetSize((wx.Display().GetClientArea().GetWidth(),wx.Display().GetClientArea().GetHeight()))
        #icon=wx.Image("./icons/icon.png",wx.BITMAP_TYPE_PNG).Scale(16,16).ConvertToBitmap()
        #self.SetIcon(wx.IconFromBitmap(icon))
        self.Centre()
        self.MakeMenuBar()
        self.SetBackgroundColour((242,245,250))
        matplotlib.rcParams["figure.facecolor"] = '#F2F5FA'
        matplotlib.rcParams["axes.facecolor"] = '0'
        matplotlib.rcParams["ytick.color"] = '0'
        matplotlib.rcParams["xtick.color"] = '0'
        matplotlib.rcParams["grid.color"] = 'w'
        matplotlib.rcParams["text.color"] = 'w'
        matplotlib.rcParams["figure.edgecolor"]="0"
        matplotlib.rcParams["xtick.labelsize"]=12
        matplotlib.rcParams["ytick.labelsize"]=12
        matplotlib.rcParams["axes.labelsize"]=14
        matplotlib.rcParams["grid.linestyle"]="-"
        matplotlib.rcParams["grid.linewidth"]=0.5
        matplotlib.rcParams["grid.color"]='#707070'
       

        self.SpecFrame=None
        self.WaterFrame=None
        self.WaveFrame=None 
        self.DemodWaveFrame=None
        self.DemodConstelFrame=None
        self.DemodCCDFFrame=None
        self.DemodEyeFrame=None

        self.SpecFrame=Spec(self)
        self.SpecFrame.Show()
        self.Tile(wx.VERTICAL)
        global specShow
        specShow=True
        self.Bind(wx.EVT_WINDOW_DESTROY,self.OnCloseSpecFrame,self.SpecFrame)
        ###############创建与中心站通信的对象##############

        self.serverCom=ServerCommunication()
        
        self.recvHardObj=0 
        #################硬件端口定义##############
        self.inPointFFT=0
        self.inPointIQ=0
        self.inPointAb=0
        self.outPoint=0
        
        ################公共帧###################
        self.tail=FrameTail(0,0,0xAA)
        
        ###############编码表##############
        self.dictThres={3:0x00,10:0x01,20:0x02,25:0x03,30:0x04,40:0x05}
        self.ListFreq={0:(98,20),1:(947.5,25),2:(1842.5,75),3:(875,10),4:(1890,20),5:(2345,50), \
                       6:(2605,60),7:(2137.5,15),8:(2310,20),9:(2565,20),10:(2117.5,15),11:(2380,20),  \
                       12:(2645,20),13:(1865,30),14:(2157.5,25),15:(433.92,1.74),16:(915,26),  \
                       17:(2451.75,63.5),18:(5787.5,125)}

        
        ##############由于要传递WaveFrame,WaterFrame对象给线程,窗口一打开就传递进去#############
        self.threadRecv_drawIQ=0
        self.threadRecv_drawFFT=0     
        ###########要传递给WaterFrame确定横坐标范围 ,传递给SpecFrame以便恢复原图。
        self.FreqMin=70
        self.FreqMax=5995       
        
    def OnCloseSpecFrame(self,event):
        self.SpecFrame=None
        global specShow
        specShow=False

    def OnCloseWaveFrame(self,event):
        self.WaveFrame=None
        global waveShow
        waveShow=False

    def OnCloseWaterFrame(self,event):
        self.WaterFrame=None
        global waterShow
        waterShow=False
    def OnCloseDemodWaveFrame(self,event):
        self.DemodWaveFrame=None
        global demodWaveShow
        demodWaveShow=False
    
    def OnCloseDemodConstelFrame(self,event):
        self.DemodConstelFrame=None
        global demodConstelShow
        demodConstelShow=False

    def OnCloseDemodEyeFrame(self,event):
        self.DemodEyeFrame=None
        global demodEyeShow
        demodEyeShow=False
    
    def OnCloseDemodCCDFFrame(self,event):
        self.DemodCCDFFrame=False
        global demodCCDFShow
        demodCCDFShow=False
    

    def MakeMenuBar(self):
        self.menubar=wx.MenuBar()
           
        self.filemenu=wx.Menu()
        i=self.filemenu.Append(-1,u"开启上传")
        self.Bind(wx.EVT_MENU,self.OnStartTransfer,i)  
        self.filemenu.AppendSeparator()
        i=self.filemenu.Append(-1,u"关闭上传")
        self.Bind(wx.EVT_MENU,self.OnCloseTransfer,i)    
        self.filemenu.AppendSeparator()
        i=self.filemenu.Append(-1,u"接入方式...")
        self.Bind(wx.EVT_MENU,self.OnSetAccessWay,i) 
        self.menubar.Append(self.filemenu,u"&硬件控制")

        self.display_menu=wx.Menu()
        i= self.display_menu.Append(-1,u"接收增益")
        self.Bind(wx.EVT_MENU,self.OnSetRecvGain,i)
        self.display_menu.AppendSeparator()
        i= self.display_menu.Append(-1,u"发射衰减")
        self.Bind(wx.EVT_MENU,self.OnSetSendWeak,i)
        self.display_menu.AppendSeparator()
        i= self.display_menu.Append(-1,u"检测门限")
        self.Bind(wx.EVT_MENU,self.OnSetThres,i)
        self.display_menu.AppendSeparator()
        submenu=wx.Menu()
        i1=submenu.Append(-1,u"压制公共参数")
        i2=submenu.Append(-1,u"单频点压制")
        i3=submenu.Append(-1,u"双频点压制")
        self.Bind(wx.EVT_MENU,self.OnSetPressPara,i1)
        self.Bind(wx.EVT_MENU,self.OnSetPressOne,i2)
        self.Bind(wx.EVT_MENU,self.OnSetPressTwo,i3)
        self.display_menu.AppendMenu(-1,u"压制发射...",submenu)
        self.menubar.Append(self.display_menu,u"&参数设置")

        self.setting_menu=wx.Menu()
        i=self.setting_menu.Append(-1,u"全频段...")
        self.Bind(wx.EVT_MENU,self.OnSetFullSweep,i)
        self.setting_menu.AppendSeparator()
        i=self.setting_menu.Append(-1,u"指定频段...")
        self.Bind(wx.EVT_MENU,self.OnSetSpecialSweep,i)
        self.setting_menu.AppendSeparator()
        i=self.setting_menu.Append(-1,u"多频段...")
        self.Bind(wx.EVT_MENU,self.OnSetMutiSweep,i)
        self.menubar.Append(self.setting_menu,u"&扫频设置")

        self.linkmenu=wx.Menu()
        i= self.linkmenu.Append(-1,u"定频公共参数")
        self.Bind(wx.EVT_MENU,self.OnSetIQPara,i)
        self.setting_menu.AppendSeparator()
        i=self.linkmenu.Append(-1,u"定频频点频率")
        self.Bind(wx.EVT_MENU,self.OnSetIQFreq,i)
        
        self.menubar.Append(self.linkmenu,u"&定频设置")


        self.commandmenu=wx.Menu()
        i=self.commandmenu.Append(-1,u"扫频范围")
        self.Bind(wx.EVT_MENU,self.OnQuerySweepRange,i)
        self.commandmenu.AppendSeparator()
        submenu=wx.Menu()
        i1=submenu.Append(-1,u"定频接收频率")
        i2=submenu.Append(-1,u"定频接收参数")
        self.Bind(wx.EVT_MENU,self.OnQueryIQFreq,i1)
        self.Bind(wx.EVT_MENU,self.OnQueryIQPara,i2)
        self.commandmenu.AppendMenu(-1,u"定频参数",submenu)
        self.commandmenu.AppendSeparator()

        submenu=wx.Menu()
        i1=submenu.Append(-1,u"压制发射频率")
        i2=submenu.Append(-1,u"压制发射参数")
        self.Bind(wx.EVT_MENU,self.OnQueryPressFreq,i1)
        self.Bind(wx.EVT_MENU,self.OnQueryPressPara,i2)
        self.commandmenu.AppendMenu(-1,u"压制参数",submenu)

        self.commandmenu.AppendSeparator()
        i=self.commandmenu.Append(-1,u"接收增益")
        self.Bind(wx.EVT_MENU,self.OnQueryRecvGain,i)
        self.commandmenu.AppendSeparator()
        i=self.commandmenu.Append(-1,u"发射衰减")
        self.Bind(wx.EVT_MENU,self.OnQuerySendWeak,i)
        self.commandmenu.AppendSeparator()
        i=self.commandmenu.Append(-1,u"检测门限")
        self.Bind(wx.EVT_MENU,self.OnQueryThres,i)
        self.commandmenu.AppendSeparator()
        i=self.commandmenu.Append(-1,u"硬件接入方式")
        self.Bind(wx.EVT_MENU,self.OnQueryAccessWay,i)
        self.commandmenu.AppendSeparator()
        i=self.commandmenu.Append(-1,u"硬件是否开启")
        self.Bind(wx.EVT_MENU,self.OnQueryTransferOn,i)
        self.commandmenu.AppendSeparator()
        i=self.commandmenu.Append(-1,u"硬件是否关闭")
        self.Bind(wx.EVT_MENU,self.OnQueryTransferOff,i)
        self.menubar.Append(self.commandmenu,u"&查询")

        self.uploadmenu=wx.Menu()
        submenu=wx.Menu()
        i1=submenu.Append(-1,u"功率谱文件")
        i2=submenu.Append(-1,u"IQ波形文件")
        self.uploadmenu.AppendMenu(-1,u"本地存储",submenu)
        self.Bind(wx.EVT_MENU,self.OnLocalSaveSpec,i1)
        self.Bind(wx.EVT_MENU,self.OnLocalSaveWave,i2)

        self.uploadmenu.AppendSeparator()
        submenu=wx.Menu()
        i1=submenu.Append(-1,u"功率谱文件")
        i2=submenu.Append(-1,u"IQ波形文件")
        self.uploadmenu.AppendMenu(-1,u"文件上传",submenu)
        self.Bind(wx.EVT_MENU,self.OnUploadSpec,i1)
        self.Bind(wx.EVT_MENU,self.OnUploadWave,i2)
        self.menubar.Append(self.uploadmenu,u"&文件处理")
        
        self.servicemenu=wx.Menu()
        i=self.servicemenu.Append(-1,u"入网请求\tCTRL+O")
        self.Bind(wx.EVT_MENU,self.OnConnect,i)
        self.servicemenu.AppendSeparator()
        i=self.servicemenu.Append(-1,u"电磁态势数据请求")
        self.Bind(wx.EVT_MENU,self.OnReqElecTrend,i)
        self.servicemenu.AppendSeparator()
        i=self.servicemenu.Append(-1,u"电磁路径数据请求")
        self.servicemenu.AppendSeparator()
        self.Bind(wx.EVT_MENU,self.OnReqElecPath,i)
        i=self.servicemenu.Append(-1,u"异常频点定位请求")
        self.servicemenu.AppendSeparator()
        self.Bind(wx.EVT_MENU,self.OnReqAbFreq,i)

        submenu=wx.Menu()
        i1=submenu.Append(-1,u"台站登记属性")
        i2=submenu.Append(-1,u"登记台站当前属性")
        i3=submenu.Append(-1,u"全部台站记录属性")
        self.Bind(wx.EVT_MENU,self.OnQueryStationPro,i1)
        self.Bind(wx.EVT_MENU,self.OnQueryCurStationPro,i2)
        self.Bind(wx.EVT_MENU,self.OnQueryAllStationPro,i3)
        self.servicemenu.AppendMenu(-1,u"台站属性查询",submenu)
        self.servicemenu.AppendSeparator()
        submenu=wx.Menu()
        i1=submenu.Append(-1,u"在网终端属性")
        i2=submenu.Append(-1,u"所有注册终端属性")
        self.Bind(wx.EVT_MENU,self.OnQueryPortPro,i1)
        self.Bind(wx.EVT_MENU,self.OnQueryAllPortPro,i2)
        self.servicemenu.AppendMenu(-1,u"终端属性查询",submenu)
        self.servicemenu.AppendSeparator()
        i=self.servicemenu.Append(-1,u"国家无线电频率规划查询")
        self.Bind(wx.EVT_MENU,self.OnQueryFreqPlan,i)
        submenu=wx.Menu()
        i1=submenu.Append(-1,u"更改扫频参数")
        i2=submenu.Append(-1,u"更改定频参数")
        i3=submenu.Append(-1,u"启动压制发射")
        self.Bind(wx.EVT_MENU,self.OnChangeAnotherSweep,i1)
        self.Bind(wx.EVT_MENU,self.OnChangeAnotherIQPara,i2)
        self.Bind(wx.EVT_MENU,self.OnChangeAnotherPress,i3)
        self.servicemenu.AppendSeparator()
        self.servicemenu.AppendMenu(-1,u"高级用户更改另一终端请求",submenu)
        self.menubar.Append(self.servicemenu,u"&服务请求")
        
        self.IQmenu=wx.Menu()
        i=self.IQmenu.Append(-1,u"历史功率谱")
        self.Bind(wx.EVT_MENU,self.OnSetSpecTime,i)
        self.IQmenu.AppendSeparator()
        submenu=wx.Menu()
        i1=submenu.Append(-1,u"解调时间段")
        i2=submenu.Append(-1,u"窗口显示类型")
        self.Bind(wx.EVT_MENU,self.OnSetDemodTime,i1)
        self.Bind(wx.EVT_MENU,self.OnDemodDisplay,i2)
        self.IQmenu.AppendMenu(-1,u"解调历史IQ数据",submenu)
        self.menubar.Append(self.IQmenu,u"&文件请求")


        self.windowmenu=wx.Menu()
        i=self.windowmenu.Append(-1,u"显示设置")
        self.Bind(wx.EVT_MENU,self.OnDisplayWindow,i)
        self.menubar.Append(self.windowmenu,u"&显示窗口")


        self.SetMenuBar(self.menubar)
    
    ####入网相关######
    def OnConnect(self,event):
        self.serverCom.ConnectToServer()
        '''
        receiveServerDataThread=ReceiveServerData(self.SpecFrame,self.serverCom.sock,self.outPoint)
        receiveServerDataThread.start()
        '''
        connect=ConnectServer()
        connect.CommonHeader=FrameHeader(0x055,0xA1,0x0F,0)
        connect.CommonTail=self.tail 
        connect.LonLatAlti=LonLatAltitude(0,0,0,0,0,0,0,0,0,0,0)

        self.serverCom.SendQueryData(0,bytearray(connect))

        #thread=UploadThread(self.serverCom.sock,0)
        #thread.start()
        print 'start receiving data thread'
        
        
        
    ###硬件相关################
    
    def OnStartTransfer(self,event):
        dev = usb.core.find(idVendor=0x04b4, idProduct=0x00f1)
        cfg=dev[0]
        intf=cfg[(0,0)]
        #0x01
        self.outPoint=intf[0]
        #0x81 fft
        self.inPointFFT=intf[1]
        #0x82 iq
        self.inPointIQ=intf[3]
        #0x83 query receive and abFreq
        self.inPointAb=intf[5]
        transfer=TransferSet()
        transfer.CommonHeader=FrameHeader(0x55,0x0A,0x0F,0)
        transfer.CommonTail=self.tail
        self.outPoint.write(bytearray(transfer))
        
        print 'usb transfer open'
        
        #########创建与硬件通信的对象################
        self.recvHardObj=RecvHardwaveData(self.inPointFFT,self.inPointIQ,self.inPointAb)
        
        ##########开启与硬件通信的线程##################
        
        self.threadRecv_drawFFT=ReceiveFFTThread(self.recvHardObj,self.SpecFrame,self.WaterFrame)
        self.threadRecv_drawFFT.start()
        
    
        #thread=ReceiveQueryThread(self.SpecFrame)
        #thread.start()
        
        #self.threadRecv_drawIQ=ReceiveIQThread(self.recvHardObj,self.WaveFrame)
        #self.threadRecv_drawIQ.start()
      
        
        #self.threadRecv_drawFFT=DrawSpecAbListThread(self.SpecFrame,self.WaterFrame)
        #self.threadRecv_drawFFT.start()
        
        
    def OnCloseTransfer(self,event):
        transfer=TransferSet()
        transfer.CommonHeader=FrameHeader(0x55,0x0B,0x0F,0)
        transfer.CommonTail=self.tail
        self.outPoint.write(bytearray(transfer))
        
        print 'usb transfer close'

    ###设置相关指令####
    def OnSetAccessWay(self,event):
        dlg=AllDialog.AccessSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            if(dlg.CtrlUSB.GetValue()): pass
        
            header=FrameHeader(0x55,0x09,0x0F,0x00)
            usbWay=AccessWaySet(header,0x03,0,0,0,0,0,0,0,0,0,self.tail)
            self.outPoint.write(bytearray(usbWay))
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowAccessWay(usbWay)
      
    def OnSetRecvGain(self,event):
        dlg=AllDialog.GainSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            Gain=int(dlg.sliderGain.GetValue())
            header=FrameHeader(0x55,0x04,0x0F,0x00)
            gainSet=RecvGainSet()
            gainSet.CommonHeader=header
            gainSet.RecvGain=Gain+3
            gainSet.CommonTail=self.tail
            self.outPoint.write(bytearray(gainSet))
            for i in bytearray(gainSet):
                print 'array   ',i,
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowRecvGain(gainSet)
            
    def OnSetSendWeak(self,event):
        dlg=AllDialog.WeakSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            Weak=int(dlg.sliderWeak.GetValue())
            print Weak
            header=FrameHeader(0x55,0x05,0x0F,0x00)
            SendWeak=SendWeakSet()
            SendWeak.CommonHeader=header
            SendWeak.SendWeak=Weak
            SendWeak.CommonTail=self.tail
            self.outPoint.write(bytearray(SendWeak))
            for i in bytearray(SendWeak):
                print 'array   '+str(i)
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowSendWeak(SendWeak)
        
    def OnSetThres(self,event):
        dlg=AllDialog.ThresSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            thres=int(dlg.selected.GetValue())
            thresSet=ThresSet()
            if(dlg.radio1.GetValue()):
                thresMode=0x00
                thresSet.AdaptThres=self.dictThres[thres]
            else:    
                thresMode=0x01
                thresSet.HighFixedThres=thres>>8
                thresSet.LowFixedThres=thres& 0x00FF    
            
            header=FrameHeader(0x55,0x06,0x0F,0x00)
            thresSet.CommonHeader=header 
            thresSet.ThresMode=thresMode            
            thresSet.CommonTail=self.tail
            for i in bytearray(thresSet):
                print 'array   '+str(i)
            self.outPoint.write(bytearray(thresSet))
            
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowTestGate(thresSet)
    
    def OnSetPressPara(self,event):
        dlg=AllDialog.PressParaSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            freqNum=dlg.radioFreq.GetSelection()
            pressMode=dlg.radioBox.GetSelection()
            if(pressMode==0):
                if(freqNum==0):
                    Mode=0x02
                    oneFreqT1=int(dlg.textPressTime1.GetValue())
                    oneFreqT2=int(dlg.textPressWait.GetValue())
                else:
                    Mode=0x04
                    twoFreqT1=int(dlg.textPressTotal.GetValue())
                    twoFreqT2=int(dlg.textPressWait.GetValue())
                    twoFreqT3=int(dlg.textPressTime1.GetValue())
                    twoFreqT4=int(dlg.textPressTime2.GetValue())
                    
            elif(pressMode==1):
                if(freqNum==0):
                    Mode=0x01
                    oneFreqT1=int(dlg.textPressTime1.GetValue())
                    oneFreqT2=int(dlg.textPressWait.GetValue())
                else:
                    Mode=0x03
                    twoFreqT1=int(dlg.textPressTotal.GetValue())
                    twoFreqT2=int(dlg.textPressWait.GetValue())
                    twoFreqT3=int(dlg.textPressTime1.GetValue())
                    twoFreqT4=int(dlg.textPressTime2.GetValue())
                    
            else:
                Mode=0x05
            
            
            PressSignal=dlg.combox.GetSelection()    
            pressSet=PressParaSet()   
            header=FrameHeader(0x55,0x08,0x0F,0)
            pressSet.PressMode=Mode
            pressSet.CommonHeader=header
            pressSet.PressSignal=PressSignal+1
            pressSet.CommonTail=self.tail
            
            if(PressSignal==2 or PressSignal==3):
                pressSet.PressSignalBandWidth=PressSignal
            else:
                pressSet.PressSignalBandWidth=PressSignal+1
            if(Mode!=0x05):
                if(freqNum==0):
                    pressSet.HighT1=oneFreqT1>>8
                    pressSet.LowT1=oneFreqT1&0x00FF
                    pressSet.HighT2=oneFreqT2>>8
                    pressSet.LowT2= oneFreqT2&0x00FF    
                else:
                    pressSet.HighT1=twoFreqT1>>8
                    pressSet.LowT1=twoFreqT1&0x00FF
                    pressSet.HighT2=twoFreqT2>>8
                    pressSet.LowT2= twoFreqT2&0x00FF
                    pressSet.HighT3=twoFreqT3>>8
                    pressSet.LowT3=twoFreqT3&0x00FF
                    pressSet.HighT4=twoFreqT4>>8
                    pressSet.LowT4=twoFreqT4&0x00FF 
                
            for i in bytearray(pressSet):
                print 'array   '+str(i) 
            self.outPoint.write(bytearray(pressSet))
             
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowPressPara(pressSet)
            
        
    def OnSetPressOne(self,event):
        dlg=AllDialog.PressOneSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            PressFreq=float(dlg.textPressFreq.GetValue())
            array=self.FreqToByte(PressFreq)
            pressFreqSet=PressFreqSet()
            pressFreqSet.CommonHeader=FrameHeader(0x55,0x03,0x0F,0)
            pressFreqSet.CommonTail=self.tail
            pressFreqSet.PressNum=1
            pressFreqSet.FreqArray[0]=CentreFreq(array[0],array[1],array[2],array[3])
            for i in bytearray(pressFreqSet):
                print 'array   '+str(i)
            self.outPoint.write(bytearray(pressFreqSet))
             
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowPressFreq(pressFreqSet)
        
    def FreqToByte(self,freq):
        freqInt=int(freq)
        freqFloat=freq-freqInt
        freqF=int(freqFloat*2**10)
        highFreqInt=freqInt>>6
        lowFreqInt=freqInt&0x003F
        highFreqFrac=freqF>>8
        lowFreqFrac=freqF&0x0FF
        return (highFreqInt,highFreqFrac,lowFreqInt,lowFreqFrac)
        

    def OnSetPressTwo(self,event):
        
        dlg=AllDialog.PressTwoSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            PressFreq1=float(dlg.textPressFreq1.GetValue())
            PressFreq2=float(dlg.textPressFreq2.GetValue())
            array1=self.FreqToByte(PressFreq1)
            array2=self.FreqToByte(PressFreq2)
            pressFreqSet=PressFreqSet()
            pressFreqSet.CommonHeader=FrameHeader(0x55,0x03,0x0F,0)
            pressFreqSet.CommonTail=self.tail
            pressFreqSet.PressNum=2
            pressFreqSet.FreqArray[0]=CentreFreq(array1[0],array1[1],array1[2],array1[3])    
            pressFreqSet.FreqArray[1]=CentreFreq(array2[0],array2[1],array2[2],array2[3])
            for i in bytearray(pressFreqSet):
                print 'array   '+str(i) 
            self.outPoint.write(bytearray(pressFreqSet))
           
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowPressFreq(pressFreqSet)

    def OnSetFullSweep(self,event):
        dlg=AllDialog.FullSweepSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            sweepRangeSet=SweepRangeSet()
            sweepRangeSet.CommonHeader=FrameHeader(0x55,0x01,0x0F,0)
            sweepRangeSet.CommonTail=self.tail
            sweepRangeSet.SweepRecvMode=1
            sweepRangeSet.SweepSectionTotalNum=1
            sweepRangeSet.SweepSectionNo=1
            sweepRangeSet.StartSectionNo=1 
            sweepRangeSet.EndSectionNo=237 
            
            if(dlg.radioM.GetValue()):
                sweepRangeSet.FileUploadMode=3
                sweepRangeSet.ExtractM=int(dlg.textM.GetValue())
            elif(dlg.radioAuto.GetValue()):
                sweepRangeSet.FileUploadMode=2
                choice=dlg.ChangeThres.GetSelection()
                if(choice==0):
                    sweepRangeSet.ChangeThres=3
                else:
                    sweepRangeSet.ChangeThres=2
            else:
                sweepRangeSet.FileUploadMode=1
            self.outPoint.write(bytearray(sweepRangeSet))
            
          
            self.SpecFrame.panelFigure.setSpLabel()
            self.FreqMin=70
            self.FreqMax=5995 
            self.SpecFrame.panelFigure.FFT_Min_X=70 

            self.SpecFrame.panelFigure.FFT_Max_X=5995 
            self.SpecFrame.panelFigure.Min_X.SetValue(str(self.FreqMin))
            self.SpecFrame.panelFigure.Max_X.SetValue(str(self.FreqMax))
            
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowSweepRange(sweepRangeSet)
           

    def OnSetSpecialSweep(self,event):
        dlg=AllDialog.SpecialSweepSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            sweepRangeSet=SweepRangeSet()
            sweepRangeSet.CommonHeader=FrameHeader(0x55,0x01,0x0F,0)
            sweepRangeSet.CommonTail=self.tail
            sweepRangeSet.SweepRecvMode=2
            sweepRangeSet.SweepSectionNo=1
            sweepRangeSet.SweepSectionTotalNum=1
            
            if(dlg.radioM.GetValue()):
                sweepRangeSet.FileUploadMode=3
                sweepRangeSet.ExtractM=int(dlg.textM.GetValue())
            elif(dlg.radioAuto.GetValue()):
                sweepRangeSet.FileUploadMode=2
                choice=dlg.ChangeThres.GetSelection()
                if(choice==0):
                    sweepRangeSet.ChangeThres=3
                else:
                    sweepRangeSet.ChangeThres=2
                    
            else:
                sweepRangeSet.FileUploadMode=1
            freqStart=int(dlg.FreqStart.GetValue())
            freqEnd=int(dlg.FreqEnd.GetValue())
            array=self.SweepSection(freqStart, freqEnd)
            sweepRangeSet=self.FillSweepRange(sweepRangeSet, array)
            self.outPoint.write(bytearray(sweepRangeSet))
            begin=(array[0]-1)*25+70
            end = array[1]*25+70
            self.SpecFrame.panelFigure.setSpLabel(begin_X=begin,  \
                end_X=end)

            self.FreqMin=begin
            self.FreqMax=end 
            self.SpecFrame.panelFigure.FFT_Min_X=begin 

            self.SpecFrame.panelFigure.FFT_Max_X=end 
            self.SpecFrame.panelFigure.Min_X.SetValue(str(self.FreqMin))
            self.SpecFrame.panelFigure.Max_X.SetValue(str(self.FreqMax))
            
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowSweepRange(sweepRangeSet)
    def FillSweepRange(self,sweepRangeSet,array):
        sweepRangeSet.StartSectionNo=array[0]
        sweepRangeSet.EndSectionNo=array[1]
        sweepRangeSet.HighStartFreq=array[2]
        sweepRangeSet.LowStartFreq=array[3]
        sweepRangeSet.HighEndFreq=array[4]
        sweepRangeSet.LowEndFreq=array[5]
        return sweepRangeSet
    def SweepSection(self,freqStart,freqEnd):
        startK=(freqStart-70)/25
        endK=(freqEnd-70)/25
        startNum=int(float(freqStart-(startK*25+70))*1024/25)
        endNum=int(float(freqEnd-(endK*25+70))*1024/25)
        startKth=startK+1
        endKth=endK+1 
        if ((freqEnd-70)%25==0):
            endKth=endK 
            endNum=1023
        startf_h=startNum>>8
        startf_l=startNum&0x0FF
        endf_h=endNum>>8
        endf_l=endNum&0x0FF
        return (startKth,endKth,startf_h,startf_l,endf_h,endf_l)
        
        
    def OnSetMutiSweep(self,event):
        dlg=AllDialog.MutiSweepSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            sweepRangeSet=SweepRangeSet()
            sweepRangeSet.CommonHeader=FrameHeader(0x55,0x01,0x0F,0)
            sweepRangeSet.CommonTail=self.tail
            sweepRangeSet.SweepRecvMode=3
            if(dlg.radioM.GetValue()):
                sweepRangeSet.FileUploadMode=3
                sweepRangeSet.ExtractM=int(dlg.textM.GetValue())
            elif(dlg.radioAuto.GetValue()):
                sweepRangeSet.FileUploadMode=2
                choice=dlg.ChangeThres.GetSelection()
                if(choice==0):
                    sweepRangeSet.ChangeThres=3
                else:
                    sweepRangeSet.ChangeThres=2 
            else:
                sweepRangeSet.FileUploadMode=1
                
            totalNum=0
            listFreq=[(dlg.FreqStart1.GetValue(),dlg.FreqEnd1.GetValue()),  \
                      (dlg.FreqStart2.GetValue(),dlg.FreqEnd2.GetValue()),  \
                      (dlg.FreqStart3.GetValue(),dlg.FreqEnd3.GetValue()),  \
                      (dlg.FreqStart4.GetValue(),dlg.FreqEnd4.GetValue()),  \
                      (dlg.FreqStart5.GetValue(),dlg.FreqEnd5.GetValue())
                      ]  
            for i in range(5):
                if(listFreq[i][0]):
                    totalNum+=1
            sweepRangeSet.SweepSectionTotalNum=totalNum
            for i in range(5):
                if(listFreq[i][0]):
                    sweepRangeSet.SweepSectionNo=i+1
                    freqStart=int(listFreq[i][0])
                    freqEnd=int(listFreq[i][1])
                    array=self.SweepSection(freqStart, freqEnd)
                    sweepRangeSet=self.FillSweepRange(sweepRangeSet, array)
                    for i in bytearray(sweepRangeSet):
                        print 'array   '+str(i) 
             
                    self.outPoint.write(bytearray(sweepRangeSet))
            
            begin=(int(listFreq[0][0])-70)/25*25+70
            end =((int(listFreq[totalNum-1][1])-70)/25+1)*25+70
            self.SpecFrame.panelFigure.setSpLabel(begin_X=begin,end_X=end)       
            

            self.FreqMin=begin
            self.FreqMax=end 
            self.SpecFrame.panelFigure.FFT_Min_X=begin 

            self.SpecFrame.panelFigure.FFT_Max_X=end 
            self.SpecFrame.panelFigure.Min_X.SetValue(str(self.FreqMin))
            self.SpecFrame.panelFigure.Max_X.SetValue(str(self.FreqMax))

            
        dlg.Destroy()   
        self.threadRecv_drawFFT.ShowSweepRange(sweepRangeSet)     
            
                            
    def OnSetIQPara(self,event):
        dlg=AllDialog.IQParaSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            bandWidth=int(dlg.BandWidth.GetSelection())
            uploadNum=int(dlg.textUploadNum.GetValue())
            delayTime=int(dlg.textDelay.GetValue())
            
            curTime=time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
            iqPara=IQParaSet()
            iqPara.CommonHeader=FrameHeader(0x55,0x07,0x0F,0)
            iqPara.CommonTail=self.tail
            iqPara.BandWidth=bandWidth+1
            iqPara.DataRate=bandWidth+1
            iqPara.UploadNum=uploadNum
            Year=int(curTime[0:4])
            Month=int(curTime[4:6])
            Day=int(curTime[6:8])
            Hour=int(curTime[8:10])
            Min=int(curTime[10:12])
            Second=int(curTime[12:14])+delayTime
            if(Second>=60):
                Min+=1 
                Second-=60
            iqPara.Time.HighYear=Year>>4
            iqPara.Time.LowYear=Year&0x00F
            iqPara.Time.Month=Month
            iqPara.Time.Day=Day
            iqPara.Time.HighHour=Hour>>2
            iqPara.Time.LowHour=Hour&0x03
            iqPara.Time.Minute=Min
            iqPara.Time.Second=Second
           
            self.outPoint.write(bytearray(iqPara))
           
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowIQPara(iqPara)
    def OnSetIQFreq(self,event):
        dlg=AllDialog.IQFreqSetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            iqFreq=IQFreqSet()
            iqFreq.CommonHeader=FrameHeader(0x55,0x02,0x0F,0)
            iqFreq.CommonTail=self.tail
            listFreq=[]
            Freq1=float(dlg.textFreq1.GetValue())
            Freq2=dlg.textFreq2.GetValue()
            Freq3=dlg.textFreq3.GetValue()
            listFreq.append(Freq1)
            if(Freq2):
                listFreq.append(float(Freq2))
            if(Freq3):
                listFreq.append(float(Freq3))
            for i in xrange(len(listFreq)):
                array=self.FreqToByte(listFreq[i])
                iqFreq.FreqArray[i]=CentreFreq(array[0],array[1],array[2],array[3])
            iqFreq.FreqNum=len(listFreq)
            for i in bytearray(iqFreq):
                print 'array   '+str(i) 
            self.outPoint.write(bytearray(iqFreq))
            
        dlg.Destroy()
        self.threadRecv_drawFFT.ShowIQCentreFreq(iqFreq)
        

    ###查询相关指令#####
    
    def QuerySend(self,funcPara):
        query=Query()
        query.CommonHeader=FrameHeader(0x55,funcPara,0x0F,0)
        query.CommonTail=self.tail
        self.outPoint.write(bytearray(query))   
        
    def OnQuerySweepRange(self,event):
        self.QuerySend(0x11)
    
    def OnQueryIQFreq(self,event):
        self.QuerySend(0x12)
    def OnQueryIQPara(self,event):
        self.QuerySend(0x17)
    def OnQueryPressFreq(self,event):
        self.QuerySend(0x13)
    def OnQueryPressPara(self,event):
        self.QuerySend(0x18)
    def OnQueryRecvGain(self,event):
        self.QuerySend(0x14)
    def OnQuerySendWeak(self,event):
        self.QuerySend(0x15)
    def OnQueryThres(self,event):
        self.QuerySend(0x16)
    def OnQueryAccessWay(self,event):
        self.QuerySend(0x19)
    def OnQueryTransferOn(self):
        self.QuerySend(0x1A)
    def OnQueryTransferOff(self):
        self.QuerySend(0x1B)
        
    ####文件上传#####
    
    def OnLocalSaveSpec(self,event):
        pass
    def OnUploadSpec(self,event):
        pass

    def OnLocalSaveWave(self,event):
        pass
    def OnUploadWave(self,event):
        pass
    
    ########服务请求###############
    
    ###电磁分布AND异常频点定位######

    def OnReqElecTrend(self,event):
        dlg=AllDialog.ReqElecTrendDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            reqElec=ReqElecTrend()
            reqElec.CommonHeader=FrameHeader(0x55,0xA2,0x0F,0)
            reqElec.CommonTail=self.tail
            if(dlg.radioChoose.GetValue()):
                centreFreq=self.ListFreq[dlg.FreqSection.GetSelection()][0]
                bandWidth=self.ListFreq[dlg.FreqSection.GetSelection()][1]
            else:
                centreFreq=int(dlg.CentreFreq.GetValue())
                bandWidth=int(dlg.BandWidth.GetValue())
            
            reqElec.HighCentreFreq=centreFreq>>8
            reqElec.HighCentreFreq=centreFreq&0x00FF
            reqElec.BandWidth=bandWidth
            reqElec.Raius=int(dlg.Radius.GetValue())
            fenBianLv=float(dlg.Radius.GetValue())
            startTime=(int(dlg.StartTimeYear.GetValue()),int(dlg.StartTimeMonth.GetValue()),  \
                       int(dlg.StartTimeDay.GetValue()),int(dlg.StartTimeHour.GetValue()),    \
                       int(dlg.StartTimeMinute.GetValue())
                       )
            endTime=(int(dlg.EndTimeYear.GetValue()),int(dlg.EndTimeMonth.GetValue()),  \
                       int(dlg.EndTimeDay.GetValue()),int(dlg.EndTimeHour.GetValue()),    \
                       int(dlg.EndTimeMinute.GetValue())
                       )
            
            reqElec.FenBianLvInteger=int(fenBianLv)
            reqElec.FenBianLvFraction=int((fenBianLv-int(fenBianLv))*8)
            reqElec.RefreshIntv=int(dlg.RefreshIntv.GetValue())
            reqElec.StartTime=self.ByteToTime(startTime)
            reqElec.EndTime=self.ByteToTime(endTime)
            frameLen=sizeof(reqElec)
            self.serverCom.SendQueryData(frameLen,reqElec)
        dlg.Destroy()

    def ByteToTime(self,time):
        Obj=Time()
        Obj.HighYear=time[0]>>4
        Obj.LowYear=time[0]&0x00F
        Obj.Month=time[1]
        Obj.Day=time[2]
        Obj.HighHour=time[3]>>2
        Obj.LowHour=time[3]&0x03
        Obj.Minute=time[4]
        
        return Obj
            
    def OnReqElecPath(self,event):
        dlg=AllDialog.ReqElecPathDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            reqElec=ReqElecTrend()
            reqElec.CommonHeader=FrameHeader(0x55,0xA3,0x0F,0)
            reqElec.CommonTail=self.tail
            if(dlg.radioBox1.GetSelection()):
                reqElec.DataSource=15
            elif(dlg.radioBox2.GetSelection()):
                reqElec.Display=15
            
            if(dlg.radioBox3.GetSelection()==0):
                centreFreq=self.ListFreq[dlg.FreqSection.GetSelection()][0]
                bandWidth=self.ListFreq[dlg.FreqSection.GetSelection()][1]
            else:
                centreFreq=int(dlg.CentreFreq.GetValue())
                bandWidth=int(dlg.BandWidth.GetValue())
                
            reqElec.HighCentreFreq=centreFreq>>8
            reqElec.HighCentreFreq=centreFreq&0x00FF
            reqElec.BandWidth=bandWidth

            startTime=(int(dlg.StartTimeYear.GetValue()),int(dlg.StartTimeMonth.GetValue()),  \
                       int(dlg.StartTimeDay.GetValue()),int(dlg.StartTimeHour.GetValue()),    \
                       int(dlg.StartTimeMinute.GetValue())
                       )
            endTime=(int(dlg.EndTimeYear.GetValue()),int(dlg.EndTimeMonth.GetValue()),  \
                       int(dlg.EndTimeDay.GetValue()),int(dlg.EndTimeHour.GetValue()),    \
                       int(dlg.EndTimeMinute.GetValue())
                       )
            
            reqElec.StartTime=self.ByteToTime(startTime)
            reqElec.EndTime=self.ByteToTime(endTime)
            
            frameLen=sizeof(reqElec)
            self.serverCom.SendQueryData(frameLen,reqElec)
        dlg.Destroy()
    def OnReqAbFreq(self,event):
        dlg=AllDialog.ReqAbFreqDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            reqAb=ReqAbFreq()
            reqAb.CommonHeader=FrameHeader(0x55,0xA4,0x0F,0)
            reqAb.CommonTail=self.tail
            if(dlg.radioBox.GetSelection()):
                reqAb.LocateWay=0x0F
            centreFreq=float(dlg.CentreFreq.GetValue())  
            bandWidth=int(dlg.BandWidth.GetSelection())+1  
            centreFreq_I=int(centreFreq)
            centreFreq_F=int((centreFreq-int(centreFreq))*2**10)
            reqAb.Param.HighCentreFreqInteger=centreFreq_I>>6
            reqAb.Param.LowCentreFreqInteger=centreFreq_I&0x003F
            reqAb.Param.HighCentreFreqFraction=centreFreq_F>>8
            reqAb.Param.LowCentreFreqFraction=centreFreq_F&0x0FF
            reqAb.Param.UploadNum=int(dlg.UploadNum.GetValue())
            reqAb.Param.DataRate=bandWidth
            reqAb.Param.BandWidth=bandWidth
            
            startTime=(int(dlg.StartTimeYear.GetValue()),int(dlg.StartTimeMonth.GetValue()),  \
                       int(dlg.StartTimeDay.GetValue()),int(dlg.StartTimeHour.GetValue()),    \
                       int(dlg.StartTimeMinute.GetValue(),int(dlg.StartTimeSecond.GetValue()))
                       )
            
           
            reqAb.Time.HighYear=startTime[0]>>4
            reqAb.Time.LowYear=startTime[0]&0x00F
            reqAb.Time.Month=startTime[1]
            reqAb.Time.Day=startTime[2]
            reqAb.Time.HighHour=startTime[3]>>2
            reqAb.Time.LowHour=startTime[3]&0x03
            reqAb.Time.Minute=startTime[4]
            reqAb.Time.Second=startTime[5]
            frameLen=sizeof(reqAb)
            self.serverCom.SendQueryData(frameLen,reqAb)
            
        dlg.Destroy()
        

    #########台站相关属性#############

    def OnQueryStationPro(self,event):
        dlg=AllDialog.QueryStationProDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            freqStart=int(dlg.FreqStart.GetValue())
            freqEnd=int(dlg.FreqEnd.GetValue())
            stationPro=QueryStationPro()
            stationPro.CommonHeader=FrameHeader(0x55,0xA5,0x0F,0)
            stationPro.CommonTail=self.tail
            stationPro.HighFreqStart=freqStart>>8
            stationPro.LowFreqStart=freqStart&0x00FF
            stationPro.HighFreqEnd=freqEnd>>8
            stationPro.LowFreqEnd=freqEnd&0x00FF
            frameLen=sizeof(stationPro)
            self.serverCom.SendQueryData(frameLen,stationPro)
            
        dlg.Destroy()

    def OnQueryCurStationPro(self,event):
        dlg=AllDialog.QueryCurStationProDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            ID=int(dlg.StationID.GetValue())
            curStationPro=QueryCurStationPro()
            curStationPro.CommonHeader=FrameHeader(0x55,0xA6,0x0F,0)
            curStationPro.CommonTail=self.tail
            curStationPro.Identifier_h=ID>>16
            curStationPro.Identifier_m=ID&0x00FF00
            curStationPro.Identifier_l=ID&0x0000FF
            frameLen=sizeof(curStationPro)
            self.serverCom.SendQueryData(frameLen,curStationPro)
            
        dlg.Destroy()

    def OnQueryAllStationPro(self,event):
        dlg=AllDialog.QueryStationProDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            freqStart=int(dlg.FreqStart.GetValue())
            freqEnd=int(dlg.FreqEnd.GetValue())
            stationPro=QueryStationPro()
            stationPro.CommonHeader=FrameHeader(0x55,0xA8,0x0F,0)
            stationPro.CommonTail=self.tail
            stationPro.HighFreqStart=freqStart>>8
            stationPro.LowFreqStart=freqStart&0x00FF
            stationPro.HighFreqEnd=freqEnd>>8
            stationPro.LowFreqEnd=freqEnd&0x00FF
            frameLen=sizeof(stationPro)
            self.serverCom.SendQueryData(frameLen,stationPro)
            
        dlg.Destroy()
    #############在网和全部终端属性以及无线电频率规划#########

    def OnQueryPortPro(self,event):
        query=Query()
        query.CommonHeader=FrameHeader(0x55,0xA9,0x0F,0)
        query.CommonTail=self.tail
        self.serverCom.SendQueryData(sizeof(query),query)  
        
    def OnQueryAllPortPro(self,event):
        query=Query()
        query.CommonHeader=FrameHeader(0x55,0xAA,0x0F,0)
        query.CommonTail=self.tail
        self.serverCom.SendQueryData(sizeof(query),query)  

    def OnQueryFreqPlan(self,event):
        dlg=AllDialog.QueryFreqPlanDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            freqStart=int(dlg.FreqStart.GetValue())
            freqEnd=int(dlg.FreqEnd.GetValue())
        dlg.Destroy()
        highFreqStart=freqStart>>16
        midFreqStart=(freqStart&0x00FF00)>>8
        lowFreqStart=freqStart&0x0000FF
        
        highFreqEnd=freqEnd>>16
        midFreqEnd=(freqEnd&0x00FF00)>>8
        lowFreqEnd=freqEnd&0x0000FF
        header=FrameHeader(0x55,0xA7,0x0F,0)
        
        structObj=QueryFreqPlan(header,highFreqStart,midFreqStart,  \
                                lowFreqStart,highFreqEnd,midFreqEnd,lowFreqEnd,self.tail)
       
        frameLen=11
        self.serverCom.SendQueryData(frameLen,structObj)



###########高级用户更改另一终端请求########################

    
    def OnChangeAnotherSweep(self,event):
        dlg=AllDialog.ChangeAnotherSweep()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            apointID=int(dlg.ApointID.GetValue())
            recvMode=dlg.RadioBoxSweep.GetSelection()
            transMode=dlg.RadioBoxTrans.GetSelection()
            thresMode=dlg.RadioBoxThres.GetSelection()
            sweepRangeSet=ChangeSweep()
            sweepRangeSet.CommonHeader=FrameHeader(0x55,0xAD,0x0F,0)
            sweepRangeSet.CommonTail=self.tail
            
            sweepRangeSet.ApointID_l=apointID&0x00FF
            sweepRangeSet.ApointID_h=apointID>>8
            sweepRangeSet.SweepRecvMode=recvMode+1
            sweepRangeSet.FileUploadMode=transMode+1
            
            if(transMode==2):
                sweepRangeSet.ExtractM=int(dlg.textM.GetValue())
            elif(transMode==1):
                sweepRangeSet.ChangeThres=int(dlg.ChangeThres.GetValue())
            sweepRangeSet.RecvGain=int(dlg.sliderGain.GetValue())+3
            sweepRangeSet.ThresMode=thresMode
            
            if(thresMode):
                sweepRangeSet.HighFixedThres=int(dlg.StaticThres.GetValue())>>8
                sweepRangeSet.LowFixedThres=int(dlg.StaticThres.GetValue())&0x00FF
            else:
                sweepRangeSet.AdaptThres=int(dlg.AdaptThres.GetValue())
                
            if(recvMode==0):
                self.outPoint.write(bytearray(sweepRangeSet))
            
            elif(recvMode==1):
                sweepRangeSet.SweepSectionTotalNum=1
                sweepRangeSet.SweepSectionNo=1
                freqStart=int(dlg.FreqStart1.GetValue())
                freqEnd=int(dlg.FreqEnd1.GetValue())
                array=self.SweepSection(freqStart, freqEnd)
                sweepRangeSet=self.FillSweepRange(sweepRangeSet, array)
                self.outPoint.write(bytearray(sweepRangeSet))
            else:    
                totalNum=0
                listFreq=[(dlg.FreqStart1.GetValue(),dlg.FreqEnd1.GetValue()),  \
                          (dlg.FreqStart2.GetValue(),dlg.FreqEnd2.GetValue()),  \
                          (dlg.FreqStart3.GetValue(),dlg.FreqEnd3.GetValue()),  \
                          (dlg.FreqStart4.GetValue(),dlg.FreqEnd4.GetValue()),  \
                          (dlg.FreqStart5.GetValue(),dlg.FreqEnd5.GetValue())
                          ]  
                for i in range(5):
                    if(listFreq[i][0]):
                        totalNum+=1
                sweepRangeSet.SweepSectionTotalNum=totalNum
                for i in range(5):
                    if(listFreq[i][0]):
                        sweepRangeSet.SweepSectionNo=i+1
                        freqStart=int(listFreq[i][0])
                        freqEnd=int(listFreq[i][1])
                        array=self.SweepSection(freqStart, freqEnd)
                        sweepRangeSet=self.FillSweepRange(sweepRangeSet, array)
                        self.outPoint.write(bytearray(sweepRangeSet))
                      
        dlg.Destroy()
    def OnChangeAnotherIQPara(self,event):
        dlg=AllDialog.ChangeAnotherIQ()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            bandWidth=int(dlg.BandWidth.GetSelection())
            uploadNum=int(dlg.textUploadNum.GetValue())
            delayTime=int(dlg.textDelay.GetValue())
            
            curTime=time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
            iqPara=ChangeIQPara()
            iqPara.CommonHeader=FrameHeader(0x55,0xAE,0x0F,0)
            iqPara.CommonTail=self.tail
            iqPara.RecvGain=int(dlg.sliderGain.GetValue())+3
            iqPara.ApointID=int(dlg.ApointID.GetValue())
            iqPara.BandWidth=bandWidth+1
            iqPara.DataRate=bandWidth+1
            iqPara.UploadNum=uploadNum
            Year=int(curTime[0:4])
            Month=int(curTime[4:6])
            Day=int(curTime[6:8])
            Hour=int(curTime[8:10])
            Min=int(curTime[10:12])
            Second=int(curTime[12:14])+delayTime
            iqPara.Time.HighYear=Year>>4
            iqPara.Time.LowYear=Year&0x00F
            iqPara.Time.Month=Month
            iqPara.Time.Day=Day
            iqPara.Time.HighHour=Hour>>2
            iqPara.Time.LowHour=Hour&0x03
            iqPara.Time.Minute=Min
            iqPara.Time.Second=Second
           
            listFreq=[]
            Freq1=float(dlg.textFreq1.GetValue())
            Freq2=dlg.textFreq2.GetValue()
            Freq3=dlg.textFreq3.GetValue()
            listFreq.append(Freq1)
            if(Freq2):
                listFreq.append(float(Freq2))
            if(Freq3):
                listFreq.append(float(Freq3))
            for i in xrange(len(listFreq)):
                array=self.FreqToByte(listFreq[i])
                iqPara.FreqArray[i]=CentreFreq(array[0],array[1],array[2],array[3])
            iqPara.FreqNum=len(listFreq)
       
            self.outPoint.write(bytearray(iqPara))
            
        dlg.Destroy()   
    def OnChangeAnotherPress(self,event):
        dlg=AllDialog.ChangeAnotherPress()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            freqNum=dlg.radioFreq.GetSelection()
            pressMode=dlg.radioBox.GetSelection()
            if(pressMode==0):
                if(freqNum==0):
                    Mode=0x02
                    oneFreqT1=int(dlg.textPressTime1.GetValue())
                    oneFreqT2=int(dlg.textPressWait.GetValue())
                else:
                    Mode=0x04
                    twoFreqT1=int(dlg.textPressTotal.GetValue())
                    twoFreqT2=int(dlg.textPressWait.GetValue())
                    twoFreqT3=int(dlg.textPressTime1.GetValue())
                    twoFreqT4=int(dlg.textPressTime2.GetValue())
                    
            elif(pressMode==1):
                if(freqNum==0):
                    Mode=0x01
                    oneFreqT1=int(dlg.textPressTime1.GetValue())
                    oneFreqT2=int(dlg.textPressWait.GetValue())
                else:
                    Mode=0x03
                    twoFreqT1=int(dlg.textPressTotal.GetValue())
                    twoFreqT2=int(dlg.textPressWait.GetValue())
                    twoFreqT3=int(dlg.textPressTime1.GetValue())
                    twoFreqT4=int(dlg.textPressTime2.GetValue())
                    
            else:
                Mode=0x05
            
            PressSignal=dlg.combox.GetSelection()   
            apointID=int(dlg.ApointID.GetValue()) 
            pressSet=ChangePressPara()   
            pressSet.PressMode=Mode
            pressSet.ApointID_l=apointID&0x00FF
            pressSet.ApointID_h=apointID>>8
            pressSet.PressNum=freqNum+1
            pressSet.SendWeak=int(dlg.sliderWeak.GetValue())
            pressSet.CommonHeader=FrameHeader(0x55,0xAF,0x0F,0)
            pressSet.CommonTail=self.tail
            pressSet.PressSignal=PressSignal+1
            if(PressSignal==2 or PressSignal==3):
                pressSet.PressSignalBandWidth=PressSignal
            else:
                pressSet.PressSignalBandWidth=PressSignal+1
            if(freqNum==0):
                pressSet.HighT1=oneFreqT1>>8
                pressSet.LowT1=oneFreqT1&0x00FF
                pressSet.HighT2=oneFreqT2>>8
                pressSet.LowT2= oneFreqT2&0x00FF   
                PressFreq1=float(dlg.textPressFreq1.GetValue())
                array1=self.FreqToByte(PressFreq1)
                pressSet.FreqArray[0]=CentreFreq(array1[0],array1[1],array1[2],array1[3]) 
                 
            else:
                pressSet.HighT1=twoFreqT1>>8
                pressSet.LowT1=twoFreqT1&0x00FF
                pressSet.HighT2=twoFreqT2>>8
                pressSet.LowT2= twoFreqT2&0x00FF
                pressSet.HighT3=twoFreqT3>>8
                pressSet.LowT3=twoFreqT3&0x00FF
                pressSet.HighT4=twoFreqT4>>8
                pressSet.LowT4=twoFreqT4&0x00FF 
        
                PressFreq1=float(dlg.textPressFreq1.GetValue())
                PressFreq2=float(dlg.textPressFreq2.GetValue())
                array1=self.FreqToByte(PressFreq1)
                array2=self.FreqToByte(PressFreq2)
                pressSet.FreqArray[0]=CentreFreq(array1[0],array1[1],array1[2],array1[3])    
                pressSet.FreqArray[1]=CentreFreq(array2[0],array2[1],array2[2],array2[3])
            
            self.outPoint.write(bytearray(pressSet))
            
             
        dlg.Destroy()
            
            

    #############指定终端历史功率谱文件请求#####################
    def OnSetSpecTime(self,event):
        dlg=AllDialog.SetSpecTimeDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            self.HistoryDataQuery(dlg, 0xAB)
        dlg.Destroy()
    
    def HistoryDataQuery(self,dlg,functionPara):
        Obj=ReqData()
        
        startTime=(int(dlg.StartTimeYear.GetValue()),int(dlg.StartTimeMonth.GetValue()),  \
                   int(dlg.StartTimeDay.GetValue()),int(dlg.StartTimeHour.GetValue()),    \
                   int(dlg.StartTimeMinute.GetValue())
                   )
        endTime=(int(dlg.EndTimeYear.GetValue()),int(dlg.EndTimeMonth.GetValue()),  \
                   int(dlg.EndTimeDay.GetValue()),int(dlg.EndTimeHour.GetValue()),    \
                   int(dlg.EndTimeMinute.GetValue())
                   )
        apointID=int(dlg.ApointID.GetValue())
        
        Obj.CommonHeader=FrameHeader(0x55,functionPara,0x0F,0)
        Obj.CommonTail=self.tail
        Obj.ApointID_h=apointID>>8
        Obj.ApointID_l=apointID&0x00FF
        Obj.StartTime=self.ByteToTime(startTime)
        Obj.EndTime=self.ByteToTime(endTime)
        
        frameLen=sizeof(Obj)
        self.serverCom.SendQueryData(frameLen,Obj)
        
  

    #############指定终端历史IQ数据请求######################
    def OnSetDemodTime(self,event):
        dlg=AllDialog.SetDemodTimeDialog()
        result=dlg.ShowModal()  
        if(result==wx.ID_OK):
            self.HistoryDataQuery(dlg, 0xAC)
        dlg.Destroy()


    ############窗口显示（解调的和正常应该显示的）#########
    
    def OnDemodDisplay(self,event):
        dlg=AllDialog.IQDisplaySetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            if(dlg.CtrlDemodWave.GetValue()): self.OnNewChild("Demod Wave")
            elif(dlg.CtrlDemodConstel.GetValue()):self.OnNewChild("Constel")
            elif(dlg.CtrlDemodEye.GetValue()): self.OnNewChild("Eye")
            elif(dlg.CtrlDemodCCDF.GetValue()):self.OnNewChild("CCDF")
            else:
                pass
        dlg.Destroy()

    def OnDisplayWindow(self,event):
        dlg=AllDialog.DisplaySetDialog()
        result=dlg.ShowModal()
        if(result==wx.ID_OK):
            if(dlg.CtrlSpec.GetValue()): self.OnNewChild("Spectrum")
            elif(dlg.CtrlWater.GetValue()):self.OnNewChild("WaterFall")
            elif(dlg.CtrlWave.GetValue()):self.OnNewChild("Wave")
            else:
                pass
        dlg.Destroy()
      
    
    def OnNewChild(self,string):
        
        global waveShow
        global specShow
        global waterShow
        global demodWaveShow
        global demodConstelShow
        global demodCCDFShow
        global demodEyeShow
        
        if(string=="Wave"): 
            if(not waveShow):
                self.WaveFrame=WaveIQ(self,"IQ Wave")
                self.WaveFrame.Show()
                self.Bind(wx.EVT_WINDOW_DESTROY,self.OnCloseWaveFrame,self.WaveFrame)
                self.Tile(wx.HORIZONTAL)
                waveShow=True
                self.threadRecv_drawIQ.WaveFrame=self.WaveFrame
                    
        elif(string=="Spectrum"):
            if(not specShow):
                self.SpecFrame=Spec(self)
                self.SpecFrame.Show()
                self.Bind(wx.EVT_WINDOW_DESTROY,self.OnCloseSpecFrame,self.SpecFrame)
                self.Tile(wx.HORIZONTAL)
                specShow=True
                    
        elif(string=="WaterFall"):
            if(not waterShow):
                self.WaterFrame=Water(self)
                self.WaterFrame.Show()
                self.Bind(wx.EVT_WINDOW_DESTROY,self.OnCloseWaterFrame,self.WaterFrame)
                self.Tile(wx.HORIZONTAL)
                waterShow=True
                self.threadRecv_drawFFT.WaterFrame=self.WaterFrame
        elif(string=="Demod Wave"):
            if(not demodWaveShow):
                self.DemodWaveFrame=WaveIQ(self,"Demod Wave")
                self.DemodWaveFrame.Show()
                self.Bind(wx.EVT_WINDOW_DESTROY,self.OnCloseDemodWaveFrame,self.DemodWaveFrame)
                self.Tile(wx.HORIZONTAL)
                demodWaveShow=True
        elif(string=="Constel"):
            if(not demodConstelShow):
                self.DemodConstelFrame=Constel(self)
                self.DemodConstelFrame.Show()
                self.Bind(wx.EVT_WINDOW_DESTROY,self.OnCloseDemodConstelFrame,self.DemodConstelFrame)
                self.Tile(wx.HORIZONTAL)
                demodConstelShow=True

        elif(string=="Eye"):
            if(not demodEyeShow):
                self.DemodEyeFrame=Eye(self)
                self.DemodEyeFrame.Show()
                self.Bind(wx.EVT_WINDOW_DESTROY,self.OnCloseDemodEyeFrame,self.DemodEyeFrame)
                self.Tile(wx.HORIZONTAL)
                demodEyeShow=True

        elif(string=="CCDF"):
            if(not demodCCDFShow):
                self.DemodCCDFFrame=CCDF(self)
                self.DemodCCDFFrame.Show()
                self.Bind(wx.EVT_WINDOW_DESTROY,self.OnCloseDemodCCDFFrame,self.DemodCCDFFrame)
                self.Tile(wx.HORIZONTAL)
                demodCCDFShow=True

        

            
if __name__=="__main__":
    app=wx.App()
    main_frame=MainWindow()
    main_frame.Show()
    app.MainLoop()

os._exit(1)
           
