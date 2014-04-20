# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 13:04:36 2014

@author: Sukhbinder Singh



"""
import wx
import vtk
import sys
import os
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from numpy import genfromtxt,size,array,savetxt

class icpdata():
      def __init__(self):
          self.source = None
          self.target = None
          self.transformed = None
          self.iteration =200
          self.icp= vtk.vtkIterativeClosestPointTransform()
          self.icptf = vtk.vtkTransformPolyDataFilter()
          self.mappers =vtk.vtkPolyDataMapper()
          self.mappert =vtk.vtkPolyDataMapper()
          self.mappertf =vtk.vtkPolyDataMapper()
          self.actors = vtk.vtkActor()
          self.actort = vtk.vtkActor()
          self.actortf = vtk.vtkActor()
          self.centroidon= False
      
      def reset(self):
          self.source=None
          self.target= None
          self.transformed=None

      def saveData(self,filename):
          if (self.transformed is not None):
              data=[]
              b=self.transformed.GetPoints()
              for i in range(0,b.GetNumberOfPoints()):
                  point= b.GetPoint(i)
                  data.append(point)
              data = array(data)
              savetxt(filename, data, fmt='%.16f %.16f %.16f')
              data=None
              b=None
                      
      def loaddata(self,filename,isSource=True):
          data = genfromtxt(filename,dtype=float,skiprows=2,usecols=[0,1,2])
          if isSource:
              sourcePoints = vtk.vtkPoints()
              sourceVertices = vtk.vtkCellArray()
              for k in xrange(size(data,0)):
                  point = data[k] 
                  id = sourcePoints.InsertNextPoint(point)
                  sourceVertices.InsertNextCell(1)
                  sourceVertices.InsertCellPoint(id)
              self.source = vtk.vtkPolyData()              
              self.source.SetPoints(sourcePoints)
              self.source.SetVerts(sourceVertices)
          else:
               targetPoints = vtk.vtkPoints()
               targetVertices = vtk.vtkCellArray()
               for k in xrange(size(data,0)):
                   point = data[k] 
                   id = targetPoints.InsertNextPoint(point)
                   targetVertices.InsertNextCell(1)
                   targetVertices.InsertCellPoint(id)
               self.target = vtk.vtkPolyData()               
               self.target.SetPoints(targetPoints)
               self.target.SetVerts(targetVertices)

      def PerformICP(self):
           if (self.source is not None or self.target is not None):
               self.icp.SetSource(self.source)
               self.icp.SetTarget(self.target)
               self.icp.GetLandmarkTransform().SetModeToRigidBody()
           #icp.DebugOn()
               self.icp.SetMaximumNumberOfIterations(200)
               if self.centroidon:
                   self.icp.StartByMatchingCentroidsOn()
               self.icp.Modified()
               self.icp.Update()
 
               self.icptf.SetInput(self.source)
 
               self.icptf.SetTransform(self.icp)
               self.icptf.Update()
 
               self.transformed = self.icptf.GetOutput()
           #print icp
           
class EventsHandler(object):

    def __init__(self, parent):
        self.parent = parent

    # Exit Menu
    def onExit(self, event):
        self.parent.Destroy()
    # Change Background
    def onBackgroundColor(self, event):
        dlg = wx.ColourDialog(self.parent)
        dlg.GetColourData().SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            dlg.Destroy()
            self.SetColor(data.GetColour().Get())
            return
        dlg.Destroy()

    def SetColor(self, bkgColor):
        """
        @warning if the model is not loaded and the color is not "clicked"
        on, then rend will return None
        """
        rend = self.parent.vtkPanel.renderer
        if not rend:  # rend doesnt exist at first
            print 'Try again to change the color (you didnt "click" on the color; one time bug)'
            return
            rend = self.parent.vtkPanel.renderer
        ## bkgColor range from 0 to 255
        ## color ranges from 0 to 1
        color = [bkgColor[0] / 255., bkgColor[1] / 255., bkgColor[2] / 255.]
        rend.SetBackground(color)
        self.parent.vtkPanel.widget.Render()
    
	# StatusBar Toggle
    def onToggleStatusBar(self, e):
        if self.parent.isstatusbar:
                self.parent.statusbar.Hide()
                self.parent.isstatusbar = False
        else:
            self.parent.statusbar.Show()
            self.parent.isstatusbar = True

	# ToolBar Toggle
    def onToggleToolBar(self, e):
        if self.parent.istoolbar:
            self.parent.toolbar1.Hide()
            self.parent.istoolbar= False
        else:
            self.parent.toolbar1.Show()
            self.parent.istoolbar= True

    # Help Menu About
	# Change the list name
    def onAbout(self, event):
        about = [
            'ICP ' ,
            'Copyright Sukhbinder Singh 2014 \n' ,
            'Developed in January 2013',
            '',
            'www.sukhbindersingh.com',
            '',
            'Keyboard Controls',
            '',
            'R   - Fit the model',
            'F   - Zoom the moDEL',
            'S   - surface',
            'W   - wireframe',
        ]

        dlg = wx.MessageDialog(None, '\n'.join(about), 'About',
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
		
#   Add your events HERE


 # End of EventsHandler
 
 
class vtkPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self, parent)
        
# To interact with the scene using the mouse use an instance of vtkRenderWindowInteractor. 
        self.widget = wxVTKRenderWindowInteractor(self, -1)
        self.parent= parent
        self.widget.Enable(1)
        self.widget.AddObserver("ExitEvent", lambda o,e,f=self: f.Close())
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.widget, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.1, 0.2, 0.4)
        self.widget.GetRenderWindow().AddRenderer(self.renderer)
        self.Layout()
        self.widget.Render()
        self.filename=None
        self.isploted = False
        self.plot(self)
    
            
    def onTakePicture(self, event):
        renderLarge = vtk.vtkRenderLargeImage()
        renderLarge.SetInput(self.renderer)
        renderLarge.SetMagnification(4)

        wildcard = "PNG (*.png)|*.png|" \
            "JPEG (*.jpeg; *.jpeg; *.jpg; *.jfif)|*.jpg;*.jpeg;*.jpg;*.jfif|" \
            "TIFF (*.tif; *.tiff)|*.tif;*.tiff|" \
            "BMP (*.bmp)|*.bmp|" \
            "PostScript (*.ps)|*.ps|" \
            "All files (*.*)|*.*"

        dlg = wx.FileDialog(None, "Choose a file", "",
                            "", wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            fname = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            fname = os.path.join(self.dirname, fname)
            # We write out the image which causes the rendering to occur. If you
            # watch your screen you might see the pieces being rendered right
            # after one another.
            lfname = fname.lower()
            if lfname.endswith('.png'):
                writer = vtk.vtkPNGWriter()
            elif lfname.endswith('.jpeg'):
                writer = vtk.vtkJPEGWriter()
            elif lfname.endswith('.tiff'):
                writer = vtk.vtkTIFFWriter()
            elif lfname.endswith('.ps'):
                writer = vtk.vtkPostScriptWriter()
            else:
                writer = vtk.vtkPNGWriter()

            writer.SetInputConnection(renderLarge.GetOutputPort())
            writer.SetFileName(fname)
            writer.Write()
        dlg.Destroy()

# Write your VTK panel methods here
    def onLoadSource(self, event):
        filename=""
        openFileDialog = wx.FileDialog(self, "Open Source file", "", filename,
                                       "*.item", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
            
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        filename = openFileDialog.GetPath()
        self.parent.icpd.loaddata(filename,isSource=True)
        self.plot(self)
#
    def onLoadTarget(self, event):
        filename=""
        openFileDialog = wx.FileDialog(self, "Open Source file", "", filename,
                                       "*.item", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
            
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return
        filename = openFileDialog.GetPath()
        self.parent.icpd.loaddata(filename,isSource=False)
        self.plot(self)
#
    def onPerform(self, event):
        self.parent.icpd.PerformICP()        
        self.plot(self)

    def onSavedata(self,event):
        if(self.parent.icpd.transformed is not None):
            wildcard = "TXT (*.txt)|*.txt|" \
            "All files (*.*)|*.*"

            dlg = wx.FileDialog(None, "Choose a file", "",
                            "", wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                fname = dlg.GetFilename()
                dirname = dlg.GetDirectory()
                fname = os.path.join(dirname, fname)
                self.parent.icpd.saveData(fname)

    
    
    def onReset(self,event):
        self.parent.icpd.reset()
        actors = self.renderer.GetActors()
        numActors = actors.GetNumberOfItems()
        actors.InitTraversal()
        for i in xrange(0, numActors):
             actor = actors.GetNextItem()
             self.renderer.RemoveActor(actor)
        self.plot(self)
        
    def plot(self,event):
        self.renderthis()
          
    def renderthis(self):
            # open a window and create a renderer            
            if (self.parent.icpd.transformed is not None):            
                self.parent.icpd.mappertf.SetInput(self.parent.icpd.transformed)
                self.parent.icpd.actortf.SetMapper(self.parent.icpd.mappertf)
                self.parent.icpd.actortf.GetProperty().SetColor(1,0,0) # (R,G,B)    # Red
                self.parent.icpd.actortf.GetProperty().SetPointSize(3)
                self.renderer.AddActor(self.parent.icpd.actortf)

            if (self.parent.icpd.source is not None): 
                self.parent.icpd.mappers.SetInput(self.parent.icpd.source)
                self.parent.icpd.actors.SetMapper(self.parent.icpd.mappers)          
                self.parent.icpd.actors.GetProperty().SetColor(0,1,0) # (R,G,B)   #source
                self.parent.icpd.actors.GetProperty().SetPointSize(3)
                self.renderer.AddActor(self.parent.icpd.actors)


            if (self.parent.icpd.target is not None): 
                self.parent.icpd.mappert.SetInput(self.parent.icpd.target)
                self.parent.icpd.actort.SetMapper(self.parent.icpd.mappert)
                self.parent.icpd.actort.GetProperty().SetColor(0,0,1) # (R,G,B)   #
                self.parent.icpd.actort.GetProperty().SetPointSize(3)
                self.renderer.AddActor(self.parent.icpd.actort)

            if not self.isploted:
                axes = vtk.vtkAxesActor()
                self.marker = vtk.vtkOrientationMarkerWidget()
                self.marker.SetInteractor( self.widget._Iren )
                self.marker.SetOrientationMarker( axes )
                self.marker.SetViewport(0.75,0,1,0.25)
                self.marker.SetEnabled(1)
            self.renderer.ResetCamera()
            self.renderer.ResetCameraClippingRange()
            #cam = self.renderer.GetActiveCamera()
            #cam.Elevation(10)
            #cam.Azimuth(70)
            self.isploted = True
            self.renderer.Render()
# End of vtkPanel form

		
class AppFrame(wx.Frame):
    def __init__(self,parent,title,iconpath):
        wx.Frame.__init__(self,parent,title=title,size=(800,600))
        self.title=title
        self.icpd = icpdata()
        self.iconPath=iconpath
        self.SetupFrame()        
  
    def settingTitle(self):
             self.SetTitle(self.title+self.vtkPanel.filename)
            
    def Createstatusbar(self):
            self.statusbar = self.CreateStatusBar()
            self.statusbar.SetStatusText("Ready")
            self.isstatusbar = True
            
    def buildToolBar(self):
            self.istoolbar = True            
            events = self.eventsHandler 
            toolbar1 = self.CreateToolBar()
    
            topen = wx.Image(os.path.join(self.iconPath, 'topen.png'), wx.BITMAP_TYPE_ANY)
            topen = toolbar1.AddLabelTool(1, '', wx.BitmapFromImage(topen), longHelp='Loads Source Coords')

            topen2 = wx.Image(os.path.join(self.iconPath, 'topen.png'), wx.BITMAP_TYPE_ANY)
            topen2 = toolbar1.AddLabelTool(2, '', wx.BitmapFromImage(topen2), longHelp='Loads Target Coords')
            
            topen3 = wx.Image(os.path.join(self.iconPath, 'bookmarks.png'), wx.BITMAP_TYPE_ANY)
            topen3 = toolbar1.AddLabelTool(3, '', wx.BitmapFromImage(topen3), longHelp='Perform ICP')
            
            tcamera1 = wx.Image(os.path.join(self.iconPath, 'array.png'), wx.BITMAP_TYPE_ANY)
            camera1 = toolbar1.AddLabelTool(5, '', wx.BitmapFromImage(tcamera1), longHelp='New Session')
            
            tsave1 = wx.Image(os.path.join(self.iconPath, 'filesave.png'), wx.BITMAP_TYPE_ANY)
            tsave1 = toolbar1.AddLabelTool(5, '', wx.BitmapFromImage(tsave1), longHelp='Save transformed data')
            
            
            tcamera = wx.Image(os.path.join(self.iconPath, 'tcamera.png'), wx.BITMAP_TYPE_ANY)
            camera = toolbar1.AddLabelTool(4, '', wx.BitmapFromImage(tcamera), longHelp='Take a Screenshot')

            texit = wx.Image(os.path.join(self.iconPath, 'texit.png'), wx.BITMAP_TYPE_ANY)
            etool = toolbar1.AddLabelTool(wx.ID_EXIT, '', wx.BitmapFromImage(texit), longHelp='Exit App')
            
            toolbar1.Realize()

            self.toolbar1 = toolbar1

# Bind  Toolbar items
            self.Bind(wx.EVT_TOOL, events.onExit, id=wx.ID_EXIT)            
            self.Bind(wx.EVT_TOOL, self.vtkPanel.onTakePicture, id=camera.GetId())
            self.Bind(wx.EVT_TOOL, self.vtkPanel.onLoadSource, id=topen.GetId())
            self.Bind(wx.EVT_TOOL, self.vtkPanel.onLoadTarget, id=topen2.GetId())
            self.Bind(wx.EVT_TOOL, self.vtkPanel.onPerform, id=topen3.GetId())
            self.Bind(wx.EVT_TOOL, self.vtkPanel.onReset, id=camera1.GetId())
            self.Bind(wx.EVT_TOOL, self.vtkPanel.onSavedata, id=tsave1.GetId())
            
            
    def buildMenuBar(self):
            events = self.eventsHandler
            menubar = wx.MenuBar()
 # --------- File Menu -------------------------------------------------
            fileMenu = wx.Menu()
            nsesl = fileMenu.Append(wx.ID_ANY,'New &Session','New Session')
            nsesl.SetBitmap(wx.Image(os.path.join(self.iconPath,'array.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
            fileMenu.AppendSeparator()
             
            loadModel = fileMenu.Append(wx.ID_ANY,'Load &Source','Loads a Source Input File')
            loadModel.SetBitmap(wx.Image(os.path.join(self.iconPath,'topen.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

            loadMode2 = fileMenu.Append(wx.ID_ANY,'Load &Target','Loads a Target Input File')
            loadMode2.SetBitmap(wx.Image(os.path.join(self.iconPath,'topen.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

            fileMenu.AppendSeparator()

            picp2 = fileMenu.Append(wx.ID_ANY,'Perform &ICP','Perform ICP')
            picp2.SetBitmap(wx.Image(os.path.join(self.iconPath,'bookmarks.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
            
            picp3 = fileMenu.Append(wx.ID_ANY,'Save &Data','Save Transformed Data')
            picp3.SetBitmap(wx.Image(os.path.join(self.iconPath,'filesave.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())            
            
            fileMenu.AppendSeparator()
# ---------     ------------------------------------------------------------
            exitButton = wx.MenuItem(fileMenu,wx.ID_EXIT, 'Exit', 'Exits App')
            exitButton.SetBitmap(wx.Image(os.path.join(self.iconPath, 'texit.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap())
            fileMenu.AppendItem(exitButton)

        # --------- View Menu -------------------------------------------------
# status bar at bottom - toggles
            viewMenu = wx.Menu()
            camera = viewMenu.Append(wx.ID_ANY,'Take a Screenshot','Take a Screenshot')
            camera.SetBitmap(wx.Image(os.path.join(self.iconPath, 'tcamera.png'),wx.BITMAP_TYPE_PNG).ConvertToBitmap())
#
            viewMenu.AppendSeparator()          
            self.showStatusBar = viewMenu.Append(wx.ID_ANY, 'Show/Hide Statusbar','Show Statusbar')
            self.showToolBar   = viewMenu.Append(wx.ID_ANY, 'Show/Hide Toolbar','Show Toolbar')
            viewMenu.AppendSeparator()                      
            self.bkgColorView = viewMenu.Append(wx.ID_ANY,'Change Background Color','Change Background Color')                                         

# --------- Help / About Menu -----------------------------------------
            helpMenu = wx.Menu()
            self.helpM = helpMenu.Append(wx.ID_ANY, '&About', 'About App')
# menu bar
            menubar.Append(fileMenu, '&File')
            menubar.Append(viewMenu, '&View')
            menubar.Append(helpMenu, '&Help')
            self.menubar = menubar
            self.SetMenuBar(menubar)
#
# Bind all menubar events
#
            self.Bind(wx.EVT_MENU, events.onExit, id=wx.ID_EXIT)
            self.Bind(wx.EVT_MENU, events.onBackgroundColor, id=self.bkgColorView.GetId())
            self.Bind(wx.EVT_MENU, events.onToggleStatusBar, id=self.showStatusBar.GetId())
            self.Bind(wx.EVT_MENU, events.onToggleToolBar, id=self.showToolBar.GetId())
            self.Bind(wx.EVT_MENU, events.onAbout, id=self.helpM.GetId())           
            self.Bind(wx.EVT_MENU, self.vtkPanel.onLoadSource, id=loadModel.GetId())
            self.Bind(wx.EVT_MENU, self.vtkPanel.onLoadTarget, id=loadMode2.GetId())
            self.Bind(wx.EVT_MENU, self.vtkPanel.onPerform, id=picp2.GetId())
            self.Bind(wx.EVT_MENU, self.vtkPanel.onReset, id=nsesl.GetId())
            self.Bind(wx.EVT_MENU, self.vtkPanel.onSavedata, id=picp3.GetId())
            
    def SetupFrame(self):
            self.eventsHandler = EventsHandler(self)
            self.vtkPanel = vtkPanel(self)
            self.buildMenuBar()
            self.buildToolBar()
            self.Createstatusbar()
# End of Main APP

def Main():
	appPath = sys.path[0]   
	iconPath=os.path.join(appPath,'icons')
	app = wx.App(redirect=False)
	frame = AppFrame(None,"VTK STL viewer : ",iconPath)
	frame.Show()
	app.MainLoop()
if __name__ == "__main__": 
     Main()
