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

import genR2StarMacro
import regSpecs
from dce_motion import corrt_slice
from reg import *
from __main__ import vtk, qt, ctk, slicer

class ToNIfTI:
    def __init__(self, parent):
        parent.title = 'Dynamika: convert DICOM to NIfTI'
        parent.categories = ['BiRT']
        parent.dependencies = []
        parent.contributors = ['Yu Sun']
        parent.helpText = '''
        This is a module for converting DYNAMIKA DICOM to NIfTI files.
        '''
        parent.acknowledgementText = '''
        Acknowledge for everyone who has taught me Python, registration and other techniques. Most of what I learnt comes from people around me, books and the Internet.
        '''
        self.parent = parent
        
class ToNIfTIWidget:
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
                            'To NIfTI', self.layout, qt.QVBoxLayout())
        
        # Objects to hold the widgets
        self.labels = {}
        self.buttons = {}
        self.textareas = {}

        # Paths
        self.topFolder = os.path.abspath(os.path.join(sys.executable, *([os.pardir]*4)))
        self.cmtkPath = os.path.realpath(os.path.join(self.topFolder, 
                                            r'Tools/CMTK-2.3.0-Windows-x86/bin'))
        self.bashPath = os.path.realpath(os.path.join(self.topFolder, 
                                     r'Tools/cmder/vendor/git-for-windows/bin/bash.exe'))


        # Files to warp
        self.filesCvt = ['gd', 'auc', 'ire', 'irw', 'me', 'tonset', 
                          'twashout', 'ttp']

        # Project folder
        self.labels['lPrj'] = self.createLabel("DYNAMIKA DICOM folder(s)", 
                    self.formFrame.layout(), 'The folder for DYNAMKA DICOM files')
        self.textareas['vPrj'] = self.createTextarea(self.formFrame.layout())
        
        # Found list of files
        self.labels['lFndF'] = self.createLabel('Files found', self.formFrame.layout())
        self.textareas['vFndF'] = self.createTextarea(self.formFrame.layout())

        # Find files
        self.buttons['fndF'] = self.createBtn('Find Files', self.findFile, 
                                              self.formFrame.layout())
        
        # Output folder
        self.labels['lOut'] = self.createLabel('Output folder', self.formFrame.layout())
        self.textareas['vOut'] = self.createTextarea(self.formFrame.layout())

        # Set Fonts
        self.font_code = qt.QFont("Consolas")
        self.font_title = qt.QFont()
        # self.font_title.setPointSize(10)
        self.font_title.setBold(True)
        [t.setFont(self.font_code) for t in self.textareas.values()]
        [self.textareas[key].setMaximumHeight(30) for key in self.textareas if \
                                key not in ['vFndF']]
        [self.labels[key].setFont(self.font_title) for key in self.labels if \
                                    key.startswith('l')]

        # Set styles
        # l.setStyleSheet('background: lightgray')
        [self.labels[key].setStyleSheet('background: lightgray') for key in \
                            self.labels if key.startswith('v')]

        # Convert images
        self.buttons['convert'] = self.createBtn('Convert', self.cvtImg, 
                                              self.formFrame.layout())

        # clear
        self.buttons['clear'] = self.createBtn('Clear', self.clear, 
                                              self.formFrame.layout())
        print('Setup done')

    def findFile(self):
        fl = {i:None for i in self.filesCvt}
        prjFolder = self.textareas['vPrj'].toPlainText().strip().split()
        assert len(prjFolder) == 1
        for eachF in self.filesCvt:
            match = glob(os.path.join(prjFolder[0] + f'\\*{eachF}*'))
            if match:
                fl[eachF] = match[0]
        self.textareas['vFndF'].setText(pformat(fl, width=60))

    def cvtImg(self):
        # File list
        fl = eval(self.textareas['vFndF'].toPlainText())
        # Output folder
        outDir = self.textareas['vOut'].toPlainText().strip()

        if os.path.exists(outDir):
            print('Warning: output folder already exists.')
        os.makedirs(outDir, exist_ok=True)

        # check all files exist
        assert all([os.path.exists(i) for i in fl.values() if i is not None])

        for eachF in fl:
            # Rigid resampling
            eachFname = f'in_dce_{eachF}.nii'
            print(f'Converting {fl[eachF]}')
            cvtITK(fl[eachF], outDir, eachFname)
            

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
