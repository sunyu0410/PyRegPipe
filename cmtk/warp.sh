#!/bin/bash
# deformable registration

#cmtk_path=$1
#cmtk_path="C:/Program Files (x86)/CMTK-2.2/Program Files/CMTK/bin"
cmtk_path="C:/Program Files (x86)/CMTK-2.3.0-Windows-x86/Program Files/CMTK/bin"

#dir=$2
#dir="C:/aworkspace/peter_mac/data/patients/patient_5/registration_instructions"
dir="C:/registration/working"

    outputDir=$dir
        fixed=$dir"/ex_3d_cropped_LoG_masked.nii"
     floating=$dir"/(in_3d_LoG_masked)_into_(ex_3d_cropped)_linear.nii"
reformatImage=$dir"/(in_3d)_into_(ex_3d_cropped)_linear.nii"

outFloatingReformated=$dir"/(in_3d_LoG_masked)_into_(ex_3d_cropped)_deformable.nii"
outFinal=$dir"/(in_3d)_into_(ex_3d_cropped)_deformable.nii"
outXform=$dir"/warp_output_transform"

# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------

mkdir $outXform

# - "sampling" is the finest resampled (!) image resolution in the multi-resolution pyramid.
# Say you have 1mm voxel size in your input data. By default, the first resampled resolution is
# 2x original, i.e., here 2mm. You can use "sampling" ton increase this value, say, to 4mm to
# make things faster. This is particularly effective when you also use the "omit-original-data"
# option, because otherwise the multi-res pyramid will still have the original resolution images
# in it (which is of course slow).

options=""
#options=$options" --initial C:/aworkspace/peter_mac/data/patients/patient_8/registration/(ex_xd)_into_(in_2d).tfm" # note: CMTK does not respect initial transformation, nor the geometric values in .nii
options=$options" --write-reformatted "$outFloatingReformated
#options=$options" --fast" # don't use this, affects accuracy
options=$options" --output-intermediate"
options=$options" --omit-original-data"
options=$options" --sampling 1" # don't use samples > 1 effects accuracy
options=$options" --outlist "$outXform
#options=$options" --pad-flt 0"
#options=$options" --sobel-filter-flt"
#options=$options" --sobel-filter-ref"
#options=$options" --registration-metric nmi"
options=$options" --rigidity-weight 0.01" #0.01
#options=$options" --jacobian-weight 3" # default 0
#options=$options" --energy-weight 0.1" # default 0
#options=$options" --ic-weight 0.1" # inverse consistency default 0
#options=$options" --match-histograms"



export CMTK_WRITE_UNCOMPRESSED=1

echo "$cmtk_path"/warp.exe $options $fixed  $floating
     "$cmtk_path"/warp.exe $options $fixed  $floating


echo "$cmtk_path"/reformatx -o $outFinal --floating $reformatImage $fixed $outXform
     "$cmtk_path"/reformatx -o $outFinal --floating $reformatImage $fixed $outXform

	 
	 
	 
	 
	 
	 
	 