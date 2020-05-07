import os
import shutil
import slicer
import time
import math
import numpy as np
import matplotlib
import matplotlib.cm as cm
import SimpleITK as sitk
from subprocess import Popen, PIPE
from pydicom import read_file

matplotlib.use('WXAgg')
import matplotlib.pyplot as plt

def getDcmAttr(dcmPath, key):
    '''Get the header attribute in the DICOM file given the key
    dcmPath: the path for the DICOM file;
    key: the key for the header in a tuple, e.g. ('0019', '100c').'''
    dcm = read_file(dcmPath)
    return dcm.get_item(key).value

def sortDcm(path, outDir, _type):
    '''Sort the DICOM files based on a specific key
    For example, DWI images with different b-values
    path: path to the dicom folder;
    outDir: the output directory with subfolders for sorted dcm files;
            It needs to be an unexisted or empty folder.
    _type: the imaging modality, one of "dwi", "bold" or "dce".'''

    # DWI: ('0019', '100c')
    # BOLD: ('0018', '0081')        TE (ms)
    # DCE-MRI: ('0020', '0012')     Acquisition Number
    if _type == 'dwi':
        key = ('0019', '100c')
    elif _type == 'bold':
        key = ('0018', '0081')
    elif _type == 'dce':
        key = ('0020', '0012')
    
    filelist = os.listdir(path)

    result = {}
    
    for eachF in filelist:
        filepath = os.path.join(path, eachF)
        attr = getDcmAttr(filepath, key).strip().decode('utf-8')
        result.setdefault(attr, []).append(eachF)
    
    # # Uncomment to forbid overwriting files
    # if os.path.exists(outDir):
    #     outDir_contents = os.listdir(outDir)
    #     if outDir_contents:
    #         raise Exception("Output folder must be empty. Task terminated.")

    for eachKey in result:
        subfolder = os.path.join(outDir, eachKey)
        if not os.path.exists(subfolder):
            os.makedirs(subfolder)
        for eachF in result[eachKey]:
            sourcePath = os.path.join(path, eachF)
            destPath = os.path.join(subfolder, eachF)
            shutil.copy(sourcePath, destPath)
    return True

def cvtSlicer(path, outDir, filename):
    '''Convet an imaging file (specified by file extensions).
    path: the path to the file or the source folder (for .dcm);
    outDir: the output directory to save the NIfTI file;
    filename: the filename to be saved as;
    '''
    # If path is a folder, replace it with the path for the 1st file
    if os.path.isdir(path):
        filelist = os.listdir(path)
        path = os.path.join(path, filelist[0])
    # Load the file
    node = slicer.util.loadVolume(path)
    savepath = os.path.join(outDir, filename)
    saved = slicer.util.saveNode(node, savepath)
    slicer.mrmlScene.RemoveNode(node)
    return saved
    
def cvtITK(path, outDir, filename):
    '''Convert a folder of DICOM files to another format (specified by file extensions
    using SimpleITK
    path: the path to the DICOM folder;
    outDir: the output directory to save the file;
    filename: the filename to be saved.
    '''
    reader = sitk.ImageSeriesReader()
    dicom_names = reader.GetGDCMSeriesFileNames(path)
    reader.SetFileNames(dicom_names)
    image = reader.Execute()
    outfile = os.path.join(outDir, filename)
    sitk.WriteImage(image, outfile)
    return {outfile: True}

def rigidReg(fixedImg, movingImg, outTfm, outImg=None, initTfm=None):
    '''Rigid registration using BRAINS Registration
    fixedImg: full path to the fixed image;
    movingImg: full path to the moving image;
    outImg: full path to the output co-registered image;
    outTfm: full path to the output transform file (.tfm).
    '''
    slicer.mrmlScene.Clear(0)
    fixed = slicer.util.loadVolume(fixedImg)
    moving = slicer.util.loadVolume(movingImg)
    cliModule = slicer.modules.brainsfit
    p = {}
    p['fixedVolume'] = fixed.GetID()
    p['movingVolume'] = moving.GetID()
    outVolume = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(outVolume)
    p['outputVolume'] = outVolume.GetID()
    p['transformType'] = 'Rigid'
    tfm = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(tfm)
    p['outputTransform'] = tfm.GetID()
    if initTfm:
        _tfm = slicer.util.loadTransform(initTfm)
        p['initialTransform'] = _tfm.GetID()
    slicer.cli.run(cliModule, None, p, wait_for_completion=True)
    result = {}
    if outImg:
        state1 = slicer.util.saveNode(outVolume, outImg)
        result.update({outImg: state1})
    state2 = slicer.util.saveNode(tfm, outTfm)
    result.update({outTfm: state2})
    slicer.mrmlScene.Clear(0)
    return result
    
def invertTfm(tfmFile, outFile):
    '''Invert an existing linear .tfm file
    tfmFile: full path to the .tfm file;
    outFile: full path to the output .tfm file.
    '''
    tfm = slicer.util.loadTransform(tfmFile)
    tfm.Inverse()
    saved = slicer.util.saveNode(tfm, outFile)
    slicer.mrmlScene.Clear(0)
    return {outFile: saved}

def warpImg(inImg, refImg, outImg, pixelT, tfmFile, intplMode, labelMap=False):
    '''Resample an image using an exisiting transform.
    inImg: full path to the input image (to be resampled);
    refImg: full path to the reference image;
    outImg: full path to the output image (resampled image);
    pixelT: pixel type, options include
            float, short, ushort, int, uint, uchar, binary
    tfmFile: full path to the transform image;
    intplMode: interpolation mode, options include
            Linear, NearestNeighbor, BSpline, WindowedSinc.
    '''
    slicer.mrmlScene.Clear(0)
    if labelMap:
        inimg = slicer.util.loadLabelVolume(inImg)
        outVolume = slicer.vtkMRMLLabelMapVolumeNode()
    else:
        inimg = slicer.util.loadVolume(inImg)
        outVolume = slicer.vtkMRMLScalarVolumeNode()
    refimg = slicer.util.loadVolume(refImg)
    tfm = slicer.util.loadTransform(tfmFile)
    slicer.mrmlScene.AddNode(outVolume)
    cliModule = slicer.modules.brainsresample
    p = {}
    p['inputVolume'] = inimg.GetID()
    p['referenceVolume'] = refimg.GetID()
    p['outputVolume'] = outVolume.GetID()
    p['pixelType'] = pixelT
    p['warpTransform'] = tfm.GetID()
    p['interpolationMode'] = intplMode
    slicer.cli.run(cliModule, None, p, wait_for_completion=True)
    state = slicer.util.saveNode(outVolume, outImg)
    slicer.mrmlScene.Clear(0)
    return {outImg: state}

def dceMotCorFolder(path, num):
    '''Find the specific T1 subfolder for DYNAMIKA motion correction.
    path: the parent folder for the dynamic series
              (containing multiple subfolders);
    num: the slice number for motion correction;
    '''
    subfolders = os.listdir(path)
    result = {}
    for eachF in subfolders:
        subfolder_path = os.path.join(path, eachF)
        filelist = os.listdir(subfolder_path)
        first_file = os.path.join(path, subfolder_path, filelist[0])
        result[eachF] = getDcmAttr(first_file, ('0020', '0012')).strip().decode('utf-8')
    theFolder = [i for i in subfolders if result[i]==str(num)]
    assert len(theFolder) == 1
    return os.path.join(path, theFolder[0])

def genR2Star(macro_path, exe_path='imagej'):
    '''Generate the R2* map using ImageJ by running a macro file.
    Make sure the path of ImageJ is setup properly.
    macro_path: the path for the macro.
                e.g. F:\Registration\registration\compare\imj\test.imj
    '''
    cmd = '%s -macro %s' % (os.path.normpath(exe_path), 
                            os.path.normpath(macro_path))
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    return p.communicate()

def copyHeader(_file, refFile, outDir, tempFolder):
    '''Copy the header information in the refFile to _file.
    _file: the full path to the target file;
    refFile: the full path to the reference file (with a correct header)
    outDir: the output directory;
    tempFolder: the folder to hold the temporary files.
    '''
    # Create a temp file for .mhd files
    temp_folder = os.path.join(tempFolder, 'temp_'+str(time.time()))
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    # Convert to .mhd
    _file_temp_name = os.path.splitext(os.path.split(_file)[-1])[0] + '.mhd'
    refFile_temp_name = os.path.splitext(os.path.split(refFile)[-1])[0] + '.mhd'
    cvtSlicer(_file, temp_folder, _file_temp_name)
    cvtSlicer(refFile, temp_folder, refFile_temp_name)
    # Copy the coordinate information
    _file_header = open(os.path.join(temp_folder, _file_temp_name)).readlines()
    refFile_header = open(os.path.join(temp_folder, refFile_temp_name)).readlines()
    _file_header_key = [i.split()[0] for i in _file_header]
    _file_range = (_file_header_key.index('TransformMatrix'),
                   _file_header_key.index('ElementSpacing'))
    refFile_header_key = [i.split()[0] for i in refFile_header]
    refFile_range = (refFile_header_key.index('TransformMatrix'),
                     refFile_header_key.index('ElementSpacing'))
    result = _file_header[:_file_range[0]] + \
             refFile_header[refFile_range[0]:(refFile_range[1]+1)] + \
             _file_header[(_file_range[1]+1):]
    # Override the original .mhd file
    with open(os.path.join(temp_folder, _file_temp_name), 'w') as f:
        f.writelines(result)
    # Convert back to .nii
    cvtSlicer(os.path.join(temp_folder, _file_temp_name),
              outDir,
              os.path.splitext(os.path.split(_file)[-1])[0] + '.nii')
    return True

def dilateLabelMap(imgFile, outFile, radius=1, value=1):
    '''Dilate a label map using Simple ITK
    This is originally done in 3D Slicer - Editor.
    The end result is highly comparable.
    imgFile: full path to the image file;
    outFile: full path to the output file;
    radius: the dialtion radius;
    value: the pixel intensity of the label map.
    '''
    image = sitk.ReadImage(imgFile)
    f = sitk.BinaryDilateImageFilter()
    f.SetKernelRadius(radius)
    f.SetForegroundValue(value)
    dilated = f.Execute(image)
    sitk.WriteImage(dilated, outFile)

def labelMapSmoothing(inImg, outImg, sigma=0.2):
    '''Label map smoothing using slicer.cli.run()
    inImg: the input image path. Expects a label map;
    outImg: the output image (to be saved) path;
    sigma: the Gaussian sigma for smoothing.'''
    node = slicer.util.loadLabelVolume(inImg)
    cliModule = slicer.modules.labelmapsmoothing
    outVolume = slicer.vtkMRMLLabelMapVolumeNode()
    slicer.mrmlScene.AddNode(outVolume)
    p = {}
    p['inputVolume'] = node.GetID()
    p['outputVolume'] = outVolume.GetID()
    p['gaussianSigma'] = sigma
    slicer.cli.run(cliModule, None, p, wait_for_completion=True)
    slicer.util.saveNode(outVolume, outImg)
    dilateLabelMap(outImg, outImg)
    slicer.mrmlScene.Clear(0)
    return {outImg: True}

def genLogMacro(infile, outfile, macroPath):
    '''Generate the ImageJ macro for the LoG filter.
    infile: the path of the input file;
    outfile: the path of the output file;
    macroPath: the path for the macro to be saved.'''
    path, fname = os.path.split(infile)
    cmd = 'open("%s");\n' % infile.replace('\\', '\\\\')
    cmd += 'run("LoG 3D");\n'
    cmd += 'selectWindow("LoG of %s");\n' % fname
    cmd += 'run("NIfTI-1", "save=[%s]");\n' % \
                outfile.replace('\\', '\\\\')
    cmd += 'eval("script", "System.exit(0);");\n'
    
    with open(macroPath, 'w') as f:
        f.write(cmd)
        
    node = slicer.util.loadVolume(infile)
    spacing = [round(1.25/i, 4) for i in node.GetSpacing()]
    print("Use the following input: x: %s, y: %s, z: %s" % \
            tuple(spacing))
            
    slicer.mrmlScene.Clear(0)
  
    return True
    
def filterLoG(macro_path, exe_path):
    '''Apply the LoG filer using the macro specified by the macro_path'''
    cmd = '%s -macro %s' % (os.path.normpath(exe_path), 
                            os.path.normpath(macro_path))
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    return p.communicate()
    
def maskVolume(infile, contFile, outFile, label=1):
    '''Mask a volume using a label map.
    infile: path pf the input file;
    contFile: path of the contour file (label map);
    outFile: path of the masked file (to be saved);
    label: the value of the label map;
    '''
    inputVolume = slicer.util.loadVolume(infile)
    maskVolume = slicer.util.loadLabelVolume(contFile)
    cliModule = slicer.modules.maskscalarvolume
    outputVolume = slicer.vtkMRMLScalarVolumeNode()
    slicer.mrmlScene.AddNode(outputVolume)
    p = {}
    p['InputVolume'] = inputVolume.GetID()
    p['MaskVolume'] = maskVolume.GetID()
    p['OutputVolume'] = outputVolume.GetID()
    p['Label'] = 1
    slicer.cli.run(cliModule, None, p, wait_for_completion=True)
    state = slicer.util.saveNode(outputVolume, outFile)
    slicer.mrmlScene.Clear(0)
    return {outFile: state}
    
def sortDicom(folderPath, saveFolder, key=('0020', '0013'), reverse=False):
    '''Sort the DICOM file based slot (0020, 0013): Image Number'''
    fl = os.listdir(folderPath)
    attrs = []
    for eachF in fl:
        attr = getDcmAttr(os.path.join(folderPath, eachF), key)
        attrs.append(int(attr))
    if reverse:
        maximum = max(attrs)
        attrs = [maximum + 1 - i for i in attrs]
    for (attr, eachF) in zip(attrs, fl):
        newFileName = 'MR.%s.dcm' % str(attr).zfill(4)
        shutil.copy(os.path.join(folderPath, eachF),
                    os.path.join(saveFolder, newFileName))
    return True
    
def checkOrient(saveFolder, nRow=5, cMap=cm.Greys_r):
    '''Check the orientation of the ex 2d images.
    MR.0001 - apex
    MR.00xx - based
    '''
    fl = sorted(os.listdir(saveFolder))
    arrays = [pydicom.read_file(os.path.join(saveFolder, eachF)).pixel_array for eachF in fl]
    nCol = math.ceil(len(fl) / nRow)
    fig, ax = plt.subplots(ncols=nCol, nrows=nRow)
    
    for i in range(nCol*nRow):
        arr = arrays[i] if i < len(fl) else np.array(arrays[0].shape)
        region = ax[i//nCol][i%nCol]
        region.imshow(arr, cmap=cMap)
        region.axis('off')
        region.title.set_text(fl[i])
    
    plt.show()
    
def getParam(cliModule):
    '''Get the parameters of a Slicer CLI module
    Refer to https://www.slicer.org/wiki/Documentation/Nightly/Developers/Python_scripting
    '''
    n = cliModule.cliModuleLogic().CreateNode()
    for groupIndex in range(0,n.GetNumberOfParameterGroups()):
        for parameterIndex in range(0,n.GetNumberOfParametersInGroup(groupIndex)):
            print('  Parameter ({0}/{1}): {2} ({3})'.format(groupIndex, parameterIndex,
                        n.GetParameterName(groupIndex, parameterIndex),
                        n.GetParameterLabel(groupIndex, parameterIndex)))

def createPrjFolder(topDir):
    '''Create a project folder template for copying over the files.
    topDir: the absolute path of the top-level folder.
            This must be a non-existing folder.
    '''
    dataFolder = os.path.join(topDir, 'data')
    inFolder = os.path.join(dataFolder, 'in_vivo_mri')
    inData = ['in_2d', 'in_3d', 'dwi', 'adc', 'bold', 'dynamic', 'pk']
    inDataFolders = [os.path.join(inFolder, i) for i in inData]
    for eachF in inDataFolders:
        if not os.path.exists(eachF):
            os.makedirs(eachF)
    return True
    
def morphProcess(inPath, outPath, operation, radius=None):
    '''Apply a morphological operation on a binary label map.
    inPath: the path of the imput image;
    outPath: the path to saved the processed image;
    operation(string): must be 'dilate', 'erode' or 'close';
    radius: the radius for the morphological processing.
    Saves the processed image as a file'''
    reader = sitk.ImageFileReader()
    reader.SetFileName(inPath)
    img = reader.Execute()
    funcs = dict(dilate=sitk.BinaryDilate,
                 erode=sitk.BinaryErode,
                 close=sitk.BinaryMorphologicalClosing)
    if operation not in funcs.keys():
        raise Exception("Invalid operation, must be dilate, erode or close")
    else:
        func = funcs[operation]
        img_prc = func(img, radius) if radius else func(img)
        sitk.WriteImage(img_prc, outPath)
        return True

def logFilter(inFile, outFile):
    '''Apply the LoG filter on an image.
    inFile: the path to the input file;
    outFile: the path of the output file;
    Saves the result to outFile.'''
    reader = sitk.ImageFileReader()
    reader.SetFileName(inFile)
    img = reader.Execute()
    logFilter = sitk.LaplacianRecursiveGaussianImageFilter()
    sigma = 1.25 / img.GetSpacing()[0]
    logFilter.SetSigma(sigma)
    img_log = logFilter.Execute(img)
    sitk.WriteImage(img_log, outFile)
    return {outFile: True}
    
def runCmd(cmd):
    '''Run the command, return the ouptut and error.
    cmd: the command in a string.
    Returns the stdout and stderr.'''
    print(f"Running: {cmd}")
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    return p.communicate()

def flipArr(arr, mode):
    '''Flip an array
    arr: the input numpy array;
    mode: one of left-right 'si', anterior-posterior 'ap' and left-right 'lr';
    Returns the flipped array.'''
    axis = {
        'si': 0,
        'ap': 1,
        'lr': 2
    }
    if mode not in axis.keys():
        raise Exception(f"mode must be one of {axis.keys()}")
    
    return np.flip(arr, axis[mode])
    
def flipFile(inFile, outFile, mode):
    '''Read the image and save the flipped image.
    inFile: path to the input image;
    outFile: path to the output image;
    mode: one of left-right 'si', anterior-posterior 'ap' and left-right 'lr';
          will be passed to flipArr(arr, mode).
    The resultant image will be saved to outFile.'''
    axis = {
        'si': 0,
        'ap': 1,
        'lr': 2
    }
    if mode not in axis.keys():
        raise Exception(f"mode must be one of {axis.keys()}")
    node = slicer.util.loadVolume(inFile)
    array = slicer.util.arrayFromVolume(node)
    array[:] = flipArr(array, mode)
    state = slicer.util.saveNode(node, outFile)
    slicer.mrmlScene.RemoveNode(node)
    return state

def deformWarp(cmtkPath, inImg, refImg, outImg, xform, scrPath, bashPath):
    """Warp an image using the transform from CMTK.
    
    Arguments:
        cmtkPath {str} -- path of the CMTK
        inImg {str} -- path of the input image
        refImg {str} -- path of the reference image
        outImg {str} -- path of the output image
        xform {str} -- path of the CMTK transform folder
        scrPath {str} -- path of the folder to generate the script
        bashPath {str} -- path of the bash shell
    """
    tmpl = 'export CMTK_WRITE_UNCOMPRESSED=1\n"{}" -o "{}" --floating "{}" "{}" "{}"'

    with open(scrPath, 'w') as f:
        content = tmpl.format(os.path.realpath(os.path.join(cmtkPath, 'reformatx')), 
                              os.path.realpath(outImg), 
                              os.path.realpath(inImg),
                              os.path.realpath(refImg), 
                              os.path.realpath(xform))
        f.write(content)

    cmd = '"%s" "%s"' % (os.path.realpath(bashPath), 
                         os.path.realpath(scrPath))
    runCmd(cmd)
    
    state = True if os.path.exists(outImg) else False

    return {outImg: state}
    