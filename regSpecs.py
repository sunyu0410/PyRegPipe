import sys
import os

# Add the code folder to the path
topFolder = os.path.abspath(os.path.join(sys.executable, *([os.pardir]*4)))
sys.path.append(os.path.join(topFolder, 'code'))

import regFunc

specs = dict(
            step1_1 = dict(
                step = 'step1',
                key = 'step1_1',
                stepLabel = '''Tasks:
                # 1. Convert in_2d & in_3d to NIfTI;
                # 2. Coregister in_2d to in_3d;
                # 3. Reverse the transformation file;
                ''',
                btnFunc = regFunc.step1_1,
                title = 'T2w Images',
                shortDesc='T2w Images'
            ),

            step1_2 = dict(
                step = 'step1',
                key = 'step1_2',
                stepLabel = '''Tasks:
                # 1. Create a folder for sorted DWI .dcm files
                # 2. Sort the DWI data
                # 3. Convert the b=50 dcm files to in_dwi_b50.nii
                # 4. Rigid registration to in_3d
                # 5. Create the (in_dwi_b50)_in_(in_3d).nii
                # 6. Convert ADC to in_adc.nii
                # 7. Apply (in_dwi_b50)_to_(in_3d).tfm on in_adc
                ''',
                btnFunc = regFunc.step1_2,
                title = 'DWI',
                shortDesc='DWI'
            ),

            step1_3 = dict(
                step = 'step1',
                key = 'step1_3',
                stepLabel = '''Tasks:
                # 1. Sort the .dcm data
                # 2. Conver the second echo time (9.84 ms) to .nii
                # 3. Co-register to in_3d
                # 4. Generate R2* map
                # 5. Copy the header information
                # 6. Check the r2star map
                ''',
                btnFunc = regFunc.step1_3,
                title = 'BOLD',
                shortDesc= 'BOLD'
            ),

            step1_4 = dict(
                step = 'step1',
                key = 'step1_4',
                stepLabel = '''Tasks:
                # 1. Find the slice for motion correction
                # 2. Registered in_twist to in_3d
                # 3. Convert the phamacokinetic maps to NIfTI
                ''',
                btnFunc = regFunc.step1_4,
                title = 'DCE-MRI',
                shortDesc= 'DCE-MRI'
            ),

            step2_1 = dict(
                step = 'step2',
                key = 'step2_1',
                stepLabel = '''Tasks:
                # 1 - (0) Convert ex vivo T2w images from DICOM to NIfTI
                #       Create an identity transform
                # 2. (1) Convert in_2d_contour and ex_2d_contour to NIfTI
                #       Apply mophological operations (close) to eliminate holes
                # 3. (2) Register in_3d into in_2d (already done so in Step 1)
                # 4. (3) Convert in_2d_contour to in_3d_contour
                #       Resampling
                #       LabelMapSmoothing
                ''',
                btnFunc = regFunc.step2_1,
                title = 'Conversion',
                shortDesc= 'ex vivo T2w + contours'
            ),

            step2_2 = dict(
                step = 'step2',
                key = 'step2_2',
                stepLabel = '''Tasks:
                # 4. (4) Register ex vivo 3D with ex vivo 2D
                        Manual alignment
                        Rigid registration
                ''',
                btnFunc = regFunc.step2_2,
                title = 'Ex vivo 2D & 3D',
                shortDesc= 'Manual align + rigid reg'
            ),

            step2_3 = dict(
                step = 'step2',
                key = 'step2_3',
                stepLabel = '''Tasks:
                # 1. (5) Convert ex 2d contour to ex 3d contour
                # 2. (6) Crop ex 3d as a reference image
                # 3. (7) Filter in 3d
                # 4. (8) Filter ex 3d cropped
                # 5. (9) Mask in 3d log with manual contour
                # 6. (10) Mask ex 3d cropped log with the manual contour
                ''',
                btnFunc = regFunc.step2_3,
                title = 'Crop and mask',
                shortDesc= 'Crop and mask'
            ),

            step2_4 = dict(
                step = 'step2',
                key = 'step2_4',
                stepLabel = '''Tasks:
                # 1. (11) Manual alignment of in 3d to ex 3d
                # 2. (12) Resample in_3d_log_masked into ex_3d_cropped    
                # 3. (13) Resample in_3d into ex_3d_cropped
                ''',
                btnFunc = regFunc.step2_4,
                title = 'Manual align and resample',
                shortDesc= 'Manual align and resample'
            ), 

            step2_5 = dict(
                step = 'step2',
                key = 'step2_5',
                stepLabel = '''Tasks:
                # 1. (14) Deformable registration using CMTK
                ''',
                btnFunc = regFunc.step2_5,
                title = 'Deformable reg',
                shortDesc= 'Run with CMTK'
            ),

            step2_6 = dict(
                step = 'step2',
                key = 'step2_6',
                stepLabel = '''Tasks:
                # 1. Resample the data rigidly to ex_3d_cropped
                # 2. Resample the data deformably to ex_3d_cropped_deformable
                ''',
                btnFunc = regFunc.step2_6,
                title = 'Resample data',
                shortDesc= 'Resample data'
            )
        )
        