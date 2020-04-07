def genCmtkScript(path, params):
    '''Generate and save the script.'''
    template = '''#!/bin/bash
# deformable registration

    cmtk_path="%s"
          dir="%s"
    outputDir=$dir
        fixed=$dir"/%s"
     floating=$dir"/%s"
reformatImage=$dir"/%s"

outFloatingReformated=$dir"/(in_3d_log_masked)_into_(ex_3d_cropped)_deformable.nii"
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
'''
    cmd = template % params
    with open(path, 'w') as f:
        f.write(cmd)
        
    return True
