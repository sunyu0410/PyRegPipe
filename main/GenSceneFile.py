import os
import sys
# Add the code folder to the path
topFolder = os.path.abspath(os.path.join(sys.executable, *([os.pardir]*4)))
sys.path.append(os.path.join(topFolder, 'code'))

from __main__ import vtk, qt, ctk, slicer

def path(*parts):
    return os.path.abspath(os.path.join(*parts))

class GenSceneFile:
    def __init__(self, parent):
        parent.title = 'Scene: Auto Generate File'
        parent.categories = ['BiRT']
        parent.dependencies = []
        parent.contributors = ['Yu Sun']
        parent.helpText = '''
        This is a module for generating the Slicer scene file after the registration.
        '''
        parent.acknowledgementText = '''
        Acknowledge for everyone who has taught me Python, registration and other techniques. Most of what I learnt comes from people around me, books and the Internet.
        '''
        self.parent = parent
        
class GenSceneFileWidget:
    def __init__(self, parent=None):
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()
        if not parent:
            self.setup()
            self.parent.show()
            
    def setup(self):
        self.clp, self.formLayout, self.formFrame = self.createClp(
                            'Scene: Auto Generate Files', self.layout, qt.QVBoxLayout())

        # Variables
        self.dataDir = None

        self.folders = {
            'hist': 'histology_to_exvivo', 
            'invivo': 'invivo_to_exvivo'
        }

        self.labelmaps = ['(in_3d_contour)_into_(ex_3d_cropped)_deformable', 
                    'annotation_mask', 'contour', 'ex_2d_contour', 'ex_3d_contour']
        
        self.interpOff = ['histology', 'annotation', 'cell_density_maps', 
                        '(in_dce_gd)_into_(ex_3d_cropped)_deformable']
        
        self.colourMaps = {
            'cell_density_maps': 'vtkMRMLColorTableNodeFileColdToHotRainbow.txt',
            '(pet)_into_(ex_3d_cropped)_deformable': 'vtkMRMLPETProceduralColorNodePET-Rainbow'
        }

        self.windows = ['Red', 'Yellow', 'Green'] 
        
        # Objects to hold the widgets
        self.labels = {}
        self.buttons = {}
        self.textareas = {}

        # Paths
        self.topFolder = os.path.abspath(os.path.join(sys.executable, *([os.pardir]*4)))

        # Project folder
        self.labels['lPrj'] = self.createLabel("Registration Result Folder", 
                    self.formFrame.layout(), 'Path to the result folder')
        self.labels['vPrj'] = self.createLabel("", 
                    self.formFrame.layout(), 'Selected result folder')

        # Select the result folder
        self.buttons['selFolder'] = self.createBtn('Select Folder', self.selFolder, 
                                              self.formFrame.layout())
        # Generate the scene file
        self.buttons['genFile'] = self.createBtn('Generate Scene File', self.genFile, 
                                              self.formFrame.layout())

        print('Setup done')

    def selFolder(self):
        dataDir = self.getPath()
        self.labels['vPrj'].text = dataDir
        self.preScene(dataDir)

    def preScene(self, dataDir):
        volumes = self.loadData(dataDir, self.folders)
        assert all([self.setInterp(volumes[i], False) for i in self.interpOff])
        assert all([self.setColourMap(volumes[i], self.colourMaps[i]) \
                            for i in self.colourMaps if i in volumes])
        assert all([self.autoAdjWind(volumes[i]) for i in volumes if i not in self.labelmaps])

        fg = volumes['(in_2d)_into_(ex_3d_cropped)_deformable']
        bg = volumes['histology']
        lb = volumes['annotation_mask']
        
        assert all([self.setLayout(w, 'foreground', fg, 0.5) for w in self.windows])
        assert all([self.setLayout(w, 'background', bg) for w in self.windows])
        assert all([self.setLayout(w, 'label', lb) for w in self.windows])

        self.set3dVis(True)
        self.setLabelOutline(True)
        self.rotate2Vol(volumes['histology'])

    def genFile(self):
        savepath = self.getSaveFile()
        if not savepath.endswith('.mrb'):
            savepath += '.mrb'
        status = slicer.util.saveScene(savepath)
        if status:
            self.lastMsg = self.genMsg('Scene file successfully saved.')
            self.lastMsg.show()

    def createClp(self, text, parentLayout, boxLayout):
        '''Create a collapsible button'''
        clpBtn = ctk.ctkCollapsibleButton()
        clpBtn.text = text
        parentLayout.addWidget(clpBtn)
        formLayout = qt.QFormLayout(clpBtn)
        formFrame = qt.QFrame(clpBtn)
        formFrame.setLayout(boxLayout)
        formLayout.addWidget(formFrame)
        return clpBtn, formLayout, formFrame

    def createLabel(self, text, parentLayout, toolTip=''):
        '''Create a label'''
        label = qt.QLabel(text)
        label.toolTip = toolTip
        parentLayout.addWidget(label)
        return label

    def createBtn(self, label, func, parentLayout, toolTip=''):
        '''Create a button'''
        btn = qt.QPushButton(label)
        btn.toolTip = toolTip
        btn.maximumWidth = 800
        btn.connect('clicked(bool)', func)
        parentLayout.addWidget(btn)
        return btn

    @staticmethod
    def getPath():
        '''Choose the folder'''
        dialog = ctk.ctkFileDialog()
        selected = dialog.getExistingDirectory()
        return selected

    @staticmethod
    def getSaveFile():
        '''Choose a file'''
        dialog = ctk.ctkFileDialog()
        selected = dialog.getSaveFileName()
        return selected

    @staticmethod
    def genMsg(text):
        msg = qt.QMessageBox()
        msg.setText(text)
        return msg


    # Main functions
    def loadData(self, _dir, folders):
        fl = os.listdir(_dir)
        assert all(f in fl for f in self.folders.values())
        histFl = os.listdir(path(_dir, self.folders['hist']))
        invivoFl = os.listdir(path(_dir, self.folders['invivo']))
        filepaths = {i.split('.')[0]: path(_dir, self.folders['hist'], i) for i in histFl}
        filepaths.update({i.split('.')[0]: path(_dir, self.folders['invivo'], i) for i in invivoFl})
        volumes = {i: slicer.util.loadLabelVolume(filepaths[i]) if i in self.labelmaps \
                            else slicer.util.loadVolume(filepaths[i]) for i in filepaths}
        return volumes
        
    def setInterp(self, node, value):
        dnode = node.GetDisplayNode()
        dnode.SetInterpolate(value)
        return True
        
    def setColourMap(self, node, cm):
        # cm: colour map
        # 'vtkMRMLColorTableNodeFileColdToHotRainbow.txt' for CD
        # 'vtkMRMLPETProceduralColorNodePET-Rainbow' for PET
        dnode = node.GetDisplayNode()
        dnode.SetAndObserveColorNodeID(cm)
        return True
        
    def autoAdjWind(self, node):
        dnode = node.GetDisplayNode()
        dnode.AutoWindowLevelOn()
        return True
        
    def setLayout(self, window, layer, node, alpha=None):
        '''
        window: Red, Yellow, Green
        layer: foreground, background, label
        node: the volume node
        alpha: transparency (for foreground and label maps only)
        '''
        assert window in self.windows
        assert layer in ('foreground', 'background', 'label')
        
        setFuncs = {
            'foreground': 'SetForegroundVolumeID',
            'background': 'SetBackgroundVolumeID',
            'label':      'SetLabelVolumeID'
        }
        
        opacityFuncs = {
            'foreground': 'SetForegroundOpacity',
            'label':      'SetLabelOpacity'
        }
        
        logic = slicer.app.layoutManager().sliceWidget(window).sliceLogic()
        cn = logic.GetSliceCompositeNode()
        
        getattr(cn, setFuncs[layer])(node.GetID())
        if alpha and layer != 'background':
            getattr(cn, opacityFuncs[layer])(alpha)
            
        return True
        
    def set3dVis(self, value):
        layoutManager = slicer.app.layoutManager()
        for n in layoutManager.sliceViewNames():
            controller = layoutManager.sliceWidget(n).sliceController()
            controller.setSliceVisible(value)
        
    def setLabelOutline(self, value):
        layoutManager = slicer.app.layoutManager()
        for n in layoutManager.sliceViewNames():
            controller = layoutManager.sliceWidget(n).sliceController()
            controller.showLabelOutline(True)
            
    def rotate2Vol(self, node):
        layoutManager = slicer.app.layoutManager()
        for n in layoutManager.sliceViewNames():
            layoutManager.sliceWidget(n).mrmlSliceNode().RotateToVolumePlane(node)