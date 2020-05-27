# PyRegPipe
The automatic registration framework using Python for 3D Slicer, developed for the BiRT project.

Maintained by Yu Sun, yu.sun@sydney.edu.au

## Design
This framework utilises the Python environment in 3D Slicer for automating the registration steps developed by Reynolds, *et al*. 

> `Med Phys. 2015 Dec;42(12):7078-89. doi: 10.1118/1.4935343.`

Versions at the time of creation:
* Python v3.6.7
* 3D Slicer v4.11.0

## Modules
There are currently four modules (under the `main` folder):
* `PyRegPipe.py`: the main module which implements the steps to perform *in vivo* to *ex vivo* registration. 
* `ToNIfTI.py`: a module for converting DYNAMIKA DICOM to NIfTI files
* `PrepPk.py`: a module for preparing the folders for DYNAMIKA pharmacokinetic maps.
* `WarpImg.py`: (for heritage files) a module for warping images from the *in vivo* space into the *ex vivo* space, given the exisitng CMTK transformation folder.
