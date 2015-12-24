# -*- coding: utf-8 -*-
import wx
from numpy import array, linspace
import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas 
from DragMarker import DraggableRectangle

class Spec(wx.MDIChildFrame):
    def __init__(self,parent):
        wx.MDIChildFrame.__init__(self,parent,-1,title="Spectrum")
        topSplitter = wx.SplitterWindow(self)
        hSplitter = wx.SplitterWindow(topSplitter)

        self.panelAbFreq = MyListCtrlAbFreq(hSplitter)
        self.panelQuery = MyListCtrlQuery(hSplitter)
        hSplitter.SplitHorizontally(self.panelAbFreq, self.panelQuery)
        hSplitter.SetSashGravity(0.35)

        self.panelFigure = PanelSpec(topSplitter,parent)
        topSplitter.SplitVertically(self.panelFigure, hSplitter)
        topSplitter.SetSashGravity(0.8)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(topSplitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

        
class MyListCtrlAbFreq(wx.ListCtrl):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
        self.InsertColumn(0, u'序号')
        self.InsertColumn(1, u'异常频点频率(MHz)')
        self.InsertColumn(2, u'异常频点功率(dB)')
        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 120)
        self.SetColumnWidth(2, 130)
        for i in range(1,11):
            self.InsertStringItem(i-1,str(i))

class MyListCtrlQuery(wx.ListCtrl):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
        self.InsertColumn(0, u"帧类型")
        self.InsertColumn(1, u'参数类型')
        self.InsertColumn(2, u'参数值')
        self.SetColumnWidth(0, 100)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 100)
        for i in range(1,5301):
            self.InsertStringItem(i-1,str(i))

    
class PanelSpec(wx.Panel):
    def __init__(self,parent,parentMainFrame):
        wx.Panel.__init__(self,parent)
        self.CreatePanel()
        self.setSpLabel()
        self.parent=parentMainFrame 
        self.FFT_Max_X=5995
        self.FFT_Min_X=70
        self.FFT_Max_Y=60
        self.FFT_Min_Y=-120 

    def CreatePanel(self):
        self.Figure = matplotlib.figure.Figure()
        self.axes=self.Figure.add_axes([0.05,0.05,0.93,0.93])
        self.FigureCanvas = FigureCanvas(self,-1,self.Figure)
        self.ButtonAutoY=wx.Button(self,-1,label="AutoScaleY")
        self.ButtonAutoX=wx.Button(self,-1,label="AutoScaleX")
        self.Max_Y=wx.TextCtrl(self,-1,'60',size=(60,20),style=wx.TE_PROCESS_ENTER)
        self.Min_Y=wx.TextCtrl(self,-1,'-120',size=(60,20),style=wx.TE_PROCESS_ENTER)
        self.Min_X=wx.TextCtrl(self,-1,'70',size=(60,20),style=wx.TE_PROCESS_ENTER)
        self.Max_X=wx.TextCtrl(self,-1,'5995',size=(60,20),style=wx.TE_PROCESS_ENTER)
        sizer = wx.GridBagSizer(5,5)
                
        sizer.Add(self.ButtonAutoX,pos=(0,1),flag=wx.TOP,border=5)
        sizer.Add(self.ButtonAutoY,pos=(0,2),flag=wx.TOP,border=5)
        sizer.Add(self.Max_Y,pos=(1,0),flag=wx.ALL,border=5)
        sizer.Add(self.Min_Y,pos=(17,0),flag=wx.ALL,border=5)
        sizer.Add(self.FigureCanvas,pos=(1,1),span=(18,14),flag=wx.EXPAND)
        sizer.Add(self.Min_X,pos=(19,1),flag=wx.RIGHT|wx.BOTTOM,border=5)
        sizer.Add(self.Max_X,pos=(19,14),flag=wx.BOTTOM,border=5)

        sizer.AddGrowableCol(10)
        sizer.AddGrowableRow(10)       
        self.SetSizer(sizer)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterMin_X,self.Min_X)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterMax_X,self.Max_X)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterMax_Y,self.Max_Y)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterMin_Y,self.Min_Y)
        self.Bind(wx.EVT_BUTTON,self.OnAutoX,self.ButtonAutoX)
        self.Bind(wx.EVT_BUTTON,self.OnAutoY,self.ButtonAutoY)
        
        self.popupmenu=wx.Menu()
        StringList=["Add Marker","Remove Marker", "All Marker Off"]
        for text in StringList:
            item=self.popupmenu.Append(-1,text)
            self.FigureCanvas.Bind(wx.EVT_CONTEXT_MENU,self.OnShowPopup)
            self.FigureCanvas.Bind(wx.EVT_MENU,self.OnPopupItemSelected,item)

        Array=linspace(70, 5995,238)
        xDataList=[]
        self.LineSpec=[]
        self.LineSpecBack=[]
        for i in xrange(237):
            xData=linspace(Array[i],Array[i+1],1024)
            xDataList.append(xData)
        
        ydata=[0]*1024
        for xData in xDataList:
            lineSpec,=self.axes.plot(xData,ydata,'y')
            lineSpecBack,=self.axes.plot(xData,ydata,'r')
            self.LineSpec.append(lineSpec)
            self.LineSpecBack.append(lineSpecBack)

        ####Marker############
        self.drs=[]

    def OnAutoX(self,event):
        self.setSpLabel(begin_X=self.parent.FreqMin,end_X=self.parent.FreqMax , \
            begin_Y=self.FFT_Min_Y,end_Y=self.FFT_Max_Y)
        self.FigureCanvas.draw()
        self.FFT_Min_X=self.parent.FreqMin
        self.FFT_Max_X=self.parent.FreqMax
        self.Min_X.SetValue(str(self.FFT_Min_X))
        self.Max_X.SetValue(str(self.FFT_Max_X))

    def OnAutoY(self,event):
        self.setSpLabel(begin_X=self.FFT_Min_X,end_X=self.FFT_Max_X)
        self.FigureCanvas.draw()
        self.FFT_Min_Y=-120
        self.FFT_Max_Y=60
        self.Min_Y.SetValue("-120")
        self.Max_Y.SetValue("60")

    def OnEnterMin_X(self,event):
        self.FFT_Min_X=int(self.Min_X.GetValue())
        self.setSpLabel(self.FFT_Min_X,self.FFT_Max_X,self.FFT_Min_Y,self.FFT_Max_Y)
        self.FigureCanvas.draw()

    def OnEnterMax_X(self,event):
        self.FFT_Max_X=int(self.Max_X.GetValue())
        self.setSpLabel(self.FFT_Min_X,self.FFT_Max_X,self.FFT_Min_Y,self.FFT_Max_Y)
        self.FigureCanvas.draw()

    def OnEnterMin_Y(self,event):
        self.FFT_Min_Y=int(self.Min_Y.GetValue())
        self.setSpLabel(self.FFT_Min_X,self.FFT_Max_X,self.FFT_Min_Y,self.FFT_Max_Y)
        self.FigureCanvas.draw()

    def OnEnterMax_Y(self,event):
        self.FFT_Max_Y=int(self.Max_Y.GetValue())
        self.setSpLabel(self.FFT_Min_X,self.FFT_Max_X,self.FFT_Min_Y,self.FFT_Max_Y)
        self.FigureCanvas.draw()
    
    def OnShowPopup(self,event):
        pos=event.GetPosition()
        pos=self.FigureCanvas.ScreenToClient(pos)
        self.FigureCanvas.PopupMenu(self.popupmenu,pos)

    def OnPopupItemSelected(self,event):
        item=self.popupmenu.FindItemById(event.GetId())
        text=item.GetText()
        if(text=="Add Marker"):
            self.OnAddMarker()  
        elif(text=="Remove Marker"):
            self.OnRemove()
        elif(text=="All Marker Off"):
            self.OnAllRemove()
    
    def DrawMarker(self,Max_X,Max_Y):
        distance=((self.FFT_Max_X-self.FFT_Min_X)/10)**2
        index=len(self.drs)+1
        rect,=self.axes.plot(Max_X,Max_Y,'rd',markersize=10)
        text=self.axes.text(Max_X+5,Max_Y+2,'M'+str(index),color='r')
        textM=self.axes.text(self.FFT_Min_X+5,self.FFT_Max_Y-5*(index),'M'+str(index)+':'  \
            +'%.2f'%(Max_X)+'MHz  '+'%.2f'%(Max_Y)+'dBm')
        DragRect=DraggableRectangle(rect,text,textM,self.LineSpec,self.FigureCanvas)
        DragRect.setM_id('M'+str(index)+':')
        
        DragRect.setRadius(distance)
        DragRect.connect()
        self.drs.append(DragRect)
        #self.FigureCanvas.draw()
 
    def OnAddMarker(self):
        if(len(self.drs)<4):
            startSection=(self.FFT_Min_X-70)/25 
            endSection=(self.FFT_Max_X-70)/25
            indexStart=int((self.FFT_Min_X-(startSection*25+70))*1024.0/25)
            indexEnd=int((self.FFT_Max_X-(endSection*25+70))*1024.0/25)
            MaxList=[]
            MaxList.append(max(list(self.LineSpec[startSection].get_ydata())[indexStart:1024]))
            for i in range(startSection+1,endSection,1):
                MaxList.append(max(list(self.LineSpec[i].get_ydata())))
            if(indexEnd!=0):
                MaxList.append(max(list(self.LineSpec[endSection].get_ydata())[0:indexEnd]))
                
            Max_Y=max(MaxList)
            Max_Y_Index=MaxList.index(Max_Y)+startSection 
            Max_X_Index=list(self.LineSpec[Max_Y_Index].get_ydata()).index(Max_Y)
            Max_X=70+Max_Y_Index*25+Max_X_Index*25.0/1024 
            self.DrawMarker(Max_X,Max_Y)


    def OnRemove(self):
        
        if(len(self.axes.texts)):
            self.axes.lines.pop()
            self.axes.texts.pop()
            self.axes.texts.pop()
            self.drs.pop()
            #self.FigureCanvas.draw()

    def OnAllRemove(self):
       
        while(len(self.axes.texts)):
            self.axes.lines.pop()
            self.axes.texts.pop()
            self.axes.texts.pop()
            self.drs.pop()
        #self.FigureCanvas.draw()



    def setSpLabel(self, begin_X=70, end_X=5995,begin_Y=-120,end_Y=60): 
        self.ylabel('dBm')
        self.xlabel('MHz')
        self.ylim(begin_Y,end_Y)
        self.xlim(begin_X,end_X)
        yticks=linspace(begin_Y,end_Y,15)
        yticklabels = [str(int(i)) for i in yticks]  
        xticks=linspace(begin_X,end_X,15)

        xticklabels = [str(int(i)) for i in xticks]
        self.axes.set_xticks(xticks)
        self.axes.set_xticklabels(xticklabels,rotation=0)
        self.axes.set_yticks(yticks)
        self.axes.set_yticklabels(yticklabels,rotation=0)
        self.axes.grid(True)


    def PowerSpectrum(self, y,funcPara,curSectionNo):
       
        if(funcPara==0x0D):
            self.LineSpec[curSectionNo-1].set_ydata(array(y))
            for i in range(len(self.drs)):
                self.drs[i].yData=self.LineSpec 
                self.DrawAfterRelease()
        elif(funcPara==0x1D):
            self.LineSpecBack[curSectionNo-1].set_ydata(array(y))
        self.FigureCanvas.draw()
                
    def DrawAfterRelease(self):
        
        for i in range(len(self.drs)):
            xData=self.drs[i].rect.get_xdata()

            index=(int(xData)-70)/25
            Section=index*25+70
            index_Y=(xData-Section)*1024.0/25
            Marker_Y=list(self.LineSpec[index].get_ydata())[int(index_Y)]
            self.drs[i].rect.set_ydata(Marker_Y)
            self.drs[i].textMarker.set_position((xData,Marker_Y+2))
            self.drs[i].textM.set_text(self.drs[i].M_index+'%.2f'%(xData)+ \
                'MHz  '+'%.2f'%(Marker_Y)+'dBm')
      

    def xlim(self,x_min,x_max):  
        self.axes.set_xlim(x_min,x_max)  
  
  
    def ylim(self,y_min,y_max):  
        self.axes.set_ylim(y_min,y_max)

    def xlabel(self,XabelString="X"):   
        self.axes.set_xlabel(XabelString)  
  
  
    def ylabel(self,YabelString="Y"):  
        self.axes.set_ylabel(YabelString)
            
