#!/bin/bash

cmtk_path=$1
reformatImage=$2
referenceImage=$3
output=$4
xform=$5

#cmtk_path="C:/Program Files (x86)/CMTK-2.2/Program Files/CMTK/bin"
# reformatImage="C:/aworkspace/peter_mac/data/patients/patient_8/registration/working/into_[ex_3d]/(in_2d_adc)_into_(ex_3d_cropped)_linear.nii"
#referenceImage="C:/aworkspace/peter_mac/data/patients/patient_8/registration/working/ex_3d_cropped.nii"
#         xform="C:/aworkspace/peter_mac/data/patients/patient_8/registration/working/into_[ex_3d]/[in_3d_LoG_masked]_into_[ex_3d_LoG_masked]/warp_output_transform"
#output="C:/temp/warped.nii"


export CMTK_WRITE_UNCOMPRESSED=1
echo "$cmtk_path"/reformatx -o $output --floating $reformatImage $referenceImage $xform
     "$cmtk_path"/reformatx -o $output --floating $reformatImage $referenceImage $xform
