# Convert the dynamics DICOM files to fodler structures.
# The folder structure is required for using the Python 
#   registration framework.
#
# Use: run the following code in the Python console within 3D Slicer. 
#      Replace the path with the real path.
#
# exec(open(r'topFolder/code/dce.py', 'r').read())
# 

import os
import sys

# Add the code folder to the path
topFolder = os.path.abspath(os.path.join(sys.executable, *([os.pardir]*4)))
sys.path.append(os.path.join(topFolder, 'code'))

from reg import sortDcm

def sortDce():
    '''Convert the dynamics DICOM files to fodler structures.
    The folder structure is required for using the Python registration framework.
    No input argument, but will prompt you for selecting two folders,
        one for source, one for destination.
    Saves the sorted data to the destination folder.
    '''
    print("DCE-MRI data sorting")
    dialog = ctk.ctkFileDialog()
    print("  Please select the source folder")
    sourceFolder = dialog.getExistingDirectory()
    if sourceFolder:
        print("    Source folder: ", sourceFolder)
    else:
        print("    No folder select. Task terminated.")
        sys.exit()
    print("  Please select the destination folder for the sorted DICOM")
    destFolder = dialog.getExistingDirectory()
    if destFolder:
        print("    Destination folder: ", destFolder)
    else:
        print("    No folder select. Task terminated.")
        sys.exit()
    print("  Processing ... ")
    sortDcm(sourceFolder, destFolder, 'dce')
    print("  Completed.")
    print()

sortDce()