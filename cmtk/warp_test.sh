#!/bin/bash
# deformable registration

    cmtk_path="F:/Tools/CMTK-2.3.0-Windows-x86/bin"
          dir="F:/prj3/cmtk"
    outputDir=$dir
        fixed=$dir"/ex_3d_cropped_log_masked.nii"
     floating=$dir"/(in_3d_log_masked)_into_(ex_3d_cropped)_linear.nii"
reformatImage=$dir"/(in_3d)_into_(ex_3d_cropped)_linear.nii"

outFloatingReformated=$dir"/(in_3d_LoG_masked)_into_(ex_3d_cropped)_deformable.nii"
outFinal=$dir"/(in_3d)_into_(ex_3d_cropped)_deformable.nii"
outXform=$dir"/warp_output_transform"

mkdir $outXform

options=""
options=$options" --write-reformatted "$outFloatingReformated
options=$options" --output-intermediate"
options=$options" --omit-original-data"
options=$options" --sampling 1"
options=$options" --outlist "$outXform
options=$options" --rigidity-weight 0.01"
export CMTK_WRITE_UNCOMPRESSED=1

echo "$cmtk_path"/warp.exe $options $fixed  $floating
     "$cmtk_path"/warp.exe $options $fixed  $floating


echo "$cmtk_path"/reformatx -o $outFinal --floating $reformatImage $fixed $outXform
     "$cmtk_path"/reformatx -o $outFinal --floating $reformatImage $fixed $outXform
