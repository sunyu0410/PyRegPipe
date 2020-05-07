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

class PyRegPipe:
    def __init__(self, parent):
        parent.title = 'Python Assisted Registration Pipeline'
        parent.categories = ['BiRT']
        parent.dependencies = []
        parent.contributors = ['Yu Sun']
        parent.helpText = '''
        This is a module for assisting the registration process of the BiRT project.
        '''
        parent.acknowledgementText = '''
        Acknowledge for everyone who has taught me Python, registration and other techniques. Most of what I learnt comes from people around me, books and the Internet.
        '''
        self.parent = parent
        
class PyRegPipeWidget:
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
        # clpStart
        self.clpStart, self.formLyout, self.formFrame = self.createClp('Start', 
                                                self.layout, qt.QVBoxLayout())

        # labPrjpath
        self.labPath = self.createLabel('Project Path: ', self.formFrame.layout())
        self.labPrjpath = self.createLabel('', self.formFrame.layout())

        # btnGetpath
        # self.btnGetpath = self.createBtn('Choose Project Folder', self.getPath, 
        #                     self.formFrame.layout(), 
        #                     'Choose the top level folder')
        
        # winMain
        self.winMain, self.pLayout = self.createWin((100, 50, 500, 700), 
                                'Python Assisted Registration Pipeline', 
                                qt.QVBoxLayout(), maxW=500, minW=400,
                                maxH=750, minH=650)
        self.pInitiated = False

        # winFilePanel
        self.winFilePanel, self.treeVol, self.treeTfm = self.createFilePanel()

        # Note area
        self.labNote = self.createLabel('Note', self.formFrame.layout())
        self.textNote = qt.QTextEdit()
        self.formFrame.layout().addWidget(self.textNote)

        # btnShowmain
        self.btnShowmain = self.createBtn('Main Panel', self.showMain, 
                            self.layout, 
                            'Start the registration process and show the panel')
        
        # btnFiles
        self.btnFiles = self.createBtn('File List', self.showFilePanel, self.layout, 
                                        'Open the file list')
        
        # btnShowCopyHeader
        self.btnShowCopyHeader = self.createBtn('Copy Header', 
                                            lambda: self.winCopyHeader.show(), 
                                            self.layout, 'Copy the header from a reference image')
        self.btnShowCopyHeader.enabled = False
        
        # btnShowFlipImage
        self.btnShowFlipImage = self.createBtn('Flip Image', 
                                            lambda: self.winFlipImage.show(), 
                                            self.layout, 'Flip an image along an axis')
        self.btnShowFlipImage.enabled = False

        # btnSaveSetting
        self.btnSaveSetting = self.createBtn('Save', self.saveSetting, 
                            self.layout, 'Save the current progress.')
        self.btnSaveSetting.enabled = False
        # # btnLoadSetting
        # self.btnLoadSetting = self.createBtn('Load', lambda: (self.addtoFilePanel(self.inFilePanel), self.refreshStatus()), 
        #                     self.layout, 'Load the progress from setting.')
        # self.btnLoadSetting.enabled = False

        
        # Other settings
        self.prjPath = None
        # self.bPathchosen = False
        self.patient_number = None
        self.outputs = {}       # {'step1_1': {fullpath: True/False}}
        self.statusLight = {}   # {'step1_1', the_label_obj}
        self.completed = {}     # {'step1_1', True}
        self.volumes = {}       # {filename: fullpath} for .nii
        self.transfms = {}      # {filename: fullpath} for .tfm
        self.sessFrames = {}    # {'step1_1': ref_to_widget}
        self.inFilePanel = []
        
        self.imagej_path = path.join(topFolder, r'Tools/ImageJ/ImageJ.exe')
        self.cmtk_path = path.join(topFolder, r'Tools/CMTK-2.3.0-Windows-x86/bin')
        self.bash_path = path.join(topFolder, r'Tools/cmder/vendor/git-for-windows/bin/bash.exe')

        self.cmtkOutput = [
            '(in_3d_log_masked)_into_(ex_3d_cropped)_deformable.nii',
            '(in_3d)_into_(ex_3d_cropped)_deformable.nii']

        self.pkMaps = ['in_dce_gd.nii',
                        'in_dce_auc.nii',
                        'in_dce_ire.nii',
                        'in_dce_irw.nii',
                        'in_dce_me.nii',
                        'in_dce_tonset.nii',
                        'in_dce_twashout.nii',
                        'in_dce_ttp.nii',
                        'in_ktrans_left_femoral.nii',
                        'in_ktrans_right_femoral.nii',
                        'in_ktrans_weinmann.nii',
                        'in_ktrans_parker.nii',
                        'in_ve_left_femoral.nii',
                        'in_ve_right_femoral.nii',
                        'in_ve_weinmann.nii',
                        'in_ve_parker.nii',
                        'in_iaugc60.nii']
    
    @staticmethod
    def createComboBox(items):
        cb = qt.QComboBox()
        cb.addItems(items)
        return cb

    def createWinCopyHeader(self):
        ''''''
        win, layout = self.createWin((100, 50, 300, 100), 
                        'Copy Header', qt.QVBoxLayout())
        win.setFixedSize(300, 112)
        filelist = os.listdir(self.nii_folder) if os.path.exists(self.nii_folder) else []
        filelist.sort()
        inputList = self.createComboBox(filelist)
        refList = self.createComboBox(filelist)
        self.createLabel("Input file", layout, "Select a file to proceed")
        layout.addWidget(inputList)
        self.createLabel("Reference file", layout, "Select a file to proceed")
        layout.addWidget(refList)
        
        def apply():
            inFile = os.path.join(self.nii_folder, inputList.currentText)
            refFile = os.path.join(self.nii_folder, refList.currentText)
            if inFile == refFile:
                self.lastMsg = self.genMsg("Error", "Input file and reference file are the same", 
                                                "", "")
                self.lastMsg.show()
            else:
                # copyHeader(_file, refFile, outDir, tempFolder)
                state = copyHeader(inFile, refFile, self.nii_folder, self.temp_folder)
                # print('Copy header:', inFile, refFile, self.nii_folder, self.temp_folder)
                if state:
                    self.lastMsg = self.genMsg("Info", "Header copied successfully", 
                                        "", "", qt.QMessageBox.Information)
                    self.lastMsg.show()
        
        def refresh():
            filelist = os.listdir(self.nii_folder) if os.path.exists(self.nii_folder) else []
            inputList.clear()
            inputList.addItems(filelist)
            refList.clear()
            refList.addItems(filelist)
        
        self.createBtn("Refresh", refresh, layout)
        self.createBtn("Apply", apply, layout)
        return win

    def createWinFlipImage(self):
        ''''''
        win, layout = self.createWin((100, 50, 300, 100), 
                        'Flip Image', qt.QVBoxLayout())
        win.setFixedSize(300, 112)
        filelist = os.listdir(self.nii_folder) if os.path.exists(self.nii_folder) else []
        filelist.sort()
        inputList = self.createComboBox(filelist)
        modes = ['Anterior - Posterior', 'Superior - Inferior', 'Left - Right']
        modeList = self.createComboBox(modes)
        self.createLabel("Input file", layout, "Select a file to proceed")
        layout.addWidget(inputList)
        self.createLabel("Axis", layout, "Along which axis to be flipped")
        layout.addWidget(modeList)

        modeDict = {
            'Anterior - Posterior': 'ap', 
            'Superior - Interior': 'si', 
            'Left - Right': 'lr'
        }

        def apply():
            inFile = os.path.join(self.nii_folder, inputList.currentText)
            _mode = modeDict[modeList.currentText]
            # flipFile(inFile, outFile, mode)
            state = flipFile(inFile, inFile, _mode)
            if state:
                self.lastMsg = self.genMsg("Info", "File flipped successfully", 
                                "", "", qt.QMessageBox.Information)
                self.lastMsg.show()

        def refresh():
            filelist = os.listdir(self.nii_folder) if os.path.exists(self.nii_folder) else []
            inputList.clear()
            inputList.addItems(filelist)
        
        self.createBtn("Refresh", refresh, layout)
        self.createBtn("Flip", apply, layout)
        return win

    def loadSetting(self):
        ''''''
        with open(self.setting_path, 'rb') as f:
            (self.prjPath, self.patient_number, self.outputs, 
             self.completed, self.volumes, self.transfms,
             self.inFilePanel, self.note) = pickle.load(f)
        self.textNote.setText(self.textNote.toPlainText() + self.note)
        
    def refreshStatus(self):
        for key in self.completed:
            self.setStatus(key, 1 if self.completed[key] else 0)

    def saveSetting(self):
        ''''''
        with open(self.setting_path, 'wb') as f:
            self.note = self.textNote.toPlainText()
            toSave = (self.prjPath, self.patient_number, self.outputs, 
                      self.completed, self.volumes, self.transfms,
                      self.inFilePanel, self.note)
            pickle.dump(toSave, f)
        # print('Setting saved')
        self.lastMsg = self.genMsg("Info", "Setting saved", 
                                        "", "", qt.QMessageBox.Information)
        self.lastMsg.show()

    def initMain(self, hasBold):
        '''Initiate the main panel'''
        # Step 1: convert DICOM to NIfTI
        self.clpStep1, self.formS1, self.formFrameS1 = self.createClp('Step 1 - DICOM to NIfTI', 
                                                self.pLayout, qt.QVBoxLayout())
        # Step 2: deformable registration
        self.clpStep2, self.formS2, self.formFrameS2 = self.createClp('Step 2 - In vivo - ex vivo', 
                                                self.pLayout, qt.QVBoxLayout())
        # A dict to refer to the proper formFrame
        self.formFramDict = {
            'step1': self.formFrameS1, 
            'step2': self.formFrameS2
        }

        # Sessions
        #   A session is a processing unit -> one "Apply" button
        keys = list(regSpecs.specs.keys())
        # If no BOLD, then skip step1_3
        if not hasBold:
            keys.pop(keys.index('step1_3'))
        for key in keys:
            self.createSession(**regSpecs.specs[key])

        # Enable the relevant buttons
        self.btnSaveSetting.enabled = True
        # self.btnLoadSetting.enabled = True
        if path.exists(self.setting_path):
            self.addtoFilePanel(self.inFilePanel)
            self.refreshStatus()
            # print("Settings loaded")

    def createSession(self, step, key, stepLabel, btnFunc, \
                    title, shortDesc):
        ''''''
        layout = self.formFramDict[step].layout()
        boxLayout = qt.QHBoxLayout()
        *ignore, fFrame = self.createClp(title, layout, boxLayout)
        self.sessFrames[key] = fFrame
        self.createLabel(shortDesc, fFrame.layout(), stepLabel)
        self.createBtn('Apply', lambda:btnFunc(self), fFrame.layout(), shortDesc)
        self.statusLight[key] = self.createLabel(' ', fFrame.layout())
        self.statusLight[key].setMaximumWidth(20)
        self.setStatus(key, 0)
                
    def showFilePanel(self):
        ''''''
        self.winFilePanel.show()

    def createFilePanel(self):
        ''''''
        filePanel, fLayout = self.createWin((100, 50, 400, 600), 
                        'File List', qt.QVBoxLayout(), maxW=400, minW=300)
            
        tree = qt.QTreeWidget ()
        headerItem = qt.QTreeWidgetItem()
        item = qt.QTreeWidgetItem()

        treeItems = []
        for label in ['Volumes', 'Transforms']:
            parent = qt.QTreeWidgetItem(tree)
            parent.setText(0, label)
            parent.setFlags(parent.flags() | qt.Qt.ItemIsTristate | qt.Qt.ItemIsUserCheckable)
            parent.setExpanded(True)
            treeItems.append(parent)
        tree.setHeaderLabels(['File Path'])
        tree.setWindowTitle('File Panel')
        # Font settings
        font = qt.QFont()
        font.setPointSize(8)
        font.setBold(True)
        [i.setFont(0, font) for i in treeItems]
        # Add widget
        fLayout.addWidget(tree)
        self.createBtn('Load to Scene', self.loadSelectedFiles, 
                           fLayout, 'Load selected data')
        self.createBtn('Clear Scene', self.clearScene, fLayout, 
                        'Clean everything in the current scene')

        return (filePanel, *treeItems)

    def addtoFilePanel(self, newFiles):
        ''''''
        filenames = dict(
            volumes = [i for i in newFiles if i.endswith('.nii')],
            transfms = [i for i in newFiles if i.endswith('.tfm')]
        )
        for key in filenames:
            parent = self.treeVol if key=='volumes' else self.treeTfm
            for i in filenames[key]:
                child = qt.QTreeWidgetItem(parent)
                child.setFlags(child.flags() | qt.Qt.ItemIsUserCheckable)
                child.setText(0, i)
                child.setCheckState(0, qt.Qt.Unchecked)

    def updateFilePanel(self, outputList):
        outputFiles = [path.split(i)[-1] for i in outputList]
        newFiles = [i for i in outputFiles if i not in self.inFilePanel]
        self.addtoFilePanel(newFiles)
        self.inFilePanel.extend(newFiles)
        
    def initParams(self, hasBold):
        '''Inititialise the backend parameters.'''
        # Folders
        self.patient_id = 'mrhist' + str(self.patient_number).zfill(3)
        self.dce_motion_slice = corrt_slice[self.patient_id]
        self.dataFolder = path.join(self.prjPath, 'data')
        self.contFolder = path.join(self.dataFolder, 'prostate_contours_from_slicer')
        self.in_vivo_folder = path.join(self.dataFolder, 'in_vivo_mri')

        self.in_3d_dcm_folder = path.join(self.in_vivo_folder, 'in_3d')
        self.in_2d_dcm_folder = path.join(self.in_vivo_folder, 'in_2d')
        self.dwi_dcm_folder = path.join(self.in_vivo_folder, 'dwi')
        self.adc_dcm_folder = path.join(self.in_vivo_folder, 'adc')
        self.dynamic_dcm_folder = path.join(self.in_vivo_folder, 'dynamic')
        self.pk_dcm_folder = path.join(self.in_vivo_folder, 'pk')
        self.pk_folders = os.listdir(self.pk_dcm_folder)
        if hasBold:
            self.bold_dcm_folder = path.join(self.in_vivo_folder, 'bold')

        # Create folders
        self.nii_folder = path.join(self.prjPath, 'nifti')
        self.tfm_folder = path.join(self.prjPath, 'transformation')
        self.sort_folder = path.join(self.prjPath, 'sorted')
        self.script_folder = path.join(self.prjPath, 'script')
        self.temp_folder = path.join(self.prjPath, 'temp')
        self.cmtk_folder = path.join(self.prjPath, 'cmtk')
        for eachFolder in [self.nii_folder, self.tfm_folder, self.sort_folder, \
                self.script_folder, self.temp_folder, self.cmtk_folder]:
            if not os.path.exists(eachFolder):
                os.makedirs(eachFolder)
        # print('Create folders')

    def showMain(self):
        '''Show the main panel'''
        # If the main panel not initiated, initiate it
        if not self.prjPath:
            # self.lastMsg = self.genMsg(title='Warning', text='Please select the folder', 
            #                  info='', detail='Select the top-level folder for the project.')
            # self.lastMsg.show()
            # return
            self.getPath()
            if not self.prjPath:
                return
        if not self.valPrjFolder():
            self.lastMsg = self.genMsg(title='Warning', \
                    text='The folder structure is invalid', info='', \
                    detail='Make sure the selected folder contains the necessary subfolders')
            self.lastMsg.show()
            # Reset the project path and the display
            self.prjPath = None
            self.labPrjpath.text = ''
            return
        if not self.pInitiated:
            if path.exists(self.setting_path):
                self.loadSetting()
            else:
                # Get the patient number
                self.patient_number = qt.QInputDialog.getInt(self.parent, 'Patient Number', 
                            'Please enter the patient number (e.g. 43 for mrhist043)')
                if not self.patient_number:
                    return
            self.hasBold = path.exists(path.join(self.prjPath, 'data', 'in_vivo_mri', 'bold'))
            self.initParams(hasBold=self.hasBold)
            self.initMain(hasBold=self.hasBold)
            self.winMain.windowTitle += ': ' + str(self.patient_number)

            # winCopyHeader & winFlipImage
            self.winCopyHeader = self.createWinCopyHeader()
            self.btnShowCopyHeader.enabled = True
            self.winFlipImage = self.createWinFlipImage()
            self.btnShowFlipImage.enabled = True

            self.pInitiated = True
        self.winMain.show()

    def getPath(self):
        '''Choose the project folder'''
        dialog = ctk.ctkFileDialog()
        selected = dialog.getExistingDirectory()
        if selected:
            self.prjPath = selected
            self.setting_path = path.join(self.prjPath, 'setting')
            self.labPrjpath.text = '\t' + selected
            # self.bPathchosen = True

    def createBtn(self, label, func, parentLayout, toolTip=''):
        '''Create a button'''
        btn = qt.QPushButton(label)
        btn.toolTip = toolTip
        btn.maximumWidth = 800
        btn.connect('clicked(bool)', func)
        parentLayout.addWidget(btn)
        return btn

    def createLabel(self, text, parentLayout, toolTip=''):
        '''Create a label'''
        label = qt.QLabel(text)
        label.toolTip = toolTip
        parentLayout.addWidget(label)
        return label
        
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

    def createWin(self, geometry, title, boxLayout, 
                    maxW=None, minW=None, maxH=None, minH=None):
        '''Create a window'''
        win = qt.QWidget()
        win.setGeometry(*geometry)
        win.setWindowTitle(title)
        win.setLayout(boxLayout)
        if maxW:
            win.maximumWidth = maxW
        if minW:
            win.minimumWidth = minW
        if maxH:
            win.maximumHeight = maxH
        if minH:
            win.minimumHeight = minH
        layout = win.layout()
        return win, layout


    def genMsg(self, title, text, info, detail, icon=qt.QMessageBox.Warning):
        '''Returns a customised message box object'''
        msg = qt.QMessageBox()
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setInformativeText(info)
        msg.setDetailedText(detail)
        return msg

    def getRequirement(self):
        return '''
        The folder must be the top-level folder and contains a subfolder called data:
        data
        ├───in_vivo_mri     (in vivo MRI)
        │   ├───in_2d       (in vivo 2D T2w images)
        │   ├───in_3d       (in vivo 3D T2w images)
        │   ├───dwi         (DWI)
        │   ├───adc         (ADC)
        │   ├───bold        (BOLD, if any)
        │   ├───pk          (Pharmacokinetic maps, Tissue4D + DYNAMIKA)
        │   │   ├───ire
        │   │   └───ktrans
        │   └───dynamic     (DCE-MRI dynamic series)
        ├───ex_vivo_mri     (ex vivo MRI)
        │   ├───ex_2d       (ex vivo 2D T2w images)
        │   └───ex_3d       (ex vivo 3D T2w images)
        └───prostate_contours_from_slicer   (prostate contours, nrrd file)
        '''
        
    def valPrjFolder(self):
        '''Validate the structure of the folder meets the requirement.'''
        path = self.prjPath
        files = {
            'in_vivo_mri': ['', 'in_2d', 'in_3d', 'dwi', 'adc', 'pk', 'dynamic'],
            'ex_vivo_mri': ['', 'ex_2d', 'ex_3d'],
            'prostate_contours_from_slicer': [''],
        }
        pathsToCheck = []
        for folder in files:
            for subfolder in files[folder]:
                pathsToCheck.append(os.path.join(path, 'data', folder, subfolder))
        for eachP in pathsToCheck:
            if not os.path.exists(eachP):
                return False
        return True

    def setStatus(self, key, state=0):
        templ = "background-color:%s;"
        colours = {0: 'orange', 1: 'lightgreen', -1: 'red'}
        self.statusLight[key].setStyleSheet(templ % colours[state])
        # pprint(self.outputs)

    def updateVolTfm(self, outputList):
        '''Takes a list and return a dict: {filename: fullpath}'''
        volDict = {path.split(i)[-1]:i for i in outputList if i.endswith('.nii')}
        tfmDict = {path.split(i)[-1]:i for i in outputList if i.endswith('.tfm')}
        self.volumes.update(volDict) 
        self.transfms.update(tfmDict)

    def getCheckedItems(self, treeItem, column=0):
        '''treeVol.child(0).checkState(0)'''
        checkedItems = [treeItem.child(i).text(column) \
                            for i in range(treeItem.childCount()) \
                            if treeItem.child(i).checkState(column)]
        return checkedItems
        

    def loadSelectedFiles(self):
        ''' # >>> treeVol.child(0).text(0) 
        # first 0: item index, second 0: column index
        # 'in_3d.nii'
        # >>> treeVol.childCount()
        # 3'''
        vols = [self.volumes[i] for i in self.getCheckedItems(self.treeVol)]
        tfms = [self.transfms[i] for i in self.getCheckedItems(self.treeTfm)]
        [slicer.util.loadVolume(i) for i in vols]
        [slicer.util.loadTransform(i) for i in tfms]

    @staticmethod
    def runThread(func, args):
        ''''''
        thr = threading.Thread(target=func, args=args)
        thr.start()
        return thr

    @staticmethod
    def getDiff(aSeq, refSeq):
        ''''''
        aSet = set(aSeq)
        refSet = set(refSeq)
        diffSet = aSet.difference(refSet)
        return tuple(diffSet)

    @staticmethod
    def clearScene():
        '''Clear everything in the current scene'''
        slicer.mrmlScene.Clear(0)

    @staticmethod
    def mergeDict(*dicts):
        result = {}
        for eachD in dicts:
            result.update(eachD)
        return result
        
    @staticmethod
    def createCheckbox(parent, options, exclusive=False):
        '''group.buttons()[0].checked -- whether first item checked
        '''
        optionWidgets = [qt.QCheckBox(i) for i in options]
        group = qt.QButtonGroup(parent)
        group.setExclusive(exclusive)
        [group.addButton(i) for i in optionWidgets]
        [parent.layout().addWidget(i) for i in optionWidgets]
        return group
