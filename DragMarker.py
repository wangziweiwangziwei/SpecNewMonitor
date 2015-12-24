
class DraggableRectangle:
    lock = None  # only one can be animated at a time
    def __init__(self, rect,textMarker,textM,yData,canvas):
        self.rect = rect
        self.yData=yData
        self.textMarker=textMarker
        self.canvas=canvas
        self.press = None
        self.background = None
        self.radius=0
        self.textM=textM
        self.M_index=""
    def setM_id(self,index):
        self.M_index=index
    def setRadius(self,radius):
        self.radius=radius

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)
    def on_press(self, event):
        if event.inaxes != self.rect.axes: return
        if DraggableRectangle.lock is not None: return
        if((self.rect.get_xdata()-event.xdata)**2
            +(self.rect.get_ydata()-event.ydata)**2>self.radius):return
        (x0, y0) = self.rect.get_data()
        (x1, y1) = self.textMarker.get_position()
        self.press1 = x0, y0, event.xdata, event.ydata
        self.press2 = x1, y1
        DraggableRectangle.lock = self

        # draw everything but the selected rectangle and store the pixel buffer
        '''
        axes = self.rect.axes
        
        self.rect.set_animated(True)
        self.textMarker.set_animated(True)
        self.textM.set_animated(True)
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.rect.axes.bbox)

        # now redraw just the rectangle
        axes.draw_artist(self.rect)
        axes.draw_artist(self.textMarker)
        axes.draw_artist(self.textM)

        # and blit just the redrawn area
        self.canvas.blit(axes.bbox)
        '''
    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over us'
        if DraggableRectangle.lock is not self:
            return
        if event.inaxes != self.rect.axes: return
        x0, y0, xpress, ypress = self.press1
        x1, y1= self.press2
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        self.rect.set_xdata(x0+dx)
        index=(int(event.xdata)-70)/25
        Section=index*25+70
        index_Y=(event.xdata-Section)*1024.0/25
        Marker_Y=list(self.yData[index].get_ydata())[int(index_Y)]
        self.rect.set_ydata(Marker_Y)
        self.textMarker.set_position((x1+dx,Marker_Y+2))
        self.textM.set_text(self.M_index+'%.2f'%((x0+dx))+'MHz  '+'%.2f'%(Marker_Y)+'dBFS')
      
        # restore the background region
        '''
        self.canvas.restore_region(self.background)
        
        # redraw just the current rectangle
        axes.draw_artist(self.rect)
        axes.draw_artist(self.textMarker)
        axes.draw_artist(self.textM)
        # blit just the redrawn area
        #self.canvas.blit(axes.bbox)
        '''
    def on_release(self, event):
        'on release we reset the press data'
        if DraggableRectangle.lock is not self:
            return

        self.press1 = None
        self.press2 = None
        DraggableRectangle.lock = None

      
        # turn off the rect animation property and reset the background
        '''
        self.rect.set_animated(False)
        self.textMarker.set_animated(False)
        self.textM.set_animated(False)
        self.background = None
        # redraw the full figure

        self.canvas.draw()
        '''

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.canvas.mpl_disconnect(self.cidpress)
        self.canvas.mpl_disconnect(self.cidrelease)
        self.canvas.mpl_disconnect(self.cidmotion)

