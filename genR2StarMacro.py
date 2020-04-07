# Dynamically creates the macro for generating the r2* maps
# Flexible to change some of the parameters, such as the echo time in the fitting
# Yu Sun
# 20191128
#

def genR2StarMacro(savepath, reverse=False, vflip=False, echoTypo=False):
    '''Generate the ImageJ macrop (.imj) file for calculating the r2* map.
    savepath: the path to save the macro;
    reverse: revere the order of slices;
    vflip: flip vertically;
    echoTypo: whether to include the echo time typo:
              3rd TE: 14.76 for mrhist011 - 039;
                      14.46 for mrhist042 - 070;
                      Not documented about mrhist040 and 041.
    '''

    # Step 1: T2SubstackMaker_10slices_12echos.txt
    
    cmd = '''run('Image Sequence...');
run("32-bit");

// T2SubstackMaker_10slices_12echos.txt

'''
    unit1 = '''selectWindow("R2STAR");
run("Make Substack...", "  slices=%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d");'''
    param1 = [1,11,21,31,41,51,61,71,81,91,101,111]
    for i in range(10):
        cmd += unit1 % tuple([j+i for j in param1])
        cmd += '\n'

    unit2 = '''selectWindow("Substack (%d,%d,%d,%d, ... %d)");
rename("%s");'''


    param2 = [1, 11, 21, 31, 111]
    for i in range(9):
        cmd += unit2 % tuple([j+i for j in param2] + ['Slice'+str(i+1)])
        cmd += '\n'

    cmd += '''selectWindow("Substack (10,20,30, ... 120)");
rename("Slice10");
'''

        
    # Step 2 T2STARMapGenerator_10Slices_12echoes_unequalspacing_no_background.txt
    
    cmd += '''
// T2STARMapGenerator_10Slices_12echoes_unequalspacing_no_background.txt
'''

    unit3 = '''selectWindow("%s");
run("MRI Processor ", "map=[T2 exponential] fit=Levenberg-Marquardt''' + \
''' cap=250 max=100 force input text1=[''' + '''%s '''*11 + '''%s] time=ms");
selectWindow("map LMA 1");
rename("%s");
selectWindow("map LMA 0");
rename("%s");'''
    echoTime = [4.92, 9.84, 14.76, 19.68, 24.6, 29.52, 34.44, 39.36,
                44.28, 54.12, 63.96, 73.8]

    for i in range(10):
        sliceNum = 'Slice'+str(i+1)
        cmd += unit3 % tuple([sliceNum] + echoTime +
                             [sliceNum+'_t2star'] + [sliceNum+'_a'])
        cmd += '\n'
        
    
    # Step 3 T2STAR_R2STAR_save.txt

    cmd += '''// T2STAR_R2STAR_save.txt
'''

    unit4 = '''selectWindow("%s");
close();'''
    for i in range(10):
        sliceNum = 'Slice'+str(i+1)+'_a'
        cmd += unit4 % (sliceNum,)
        cmd += '\n'

    cmd += '''
run("Images to Stack", "name=in_t2star title=t2star use");

saveAs("Tiff", File.directory+"in_t2star.tif");

run("Reciprocal", "stack");
run("Multiply...", "value=1000.000 stack");
'''

    # If the order is reversed
    if reverse:
        cmd += 'run("Reverse");\n'

    # If it's vertically flipped
    if vflip:
        cmd += 'run("Flip Vertically", "stack");'

    cmd += '''
path = getInfo("image.directory")+File.separator+"in_r2star.nii";
run("NIfTI-1", "save=path");


eval("script", "System.exit(0);");'''
    # Save the cmd
    with open(savepath, 'w') as f:
        f.write(cmd)
    
    return True


