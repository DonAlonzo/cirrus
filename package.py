import sys, getpass, os, zipfile, shutil
from distutils.dir_util import copy_tree

def assemble(platform, tag):
    # Assemble package
    packagePath = "package"
    if os.path.exists(packagePath):
        shutil.rmtree(packagePath)
    os.mkdir(packagePath)
    
    ## Find binaries
    for (root, dirs, files) in os.walk("build"):
        for file in files:
            if platform == "vs2015" or platform == "vs2017":
                packagedFiles = [ "riks.dll", "riks.lib" ]
            else:
                packagedFiles = [ ".so", ".dylib" ]
            if any(packagedFile in file for packagedFile in packagedFiles):
                shutil.copyfile(os.path.join(root, file), os.path.join(packagePath, file))
    
    # Copy include directory
    copy_tree(os.path.join("build", "include"), os.path.join(packagePath, "include"))
    
    # Create archive
    fileName = "lib-{0}-{1}.zip".format(platform, tag)
    with zipfile.ZipFile(fileName, 'w') as zipf:
        for root, dirs, files in os.walk(packagePath):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), packagePath))
    
    shutil.rmtree(packagePath)

    return fileName
