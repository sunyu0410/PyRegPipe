import os
import sys
import threading
import time
import pickle
import pathlib
from glob import glob
from os import path
from pprint import pprint, pformat

# Add the code folder to the path
topFolder = os.path.abspath(os.path.join(sys.executable, *([os.pardir]*4)))
sys.path.append(os.path.join(topFolder, 'code'))

from reg import *
from __main__ import vtk, qt, ctk, slicer

class WarpCnt:
    def __init__(self, parent):
        parent.title = 'Contour: warp zone contours'
        parent.categories = ['BiRT']
        parent.dependencies = []
        parent.contributors = ['Yu Sun']
        parent.helpText = '''
        This is a module for warping contours to the ex vivo space.
        '''
        parent.acknowledgementText = '''
        Acknowledge for everyone who has taught me Python, registration and other techniques. Most of what I learnt comes from people around me, books and the Internet.
        '''
        self.parent = parent
        
class WarpCntWidget:
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
                            'Warp Contour', self.layout, qt.QVBoxLayout())
        
        # Objects to hold the widgets
        self.labels = {}
        self.buttons = {}

        # Paths
        self.topFolder = topFolder
        self.cmtkPath = os.path.realpath(os.path.join(self.topFolder, 
                                            r'Tools/CMTK-2.3.0-Windows-x86/bin'))
        self.bashPath = os.path.realpath(os.path.join(self.topFolder, 
                                     r'Tools/cmder/vendor/git-for-windows/bin/bash.exe'))

        config = [
            ['lCnt', 'sCnt', 'findF1', 'file', '1. The contour (for in_3d) file'],
            ['lTfm', 'sTfm', 'findF2', 'file', '2. (in_3d)_to_(ex_xd).tfm'],
            ['lWrp', 'sWrp', 'findF3', 'folder', '3. The warp_output_transform folder'],
            ['lEx3', 'sEx3', 'findF4', 'file', '4. ex_3d_cropped.nii'],
            ['lCmt', 'sCmt', 'findF5', 'folder', '5. CMTK path'],
            ['lOut', 'sOut', 'findF6', 'folder', '6. Output folder']
        ]

        # Create widgets
        for (lab1, lab2, labBtn, _type, desc) in config:
            self.labels[lab1] = self.createLabel(desc, 
                                    self.formFrame.layout(), 
                                    desc)
            self.labels[lab2] = self.createLabel("", 
                                    self.formFrame.layout(), 
                                    desc)
            self.buttons[labBtn] = self.createBtn('Locate / Change', 
                                        self.findFileFact(lab2, _type), 
                                        self.formFrame.layout())

        # Set the default CMTK path
        self.labels['sCmt'].text = self.cmtkPath
        
        # Apply button
        self.labels['lApp'] = self.createLabel('7. Apply',
                                    self.formFrame.layout(),
                                    'Apply')
        self.buttons['apply'] = self.createBtn('Apply', 
                                        self.warpCnt, 
                                        self.formFrame.layout())

    def findFileFact(self, label_id, _type):
        def findFile():
            dialog = ctk.ctkFileDialog()
            if _type == 'file':
                selected = dialog.getOpenFileName()
            if _type == 'folder':
                selected = dialog.getExistingDirectory()
            if selected:
                self.labels[label_id].text = selected
        return findFile

    def warpCnt(self):
        cntr = self.labels['sCnt'].text
        tfmLinear = self.labels['sTfm'].text
        cmtkWarp = self.labels['sWrp'].text
        ex3d = self.labels['sEx3'].text
        cmtkPath = self.labels['sCmt'].text
        outFolder = self.labels['sOut'].text

        # Linear warp
        # Output: (peripheral_zone)_into_(ex_3d_cropped).nii
        outLinear = os.path.join(outFolder, '(peripheral_zone)_into_(ex_3d_cropped).nii')
        warpImg(inImg=cntr, refImg=ex3d, outImg=outLinear, pixelT='uchar',
                tfmFile=tfmLinear, intplMode='NearestNeighbor', labelMap=True)
        print("Linear warping done")

        # Deformable warp
        # Output: (peripheral_zone)_into_(ex_3d_cropped)_deformable.nii
        outDeform = os.path.join(outFolder, 
                    '(peripheral_zone)_into_(ex_3d_cropped)_deformable.nii')
        scriptPath = os.path.join(outFolder, 'cmtk_warp.sh')
        deformWarp(cmtkPath=cmtkPath, intplMode='--nn', inImg=outLinear, 
                    refImg=ex3d, outImg=outDeform, xform=cmtkWarp, 
                    scrPath=scriptPath, bashPath=self.bashPath)
        print("Deformable warping done")


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
