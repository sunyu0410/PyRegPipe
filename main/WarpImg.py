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

class WarpImg:
    def __init__(self, parent):
        parent.title = 'Dynamika: co-register with ex vivo MRI'
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

        # Paths
        self.topFolder = os.path.abspath(os.path.join(sys.executable, *([os.pardir]*4)))
        self.cmtkPath = os.path.realpath(os.path.join(self.topFolder, 
                                            r'Tools/CMTK-2.3.0-Windows-x86/bin'))
        self.bashPath = os.path.realpath(os.path.join(self.topFolder, 
                                     r'Tools/cmder/vendor/git-for-windows/bin/bash.exe'))


        # Files to warp
        self.filesWarp = ['in_dce_gd.nii', 'in_dce_auc.nii', 'in_dce_ire.nii', 
            'in_dce_irw.nii', 'in_dce_me.nii', 'in_dce_tonset.nii', 'in_dce_twashout.nii', 
            'in_dce_ttp.nii', 'in_ktrans_left_femoral.nii', 'in_ktrans_right_femoral.nii', 
            'in_ktrans_weinmann.nii', 'in_ktrans_parker.nii', 'in_ve_left_femoral.nii', 
            'in_ve_right_femoral.nii', 'in_ve_weinmann.nii', 'in_ve_parker.nii', 
            'in_iaugc60.nii']

        self.filesAssc = ['(in_twist*)_to_(in_3d).tfm', 
                            '(in_3d)_to_(ex_xd).tfm', 'in_3d.nii', 
                            '(ex_3d)_to_(ex_2d)_cropped.nii']

        # Project folder
        self.labels['lPrj'] = self.createLabel("DYNAMIKA folder(s)", 
                    self.formFrame.layout(), 'The folder for DYNAMKA maps')
        self.textareas['vPrj'] = self.createTextarea(self.formFrame.layout())
        
        # Associated folder
        self.labels['lAsc'] = self.createLabel("Associated folder(s)", 
                        self.formFrame.layout(), 'The folder for other files')
        self.textareas['vAsc'] = self.createTextarea(self.formFrame.layout())
        
        # Found list of files
        self.labels['lFndF'] = self.createLabel('Files found', self.formFrame.layout())
        self.textareas['vFndF'] = self.createTextarea(self.formFrame.layout())

        # Find files
        self.buttons['fndF'] = self.createBtn('Find Files', self.findFile, 
                                              self.formFrame.layout())
        
        # - the CMTK transformation folder
        self.labels['lCmtk'] = self.createLabel('CMTK transformation folder', 
                                                    self.formFrame.layout())
        self.textareas['vCmtk'] = self.createTextarea(self.formFrame.layout())
        # self.createBtn('Choose', lambda:self.selPath(self.textareas['vCmtk']),
        #                                              self.formFrame.layout())
        
        # Output folder
        self.labels['lOut'] = self.createLabel('Output folder', self.formFrame.layout())
        self.textareas['vOut'] = self.createTextarea(self.formFrame.layout())

        # Set Fonts
        self.font_code = qt.QFont("Consolas")
        self.font_title = qt.QFont()
        # self.font_title.setPointSize(10)
        self.font_title.setBold(True)
        [t.setFont(self.font_code) for t in self.textareas.values()]
        [self.textareas[key].setMaximumHeight(50) for key in self.textareas if \
                                key not in ['vFndF']]
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

    def findFile(self):
        fl1 = {i:None for i in self.filesWarp}
        prjFolder = self.textareas['vPrj'].toPlainText().strip().split()
        for eachF in self.filesWarp:
            for f in prjFolder:
                match = glob(os.path.join(f + '**', eachF))
                if match:
                    fl1[eachF] = match[0]
                    break

        fl2 = {i:None for i in self.filesAssc}
        ascFolder = self.textareas['vAsc'].toPlainText().strip().split()
        for eachF in self.filesAssc:
            for f in ascFolder:
                match = glob(os.path.join(f + '**', eachF))
                if match:
                    fl2[eachF] = match[0]
                    break
        fl = dict(warp=fl1, assc=fl2)
        self.textareas['vFndF'].setText(pformat(fl, width=60))

    def warpImg(self):
        # File list
        fl = eval(self.textareas['vFndF'].toPlainText())
        flWarp = fl['warp']
        flAssc = fl['assc']

        # Output folder
        outDir = self.textareas['vOut'].toPlainText().strip()
        outDirS = os.path.join(outDir, 'script')
        outDirL = os.path.join(outDir, 'linear')
        outDirT = os.path.join(outDir, 'temp')
        outDirD = os.path.join(outDir, 'deformable')

        if os.path.exists(outDir):
            print('Warning: output folder already exists.')
        [os.makedirs(i, exist_ok=True) for i \
            in (outDir, outDirL, outDirD, outDirT, outDirS)]

        # CMTK transformation folder
        cmtkTfmDir = self.textareas['vCmtk'].toPlainText().strip()

        # assert no missing asscociated files
        assert all(flAssc.values())
        # check all files exist
        assert all([os.path.exists(i) for i in flAssc.values()])
        assert all([os.path.exists(i) for i in flWarp.values() if i is not None])
        assert os.path.exists(cmtkTfmDir)

        for eachF in flWarp:
            # Rigid resampling
            # into_(in_3d)
            inImgT = flWarp[eachF]
            if not inImgT:
                print(f'Skipping {eachF}')
                continue
            refImgT = flAssc['in_3d.nii']
            outFnameT = f"({eachF.split('.nii')[0]})_into_(in_3d).nii"
            outImgT = os.path.join(outDirT, outFnameT)
            tfmFileT = flAssc['(in_twist*)_to_(in_3d).tfm']
            warpImg(inImg=inImgT,  refImg=refImgT, outImg=outImgT, pixelT='float',
                    tfmFile=tfmFileT, intplMode='Linear', labelMap=False)

            # into_(ex_3d_cropped)
            inImgL = outImgT
            refImgL = flAssc['(ex_3d)_to_(ex_2d)_cropped.nii']
            outFnameL = f"({eachF.split('.nii')[0]})_into_(ex_3d_cropped).nii"
            outImgL = os.path.join(outDirL, outFnameL)
            tfmFileL = flAssc['(in_3d)_to_(ex_xd).tfm']
            print(f'Warp linear: {eachF}')
            warpImg(inImg=inImgL,  refImg=refImgL, outImg=outImgL, pixelT='float',
                    tfmFile=tfmFileL, intplMode='Linear', labelMap=False)

            # Deformable resampling
            # deformWarp(cmtkPath, inImg, refImg, outImg, xform, scrPath, bashPath)
            inImgD = outImgL
            refImgD = refImgL
            outFnameD = f"({eachF.split('.nii')[0]})_into_(ex_3d_cropped)_deformable.nii"
            outImgD = os.path.join(outDirD, outFnameD)
            xform = cmtkTfmDir
            srcPath = os.path.join(outDirS, f"warp_{eachF.split('.')[0]}.sh")
            print(f'Warp deform: {eachF}')
            deformWarp(cmtkPath=self.cmtkPath, inImg=inImgD, refImg=refImgD, outImg=outImgD,
                       xform=xform, scrPath=srcPath, bashPath=self.bashPath)
            

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
