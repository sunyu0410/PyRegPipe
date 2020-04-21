import os
import sys
import threading
import time
import pickle
import pathlib
from os import path
from pprint import pprint

# Add the code folder to the path
topFolder = os.path.abspath(os.path.join(sys.executable, *([os.pardir]*4)))
sys.path.append(os.path.join(topFolder, 'code'))

import genR2StarMacro
import regSpecs
from dce_motion import corrt_slice
from reg import *
from __main__ import vtk, qt, ctk, slicer

class WarpImg:
    def __init__(self, parent):
        parent.title = 'Warp Images'
        parent.categories = ['BiRT']
        parent.dependencies = []
        parent.contributors = ['Yu Sun']
        parent.helpText = '''
        This is a module for warping images from the in vivo space into the ex vivo space.
        '''
        parent.acknowledgementText = '''
        Acknowledge for everyone who has taught me Python, registration and other techniques. Most of what I learnt comes from people around me, books and the Internet.
        '''
        self.parent = parent
        
class WarpImgWidget:
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
                            'Warp Image', self.layout, qt.QVBoxLayout())
        
        # Objects to hold the widgets
        self.labels = {}
        self.buttons = {}
        self.textareas = {}

        # Files to warp
        self.filesWarp = ['in_dce_gd.nii', 'in_dce_auc.nii', 'in_dce_ire.nii', 
            'in_dce_irw.nii', 'in_dce_me.nii', 'in_dce_tonset.nii', 'in_dce_twashout.nii', 
            'in_dce_ttp.nii', 'in_ktrans_left_femoral.nii', 'in_ktrans_right_femoral.nii', 
            'in_ktrans_weinmann.nii', 'in_ktrans_parker.nii', 'in_ve_left_femoral.nii', 
            'in_ve_right_femoral.nii', 'in_ve_weinmann.nii', 'in_ve_parker.nii', 
            'in_iaugc60.nii']

        # Project folder
        self.labels['lPrj'] = self.createLabel("Project folder", self.formFrame.layout())
        self.textareas['vPrj'] = self.createTextarea(self.formFrame.layout())
        self.createBtn("Choose", self.selPrjFolder, self.formFrame.layout())
        
        # Output for into_(ex_3d_cropped) linear
        self.labels['lOutL'] = self.createLabel('Output folder (linear)',
                            self.formFrame.layout(), 'Output folder *_into_(ex_3d_cropped)')
        self.textareas['vOutL'] = self.createTextarea(self.formFrame.layout())
        self.createBtn('Change', lambda:self.selPath(self.textareas['vOutL']),
                                                     self.formFrame.layout())

        # Output for into_(ex_3d_cropped) deformable
        self.labels['lOutD'] = self.createLabel('Output folder (deformable)',
                    self.formFrame.layout(), 'Output folder *_into_(ex_3d_cropped)_deformable')
        self.textareas['vOutD'] = self.createTextarea(self.formFrame.layout())
        self.createBtn('Change', lambda:self.selPath(self.textareas['vOutD']),
                                                     self.formFrame.layout())

        # Defined list of files
        self.labels['lDefF'] = self.createLabel('Files to warp', self.formFrame.layout())
        self.textareas['vDefF'] = self.createTextarea(self.formFrame.layout())
        self.textareas['vDefF'].setText('\n'.join(self.filesWarp))
        # textarea.toPlainText()

        # Found list of files
        self.labels['lFndF'] = self.createLabel('Files found', self.formFrame.layout())
        self.textareas['vFndF'] = self.createTextarea(self.formFrame.layout())

        # Find files
        self.buttons['fndF'] = self.createBtn('Find Files', self.findFile, 
                                              self.formFrame.layout())
        
        # # - in_twist#.nii
        # self.labels['lTwist'] = self.createLabel('in_twist#.nii', self.formFrame.layout())
        # self.textareas['vTwist'] = self.createTextarea(self.formFrame.layout())

        # # - (in_twist#)_to_(in_3d).tfm
        # self.labels['lTwistToIn3d'] = self.createLabel('(in_twist#)_to_(in_3d).tfm', 
        #                                                     self.formFrame.layout())
        # self.textareas['vTwistToIn3d'] = self.createTextarea(self.formFrame.layout()) 

        # # - (in_3d)_to_(ex_xd).tfm
        # self.labels['lIn3dToEx'] = self.createLabel('(in_3d)_to_(ex_xd).tfm', 
        #                                                     self.formFrame.layout())
        # self.textareas['vIn3dToEx'] = self.createTextarea(self.formFrame.layout()) 

        # # - in_3d.nii
        # self.labels['lIn3d'] = self.createLabel('in_3d.nii', self.formFrame.layout())
        # self.textareas['vIn3d'] = self.createTextarea(self.formFrame.layout()) 

        # # - (ex_3d)_to_(ex_2d)_cropped.nii
        # self.labels['lEx3dToEx2d'] = self.createLabel('(ex_3d)_to_(ex_2d)_cropped.nii', 
        #                                                         self.formFrame.layout())
        # self.textareas['vEx3dToEx2d'] = self.createTextarea(self.formFrame.layout()) 

        # - the CMTK transformation folder
        self.labels['lCmtk'] = self.createLabel('CMTK transformation folder', 
                                                    self.formFrame.layout())
        self.textareas['vCmtk'] = self.createTextarea(self.formFrame.layout()) 

        # Set Fonts
        self.font_code = qt.QFont("Consolas")
        self.font_title = qt.QFont()
        # self.font_title.setPointSize(10)
        self.font_title.setBold(True)
        [t.setFont(self.font_code) for t in self.textareas.values()]
        [self.textareas[key].setReadOnly(True) for key in self.textareas if \
                                key in ['vPrj', 'vOutL', 'vOutD']]
        [self.textareas[key].setMaximumHeight(25) for key in self.textareas if \
                                key not in ['vDefF', 'vFndF']]
        [self.labels[key].setFont(self.font_title) for key in self.labels if \
                                    key.startswith('l')]

        # Set styles
        # l.setStyleSheet('background: lightgray')
        [self.labels[key].setStyleSheet('background: lightgray') for key in \
                            self.labels if key.startswith('v')]

        # Warp images
        self.buttons['warp'] = self.createBtn('Warp', self.warpImg, 
                                              self.formFrame.layout())

        # clear
        self.buttons['clear'] = self.createBtn('Clear', self.clear, 
                                              self.formFrame.layout())
        print('Setup done')
        
    def selPrjFolder(self):
        prjFolder = self.selPath(self.textareas['vPrj'])
        if not prjFolder:
            return
        outputLiner = os.path.join(prjFolder, 'warp_linear')
        outputDeform = os.path.join(prjFolder, 'warp_deformable')
        self.textareas['vOutL'].setText(outputLiner)
        self.textareas['vOutD'].setText(outputDeform)


    def findFile(self):
        print('findFile')
        pass

    def warpImg(self):
        print('warpImg')
        pass

    def clear(self):
        [t.clear() for t in self.textareas.values()]

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

    def createTextarea(self, parentLayout):
        # self.textNote = qt.QTextEdit()
        # self.formFrame.layout().addWidget(self.textNote)
        textarea = qt.QTextEdit()
        parentLayout.addWidget(textarea)
        return textarea

    def selPath(self, labelObj):
        "Get the path and change the label accordingly."
        path = self.getPath()
        if path:
            labelObj.setText(path)
        return path

    def getPath(self):
        '''Choose the project folder'''
        dialog = ctk.ctkFileDialog()
        selected = dialog.getExistingDirectory()
        return os.path.realpath(selected) if selected else None
