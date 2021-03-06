import os
import sys
import time
from os import path
from pprint import pprint
from subprocess import Popen

# Add the code folder to the path
topFolder = os.path.abspath(os.path.join(sys.executable, *([os.pardir]*4)))
sys.path.append(os.path.join(topFolder, 'code'))

import genR2StarMacro
from genCmtkScript import genCmtkScript
from dce_motion import corrt_slice
from reg import *
from __main__ import vtk, qt, ctk, slicer, selectModule


def update(self, key, output):
    ''''''
    # print(key, 'processed')
    self.outputs[key] = output
    outputList = list(output.keys())
    self.updateVolTfm(outputList)
    self.updateFilePanel(outputList)
    if all(output.values()):
        self.setStatus(key, 1)
        self.completed[key] = True
    else:
        self.setStatus(key, -1)
    # print(key, 'updated')

def step1_1(self):
    '''Step 1: 1. T2w'''
    key = 'step1_1'
    output = self.mergeDict(
        cvtITK(self.in_3d_dcm_folder, self.nii_folder, 'in_3d.nii'),
        cvtITK(self.in_2d_dcm_folder, self.nii_folder, 'in_2d.nii')
    )

    outTfm = path.join(self.tfm_folder, '(in_2d)_to_(in_3d).tfm')
    if not path.exists(outTfm):
        output.update(
            # Rigid registration, (in_2d)_to_(in_3d).tfm
            rigidReg(fixedImg=path.join(self.nii_folder, 'in_3d.nii'),
                    movingImg=path.join(self.nii_folder, 'in_2d.nii'),
                    outImg=None,
                    outTfm=outTfm)
        )
        
    else:
        print(f'Using existing transformation:\n\t{outTfm}')

    output.update(
        # Create the (in_2d)_to_(in_3d).nii
        warpImg(inImg=os.path.join(self.nii_folder, 'in_2d.nii'),
                refImg=os.path.join(self.nii_folder, 'in_2d.nii'),
                outImg=os.path.join(self.nii_folder, '(in_2d)_to_(in_3d).nii'),
                pixelT='float',
                tfmFile=outTfm,
                intplMode='Linear')
    )

    output.update(
        # Invert the (in_2d)_to_(in_3d).tfm
        invertTfm(outTfm, path.join(self.tfm_folder, '(in_3d)_to_(in_2d).tfm'))
    )

    update(self, key, output)

def step1_2(self):
    '''Step 1: 2. DWI'''
    key = 'step1_2'
    # Create a folder for sorted DWI .dcm files
    self.sort_dwi_folder = os.path.join(self.sort_folder, 'dwi')
    if not os.path.exists(self.sort_dwi_folder):
        os.makedirs(self.sort_dwi_folder)
    # Sort the data
    sortDcm(self.dwi_dcm_folder, self.sort_dwi_folder, 'dwi')

    output = self.mergeDict(
        # Convert the b=50 dcm files to in_dwi_b50.nii
        cvtITK(os.path.join(self.sort_dwi_folder, '50'),
                    self.nii_folder, 'in_dwi_b50.nii')
    )

    outTfm = os.path.join(self.tfm_folder, '(in_dwi_b50)_to_(in_3d).tfm')
    if not path.exists(outTfm):
        output.update(
            # Rigid registration to in_3d
            rigidReg(fixedImg=os.path.join(self.nii_folder, 'in_3d.nii'),
                    movingImg=os.path.join(self.nii_folder, 'in_dwi_b50.nii'),
                    outImg=None,
                    outTfm=outTfm)
        )
        
    else:
        print(f'Using existing transformation:\n\t{outTfm}')
                
    output.update(
        # Create the (in_dwi_b50)_to_(in_3d).nii
        warpImg(inImg=os.path.join(self.nii_folder, 'in_dwi_b50.nii'),
                refImg=os.path.join(self.nii_folder, 'in_dwi_b50.nii'),
                outImg=os.path.join(self.nii_folder, '(in_dwi_b50)_to_(in_3d).nii'),
                pixelT='float',
                tfmFile=outTfm,
                intplMode='Linear')
    )

    output.update(
        # Convert ADC to in_adc.nii
        cvtITK(self.adc_dcm_folder, self.nii_folder, 'in_adc.nii')
    )

    output.update(
        # Apply (in_dwi_b50)_to_(in_3d).tfm on in_adc
        warpImg(inImg=os.path.join(self.nii_folder, 'in_adc.nii'),
                refImg=os.path.join(self.nii_folder, 'in_adc.nii'),
                outImg=os.path.join(self.nii_folder, '(in_adc)_to_(in_3d).nii'),
                pixelT='float',
                tfmFile=outTfm,
                intplMode='Linear')
    )
    update(self, key, output)



def step1_3(self):
    '''Step 1: 3. BOLD'''
    key = 'step1_3'

    if os.path.isdir(self.bold_dcm_folder.strip()):
        # Sort the .dcm data
        self.sort_bold_folder = os.path.join(self.sort_folder, 'bold')
        if not os.path.exists(self.sort_bold_folder):
            os.makedirs(self.sort_bold_folder)
        sortDcm(self.bold_dcm_folder, self.sort_bold_folder, 'bold')
        
        self.bold_echo2_folder = os.path.join(self.sort_bold_folder, '9.84')
        output = self.mergeDict(
            # Convert the second echo time (9.84 ms) to .nii
            cvtITK(self.bold_echo2_folder, self.nii_folder, 'in_bold_echo2.nii')
        )

        outTfm = os.path.join(self.tfm_folder, '(in_bold_echo2)_to_(in_3d).tfm')
        if not path.exists(outTfm):
            output.update(
                # Co-register to in_3d
                rigidReg(fixedImg=os.path.join(self.nii_folder, 'in_3d.nii'),
                        movingImg=os.path.join(self.nii_folder, 'in_bold_echo2.nii'),
                        outImg=None,
                        outTfm=outTfm) 
            )
            
        else:
            print(f'Using existing transformation:\n\t{outTfm}')

        output.update(
            # Resampling to get the 'to' file
            warpImg(inImg=os.path.join(self.nii_folder, 'in_bold_echo2.nii'),
                    refImg=os.path.join(self.nii_folder, 'in_bold_echo2.nii'),
                    outImg=os.path.join(self.nii_folder, '(in_bold_echo2)_to_(in_3d).nii'),
                    pixelT='float',
                    tfmFile=outTfm,
                    intplMode='Linear')
        )

        # R2* map
        r2star_path = os.path.join(self.nii_folder, 'in_r2star.nii')
        if os.path.exists(r2star_path):
            # If R2* map not existed
            print('Using existing R2* map:', r2star_path)
        else:
            # Generate R2* map
            self.temp_r2star_folder = os.path.join(self.temp_folder, 'R2STAR')
            if path.exists(self.temp_r2star_folder):
                shutil.rmtree(self.temp_r2star_folder)
            shutil.copytree(self.bold_dcm_folder, self.temp_r2star_folder)   
            # Initialise a parameter set
            r2starParams = {
                'reverse': True,
                'vflip': False,
                'echoTypo': False
            }
            macroFilename = 'r2star.imj'
            self.r2starScriptPath = os.path.join(self.script_folder, macroFilename)
            # print(self.r2starScriptPath)
            # Create the ImageJ macro
            genR2StarMacro.genR2StarMacro(
                self.r2starScriptPath,
                reverse=r2starParams['reverse'],
                vflip=r2starParams['vflip'],
                echoTypo=r2starParams['echoTypo']
            )
            # Run the macro
            genR2Star(self.r2starScriptPath, self.imagej_path)
            # Move the files to the corresponding folders
            shutil.move(os.path.join(self.temp_r2star_folder, 'in_r2star.nii'), 
                        os.path.join(self.nii_folder, 'in_r2star.nii'))
            output.update(
                {os.path.join(self.nii_folder, 'in_r2star.nii'): True}
            )
            
            os.remove(os.path.join(self.temp_r2star_folder, 'in_t2star.tif'))
            # Copy the header information
            copyHeader(os.path.join(self.nii_folder, 'in_r2star.nii'),
                        os.path.join(self.nii_folder, 'in_bold_echo2.nii'),
                        self.nii_folder,
                        self.temp_folder)

        output.update(
            # Resampling to get the 'to' file
            warpImg(inImg=os.path.join(self.nii_folder, 'in_r2star.nii'),
                    refImg=os.path.join(self.nii_folder, 'in_r2star.nii'),
                    outImg=os.path.join(self.nii_folder, '(in_r2star)_to_(in_3d).nii'),
                    pixelT='float',
                    tfmFile=outTfm,
                    intplMode='Linear')
        )

        # Manually check the r2star map
        self.lastMsg = self.genMsg("Info", "Please check the orientation of the R2* map.", 
                                "", "", qt.QMessageBox.Information)
        self.lastMsg.show()
        # Clear the current scene
        slicer.mrmlScene.Clear(0)
    update(self, key, output)

def step1_4(self):
    key = 'step1_4'
    self.t1_motion_cor_folder = dceMotCorFolder(
                self.dynamic_dcm_folder, self.dce_motion_slice)
    self.t1_nii_filename = 'in_twist%s.nii' % self.dce_motion_slice
    output = self.mergeDict(
        cvtITK(self.t1_motion_cor_folder, self.nii_folder, 
                    self.t1_nii_filename)
    )

    outTfm = os.path.join(self.tfm_folder, '(in_twist#)_to_(in_3d).tfm')
    if not path.exists(outTfm):
        output.update(
            rigidReg(fixedImg=os.path.join(self.nii_folder, 'in_3d.nii'),
                    movingImg=os.path.join(self.nii_folder, self.t1_nii_filename),
                    outImg=None,
                    outTfm=outTfm)
        )
        
    else:
        print(f'Using existing transformation:\n\t{outTfm}')
    
    output.update(
        # Resampling to get the 'to' file
        warpImg(inImg=os.path.join(self.nii_folder, self.t1_nii_filename),
                refImg=os.path.join(self.nii_folder, self.t1_nii_filename),
                outImg=os.path.join(self.nii_folder, '(in_twist#)_to_(in_3d).nii'),
                pixelT='float',
                tfmFile=outTfm,
                intplMode='Linear')
    )

    for eachPk in self.pk_folders:
        output.update(
            cvtITK(os.path.join(self.pk_dcm_folder, eachPk), 
                    self.nii_folder, f'{eachPk}.nii')
        )
        output.update(
            warpImg(inImg=os.path.join(self.nii_folder, f'{eachPk}.nii'),
                refImg=os.path.join(self.nii_folder, f'{eachPk}.nii'),
                outImg=os.path.join(self.nii_folder, f'({eachPk})_to_(in_3d).nii'),
                pixelT='float',
                tfmFile=outTfm,
                # Use nearest neighbour for in_dce_gd
                intplMode='NearestNeighbor' if eachPk=='in_dce_gd' else 'Linear')
        )

    update(self, key, output)
        


def step2_1(self):
    '''Step 2: 0 - 3'''
    key = 'step2_1'
    self.ex_3d_dcm_folder = path.join(self.dataFolder, r'ex_vivo_mri\ex_3d')
    self.ex_2d_dcm_folder = path.join(self.dataFolder, r'ex_vivo_mri\ex_2d')

    # self.bash_path
    # Contours
    in_2d_contour_file = path.join(self.contFolder, f'{self.patient_number}_in_2d-label.nrrd')
    ex_2d_contour_file = path.join(self.contFolder, f'{self.patient_number}_ex_2d-label.nrrd')

    # 0 - convert files to NIfTI
    output = self.mergeDict(
        cvtITK(self.ex_3d_dcm_folder, self.nii_folder, 'ex_3d.nii'),
        cvtITK(self.ex_2d_dcm_folder, self.nii_folder, 'ex_2d.nii')
    )
    

    # Create an identity tfm
    tfm_identity = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(tfm_identity)
    tfm_identity_path = os.path.join(self.tfm_folder, 'identity.tfm')
    saved = slicer.util.saveNode(tfm_identity, tfm_identity_path)
    if saved:
        output.update({tfm_identity_path: True})

    # 1. Label masks
    in_2d_contour = slicer.util.loadLabelVolume(in_2d_contour_file)
    ex_2d_contour = slicer.util.loadLabelVolume(ex_2d_contour_file)

    # Check the contours are label maps
    assert in_2d_contour.GetNodeTagName() == 'LabelMapVolume'
    assert ex_2d_contour.GetNodeTagName() == 'LabelMapVolume'

    # Convert in_2d_contour
    in_2d_contour_path = os.path.join(self.nii_folder, 'in_2d_contour.nii')
    saved = slicer.util.saveNode(in_2d_contour, in_2d_contour_path)
    if saved:
        output.update({in_2d_contour_path: True})
    
    # Convert ex_2d_contour
    ex_2d_contour_path = os.path.join(self.nii_folder, 'ex_2d_contour.nii')
    saved = slicer.util.saveNode(ex_2d_contour, ex_2d_contour_path)
    if saved:
        output.update({ex_2d_contour_path: True})


    slicer.mrmlScene.Clear(0)

    # Check if there's bands in the contour, dilate then erode the contour

    # Close the contour in case of any holes
    morphProcess(in_2d_contour_path, in_2d_contour_path, 'close')
    morphProcess(ex_2d_contour_path, ex_2d_contour_path, 'close')
    
    # 2. Register in_3d into in_2d
    # Already done so in stepOne.py
    # => (in_3d)_to_(in_2d).tfm

    # 3. Convert in_2d_contour to in_3d_contour
    output.update(
        # Resampling
        warpImg(inImg=os.path.join(self.nii_folder, 'in_2d_contour.nii'),
                refImg=os.path.join(self.nii_folder, 'in_3d.nii'),
                outImg=os.path.join(self.nii_folder, 'in_3d_contour_blocky.nii'),
                pixelT='uchar',
                tfmFile=os.path.join(self.tfm_folder, '(in_2d)_to_(in_3d).tfm'),
                intplMode='NearestNeighbor', # US spelling
                labelMap=True)
    )
    output.update(
        # LabelMapSmoothing
        labelMapSmoothing(
            inImg=os.path.join(self.nii_folder, 'in_3d_contour_blocky.nii'),
            outImg=os.path.join(self.nii_folder, 'in_3d_contour.nii'), 
            sigma=2)
    )
    
    update(self, key, output)

def step2_2(self):
    '''Step 2: 4'''
    key = 'step2_2'
    output = {}
    # 4. Register ex vivo 3D with ex vivo 2D
    # The part for ex_3d_head_coil has been removed
    
    # Manual alignment
    ex_3d = slicer.util.loadVolume(os.path.join(self.nii_folder, 'ex_3d.nii'))
    ex_2d = slicer.util.loadVolume(os.path.join(self.nii_folder, 'ex_2d.nii'))
    tfm_manual_path = os.path.join(self.tfm_folder, '(ex_3d)_to_(ex_2d)_manual.tfm')
    if not os.path.exists(tfm_manual_path):
        tfm_manual = slicer.vtkMRMLLinearTransformNode()
        slicer.mrmlScene.AddNode(tfm_manual)
        tfm_manual.SetName('(ex_3d)_to_(ex_2d)_manual')
    else:
        tfm_manual = slicer.util.loadTransform(tfm_manual_path)
        print('Loaded:', tfm_manual_path)
    ex_3d.SetAndObserveTransformNodeID(tfm_manual.GetID())
    selectModule(slicer.modules.transforms)
    try:
        _ = input("Please manually adjust the initial alignment. \n\
                   (Notice no head coil is involved.) \n\
                   1. Select (ex_3d)_to_(ex_2d)_manual as the active transform; \n\
                   2. Use the slider to adjust the alignment; \n\
                   3. Press ENTER to continue. ")
    except:
        # In case of an EOF error (empty string)
        pass

    print('*'*20, 'Done', '*'*20)

    # Save the transformation
    saved = slicer.util.saveNode(tfm_manual, tfm_manual_path)
    if saved:
        output.update({tfm_manual_path: True})
    
    # Rigid registration
    output.update(
        rigidReg(
            fixedImg = os.path.join(self.nii_folder, 'ex_2d.nii'),
            movingImg = os.path.join(self.nii_folder, 'ex_3d.nii'),
            outImg = None,
            outTfm = os.path.join(self.tfm_folder, '(ex_3d)_to_(ex_2d)_auto.tfm'),
            initTfm = os.path.join(self.tfm_folder, '(ex_3d)_to_(ex_2d)_manual.tfm')
        )
    )

    output.update(
        # Resampling to get the 'to' file
        warpImg2(inImg=os.path.join(self.nii_folder, 'ex_3d.nii'),
                 outImg=os.path.join(self.nii_folder, '(ex_3d)_to_(ex_2d).nii'),
                 tfmFile=os.path.join(self.tfm_folder, '(ex_3d)_to_(ex_2d)_auto.tfm')
                )
    )
            
    # Check the registration
    # ex_3d = slicer.util.loadVolume(os.path.join(self.nii_folder, 'ex_3d.nii'))
    # ex_2d = slicer.util.loadVolume(os.path.join(self.nii_folder, 'ex_2d.nii'))
    # result = slicer.util.loadVolume(os.path.join(self.nii_folder, '(ex_3d)_into_(ex_2d).nii'))
    # print("Please check the registration.")

    slicer.mrmlScene.Clear(0)
    selectModule(slicer.modules.pyregpipe)
    update(self, key, output)


def step2_3(self):
    '''Step 2: 5 - 10'''
    key = 'step2_3'

    # 5. Convert ex 2d contour to ex 3d contour
    slicer.util.loadVolume(os.path.join(self.nii_folder, 'ex_2d_contour.nii'))
    slicer.util.loadVolume(os.path.join(self.nii_folder, 'ex_3d.nii'))

    output = dict(
        warpImg(inImg=os.path.join(self.nii_folder, 'ex_2d_contour.nii'),
                refImg=os.path.join(self.nii_folder, '(ex_3d)_to_(ex_2d).nii'),
                outImg=os.path.join(self.nii_folder, 'ex_3d_contour_blocky.nii'),
                pixelT='uchar',
                tfmFile=os.path.join(self.tfm_folder, 'identity.tfm'),
                intplMode='NearestNeighbor', # US spelling
                labelMap=True)
    )
    
            
    # LabelMapSmoothing
    output.update(
        labelMapSmoothing(inImg=os.path.join(self.nii_folder, 'ex_3d_contour_blocky.nii'),
                    outImg=os.path.join(self.nii_folder, 'ex_3d_contour.nii'),
                    sigma=2)
    )

    slicer.mrmlScene.Clear(0)
           
    # 6. Crop ex 3d as a reference image
    slicer.util.loadVolume(os.path.join(self.nii_folder, '(ex_3d)_to_(ex_2d).nii'))
    selectModule(slicer.modules.cropvolume)
    # Create an Annotation ROI Node
    roiNode = slicer.vtkMRMLAnnotationROINode()
    slicer.mrmlScene.AddNode(roiNode)
    # Create an output volume node
    outputNode = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(outputNode)
    outputNode.SetName('(ex_3d)_to_(ex_2d)_cropped')
    # Set the parameters. Note that the positions of the 
    #   widgets might be dependent on the Slicer version
    w = slicer.modules.cropvolume.widgetRepresentation()
    w.children()[2].children()[5].setCurrentNode(roiNode)
    w.children()[2].children()[10].setCurrentNode(outputNode)

    # Manually adjust the ROI
    try:
        _ = input("Please adjust the cropping volume \n\
                   1. Use the control points to crop ex_3d; \n\
                   2. Click 'Apply' in the 'Crop Volume' module; \n\
                   3. Press ENTER to continue. ")
    except:
        # In case of an EOF error (empty string)
        pass
    # print("Cropping the volume")
    # Simulate the click
    # w.findChildren('QPushButton', 'CropButton')[0].animateClick()
    print('*'*20, 'Done', '*'*20)

    # Save node
    ex_3d_cropped_path = os.path.join(self.nii_folder, 'ex_3d_cropped.nii')
    saved = slicer.util.saveNode(outputNode, ex_3d_cropped_path)
    if saved:
        output.update({ex_3d_cropped_path: True})
    slicer.util.saveNode(roiNode, os.path.join(self.temp_folder, 'ex_3d_cropped_roi.acsv'))
    # To load the annotation node
    # slicer.util.loadAnnotationROI(os.path.join(self.temp_folder, 'ex_3d_cropped_roi.acsv'))
    selectModule(slicer.modules.pyregpipe)
                        
    # 7. Filter in 3d
    # in_3d_log_path = os.path.join(self.nii_folder, 'in_3d_log.nii')
    # genLogMacro(infile=os.path.join(self.nii_folder, 'in_3d.nii'),
    #             outfile=in_3d_log_path,
    #             macroPath=os.path.join(self.script_folder, 'in_3d_log.imj'))
    # filterLoG(macro_path=os.path.join(self.script_folder, 'in_3d_log.imj'),
    #         exe_path=self.imagej_path)
    # copyHeader(os.path.join(self.nii_folder, 'in_3d_log.nii'),
    #         os.path.join(self.nii_folder, 'in_3d.nii'),
    #         self.nii_folder,
    #         self.temp_folder)
    # if os.path.exists(in_3d_log_path):
    #     output.update({os.path.join(self.nii_folder, 'in_3d_log.nii'):True})

    output.update(
        logFilter(inFile=os.path.join(self.nii_folder, 'in_3d.nii'),
                  outFile=os.path.join(self.nii_folder, 'in_3d_log.nii'))
    )


    # 8. Filter ex 3d cropped
    # ex_3d_cropped_log_path = os.path.join(self.nii_folder, 
    #                                     'ex_3d_cropped_log.nii')
    # genLogMacro(infile=os.path.join(self.nii_folder, 'ex_3d_cropped.nii'),
    #             outfile=ex_3d_cropped_log_path,
    #             macroPath=os.path.join(self.script_folder, 'ex_3d_log.imj'))
                
    # filterLoG(macro_path=os.path.join(self.script_folder, 'ex_3d_log.imj'),
    #         exe_path=self.imagej_path)
            
    # copyHeader(os.path.join(self.nii_folder, 'ex_3d_cropped_log.nii'),
    #         os.path.join(self.nii_folder, 'ex_3d_cropped.nii'),
    #         self.nii_folder,
    #         self.temp_folder)
    # if os.path.exists(ex_3d_cropped_log_path):
    #     output.update({ex_3d_cropped_log_path: True})
    output.update(
        logFilter(inFile=os.path.join(self.nii_folder, 'ex_3d_cropped.nii'),
                  outFile=os.path.join(self.nii_folder, 'ex_3d_cropped_log.nii'))
    )

    # 9. Mask in 3d log with manual contour
    output.update(
        maskVolume(infile=os.path.join(self.nii_folder, 'in_3d_log.nii'),
            contFile=os.path.join(self.nii_folder, 'in_3d_contour.nii'),
            outFile=os.path.join(self.nii_folder, 'in_3d_log_masked.nii'),
            label=1)
    )
    
    # 10. mask ex 3d cropped log with the manual contour
    output.update(
        maskVolume(infile=os.path.join(self.nii_folder, 'ex_3d_cropped_log.nii'),
            contFile=os.path.join(self.nii_folder, 'ex_3d_contour.nii'),
            outFile=os.path.join(self.nii_folder, 
                            'ex_3d_cropped_log_masked.nii'),
            label=1)
    )
    
    update(self, key, output)

def step2_4(self):
    '''Step2: 11 - 13'''
    key = 'step2_4'

    # 11. Manual alignment of in 3d to ex 3d
    ex_3d = slicer.util.loadVolume(
                os.path.join(self.nii_folder, '(ex_3d)_to_(ex_2d).nii'))
    
    in_3d = slicer.util.loadVolume(
                os.path.join(self.nii_folder, 'in_3d.nii'))
    
    # Manual adjustment
    in_3d_contour = slicer.util.loadLabelVolume(
                            os.path.join(self.nii_folder, 'in_3d_contour.nii'))
    tfm_manual_path = os.path.join(self.tfm_folder, '(ex_xd)_to_(in_3d).tfm')
    if not os.path.exists(tfm_manual_path):
        tfm_manual = slicer.vtkMRMLLinearTransformNode()
        slicer.mrmlScene.AddNode(tfm_manual)
        tfm_manual.SetName('(ex_xd)_to_(in_3d)')
    else:
        tfm_manual = slicer.util.loadTransform(tfm_manual_path)
        print('Loaded: ', tfm_manual_path)
    ex_3d.SetAndObserveTransformNodeID(tfm_manual.GetID())
    selectModule(slicer.modules.transforms)
    try:
        _ = input("Please manually adjust the manual alignment. \n\
                   1. Select (ex_xd)_to_(in_3d) as the active transform; \n\
                   2. Use the slider to adjust the alignment; \n\
                   3. Press ENTER to continue.")
    except:
        pass

    print('*'*20, 'Done', '*'*20)

    # Save the transformation
    saved = slicer.util.saveNode(tfm_manual, tfm_manual_path)
    if saved:
        output = {tfm_manual_path: True}
    tfm_manual.Inverse()

    tfm_manual_inv_path = os.path.join(self.tfm_folder, '(in_3d)_to_(ex_xd).tfm')
    saved = slicer.util.saveNode(tfm_manual, tfm_manual_inv_path)
    if saved:
        output.update({tfm_manual_inv_path: True})

    # Save the scene in case of fine adjustment
    slicer.util.saveScene(os.path.join(self.temp_folder, '11_manual_alignment.mrb'))
    selectModule(slicer.modules.pyregpipe)
    slicer.mrmlScene.Clear(0)

    # 12. Resample in_3d_log_masked into ex_3d_cropped
    output.update(
        warpImg(inImg=os.path.join(self.nii_folder, 'in_3d_log_masked.nii'),
            refImg=os.path.join(self.nii_folder, 'ex_3d_cropped.nii'),
            outImg=os.path.join(self.nii_folder,
                '(in_3d_log_masked)_into_(ex_3d_cropped)_linear.nii'),
            pixelT='float',
            tfmFile=os.path.join(self.tfm_folder, '(in_3d)_to_(ex_xd).tfm'),
            intplMode='Linear',
            labelMap=False)
    )
    
            
    # 13. Resample in_3d into ex_3d_cropped
    output.update(
        warpImg(inImg=os.path.join(self.nii_folder, 'in_3d.nii'),
            refImg=os.path.join(self.nii_folder, 'ex_3d_cropped.nii'),
            outImg=os.path.join(self.nii_folder,
                '(in_3d)_into_(ex_3d_cropped)_linear.nii'),
            pixelT='float',
            tfmFile=os.path.join(self.tfm_folder, '(in_3d)_to_(ex_xd).tfm'),
            intplMode='Linear',
            labelMap=False)
    )
    update(self, key, output)
            

def step2_5(self):
    '''Step 2: 14'''
    key = 'step2_5'

    filesCopy = ['ex_3d_cropped_log_masked.nii', 
             '(in_3d_log_masked)_into_(ex_3d_cropped)_linear.nii',
             '(in_3d)_into_(ex_3d_cropped)_linear.nii']
             
    for eachFile in filesCopy:
        shutil.copy(os.path.join(self.nii_folder, eachFile), 
                    os.path.join(self.cmtk_folder, eachFile))

    params = (self.cmtk_path, self.cmtk_folder, *filesCopy)
    genCmtkScript(os.path.join(self.cmtk_folder, 'warp.sh'), params)
    warpFile = os.path.join(self.cmtk_folder, 'warp.sh')

    # Locate the warp.sh in case the user needs to change it
    Popen(f'explorer.exe /select, "{os.path.realpath(warpFile)}"')
    try:
        input("Modify the warp.sh scrip if necessary.\nPress ENTER to continue: ")
    except:
        pass
    
    cmd = '"%s" "%s"' % (self.bash_path, warpFile )
    runCmd(cmd)

    # Add the output to the filelist
    outFullpath = [os.path.join(self.cmtk_folder, i) for i in self.cmtkOutput]
    output = {i: os.path.exists(i) for i in outFullpath}
    update(self, key, output)


def step2_6(self):
    '''Resample the data to ex_3d_cropped (rigidly) and 
        ex_3d_cropped_deformable (deformably)
    '''
    key = 'step2_6'
    files = {
        'in_3d.nii': '(in_3d)_into_(ex_3d_cropped).nii',
        'in_3d_contour.nii': '(in_3d_contour)_into_(ex_3d_cropped).nii',
        'in_3d_log_masked.nii': '(in_3d_log_masked)_into_(ex_3d_cropped).nii'
    }

    otherFile = [
        '(in_2d)_to_(in_3d).nii',
        '(in_adc)_to_(in_3d).nii',
        # '(in_twist#)_to_(in_3d).nii',
        '(in_dwi_b50)_to_(in_3d).nii',
        '(in_bold_echo2)_to_(in_3d).nii'
    ]

    # Define the possible PK maps
    pkMaps = [f'({os.path.splitext(i)[0]})_to_(in_3d).nii' for i in self.pkMaps]

    # Add them to otherFile
    otherFile += pkMaps

    # Update the output file names
    files.update({i:i.split('_to_')[0]+'_into_(ex_3d_cropped).nii' for i in otherFile})
    if self.hasBold:
        files.update({'(in_r2star)_to_(in_3d).nii': '(in_r2star)_into_(ex_3d_cropped).nii'})

    output = {}

    for eachF in files:
        inImgL = os.path.join(self.nii_folder, eachF)

        # Skip not existed files (possible for PK maps)
        if not os.path.exists(inImgL):
            print(f'Skipping {eachF}')
            continue

        refImgL = os.path.join(self.nii_folder, 'ex_3d_cropped.nii')
        outImgL = os.path.join(self.nii_folder, files[eachF])
        tfmFileL = os.path.join(self.tfm_folder, '(in_3d)_to_(ex_xd).tfm')
        
        # Use nearest neighbour for in_3d_contour
        nearestNFiles = ['in_3d_contour.nii', '(in_dce_gd)_to_(in_3d).nii']
        intplMode = 'NearestNeighbor' if eachF in nearestNFiles else 'Linear'

        # Rigid resampling
        output.update(
            warpImg(inImg=inImgL,
                    refImg=refImgL,
                    outImg=outImgL,
                    pixelT='float',
                    tfmFile=tfmFileL,
                    intplMode=intplMode,
                    labelMap=False)
        )

        # Deformable resampling
        # deformWarp(cmtkPath, inImg, refImg, outImg, xform, scrPath, bashPath)
        inImgD = outImgL
        refImgD = os.path.join(self.nii_folder, 'ex_3d_cropped.nii')
        outImgD = os.path.join(self.nii_folder, files[eachF].split('.')[0]+'_deformable.nii')
        xform = os.path.join(self.cmtk_folder, 'warp_output_transform')
        scrPath = os.path.join(self.script_folder, 
                               f"warp_{eachF.split('.')[0]}_{int(time.time())}.sh")
        output.update(
            deformWarp(cmtkPath=self.cmtk_path,
                    intplMode='--nn' if eachF in nearestNFiles else '--linear',
                    inImg=inImgD,
                    refImg=refImgD,
                    outImg=outImgD,
                    xform=xform,
                    scrPath=scrPath,
                    bashPath=self.bash_path)
        )
    
    update(self, key, output)

def step2_7(self):
    pass

def step2_8(self):
    pass

