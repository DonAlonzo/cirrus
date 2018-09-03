import os, sys, platform as pf, getpass, shutil, package, publish
from subprocess import call

if sys.version_info >= (3, 0):
    from functools import reduce

includeFiles = [
    [["donalonzo", "hello_world.hpp"], ["donalonzo", "hello_world.hpp"]]
]

configurations = {
    "linux": {
        "x86":    "x86",
        "x86_64": "x64",
    },
    "osx": {
        "x86":    "x86",
        "x86_64": "x64"
    },
    "ios": {
    },
    "vs2015": {
        "X86":    "x86",
        "AMD64":  "x64"
    },
    "vs2017": {
        "X86":    "x86",
        "AMD64":  "x64"
    },
    "uwp": {
        "X86":    "x86",
        "AMD64":  "x64"
    }
}

cmakeGenerators = {
    "linux": {
        "x86": "Unix Makefiles",
        "x64": "Unix Makefiles"
    },
    "osx": {
        "x86": "Unix Makefiles",
        "x64": "Unix Makefiles"
    },
    "ios": {
        "os":        "Unix Makefiles",
        "simulator": "Unix Makefiles"
    },
    "vs2015": {
        "x86": "Visual Studio 14",
        "x64": "Visual Studio 14 Win64"
    },
    "vs2017": {
        "x86": "Visual Studio 15",
        "x64": "Visual Studio 15 Win64"
    },
    "uwp": {
        "x86": "Visual Studio 14",
        "x64": "Visual Studio 14 Win64"
    }
}

cmakeArguments = {
    "ios": {
        0: ["-DBUILD_TESTS=OFF"],
        "debug": {
            "simulator": { 0: ["-DIOS_PLATFORM=SIMULATOR64"] }
        },
        "release": {
            "simulator": { 0: ["-DIOS_PLATFORM=SIMULATOR64"] }
        }
    }
}

conanArguments = {
    "linux": {
        0: ["-s", "compiler=gcc"],
        1: ["-s", "compiler.libcxx=libstdc++11"],
        "debug": {
            "x86": { 0: ["-s", "arch=x86"] },
            "x64": { 0: ["-s", "arch=x86_64"] }
        },
        "release": {
            "x86": { 0: ["-s", "arch=x86"] },
            "x64": { 0: ["-s", "arch=x86_64"] }
        }
    },
    "vs2015": {
        0: ["-s", "compiler=Visual Studio"],
        "debug": {
            0: ["-s", "compiler.runtime=MDd"],
            "x86": { 0: ["-s", "arch=x86"] },
            "x64": { 0: ["-s", "arch=x86_64"] }
        },
        "release": {
            0: ["-s", "compiler.runtime=MD"],
            "x86": { 0: ["-s", "arch=x86"] },
            "x64": { 0: ["-s", "arch=x86_64"] }
        }
    },
    "vs2017": {
        0: ["-s", "compiler=Visual Studio"],
        "debug": {
            0: ["-s", "compiler.runtime=MDd"],
            "x86": { 0: ["-s", "arch=x86"] },
            "x64": { 0: ["-s", "arch=x86_64"] }
        },
        "release": {
            0: ["-s", "compiler.runtime=MD"],
            "x86": { 0: ["-s", "arch=x86"] },
            "x64": { 0: ["-s", "arch=x86_64"] }
        }
    }
}

def getTags(platform):
    return set(cmakeGenerators[platform].keys())

def defaultMode():
    return "debug"

def defaultTag():
    currentPlatform = defaultPlatform()
    if currentPlatform not in configurations:
        raise Exception("Current platform is not supported.")
    
    uname = pf.machine()
    if uname not in configurations[currentPlatform]:
        raise Exception("Current architecture is not supported.")
    
    return configurations[currentPlatform][uname]
    
def defaultPlatform():
    if pf.system() == "Darwin":  return "osx"
    if pf.system() == "Linux":   return "linux"
    else: raise Exception("Could not automatically determine platform.")

def validateMode(mode):
    if mode == "debug" or mode == "analyze":
        return "debug"
    elif mode == "release" or mode == "package" or mode.startswith("publish"):
        return "release"
    else:
        raise Exception("{0} is not a valid mode.".format(mode))

def validateTag(tag, platform):
    if platform not in configurations:
        raise Exception("{0} is not a valid platform.".format(platform))
    elif tag not in getTags(platform):
        raise Exception("{0} is not a valid tag.".format(tag))
    elif not supportedPlatform(platform):
        raise Exception("Can't build {0} on this system.")
    else:
        return tag

def supportedPlatform(platform):
    if os.path.isfile(os.path.join("toolchains", "{0}-{1}.toolchain.cmake".format(pf.system(), platform))): return True
    elif pf.system() == "Darwin": return platform == "osx"
    elif pf.system() == "Linux": return platform == "linux"
    elif pf.system() == "Windows": return platform == "vs2015" or platform == "vs2017"
    else: return False

def build(mode, tag, platform):
    # Validate arguments
    analyze = mode == "analyze"
    mode = validateMode(mode)
    tag = validateTag(tag, platform)

    # OK!
    print("Building {2}-{0} ({1})".format(mode, tag, platform))

    # Create build directory
    buildDirectory = "build"
    footprint = os.path.join(buildDirectory, ".{2}-{1}-{0}".format(mode, tag, platform))
    if os.path.exists(buildDirectory):
        # Build directory already exists
        if not os.path.exists(footprint):
            # Footprints are not the same. Delete the build directory.
            shutil.rmtree(buildDirectory)
            os.makedirs(buildDirectory)
    else:
        os.makedirs(buildDirectory)

    # Update/create footprint (For detecting if build configurations are the same)
    with open(footprint, 'a+'):
        os.utime(footprint, None)

    # Go into build directory
    cwd = os.getcwd()
    os.chdir(buildDirectory)

    # Debug if mode is "debug", release if mode is "release" or "publish"
    buildType = "Debug" if mode == "debug" else "Release"

    # Configuration specific argument extraction method
    def extract(args):
        extracted = list((k, v) for (k, v) in args if type(v) is not dict)
        extracted.sort()
        return list(arg[1] for arg in extracted)

    # Get configuration specific Conan arguments.
    conanArgs = []
    if platform in conanArguments:
        conanArgs.extend(extract(conanArguments[platform].items()))
        if mode in conanArguments[platform]: 
            conanArgs.extend(extract(conanArguments[platform][mode].items()))
            if tag in conanArguments[platform][mode]:
                conanArgs.extend(extract(conanArguments[platform][mode][tag].items()))

    # Get configuration specific CMake arguments.
    cmakeArgs = []
    if platform in cmakeArguments:
        cmakeArgs.extend(extract(cmakeArguments[platform].items()))
        if mode in cmakeArguments[platform]: 
            cmakeArgs.extend(extract(cmakeArguments[platform][mode].items()))
            if tag in cmakeArguments[platform][mode]:
                cmakeArgs.extend(extract(cmakeArguments[platform][mode][tag].items()))

    # Install dependencies
    conan = ["conan", "install", "..", "-s", "build_type={0}".format(buildType), "--build", "missing"]

    # Append platform specific Conan arguments
    for arg in conanArgs: conan.extend(arg)

    # If Conan profile exists for the current setup, use it
    if (os.path.isfile(os.path.join(os.path.dirname( __file__ ), "..", "toolchains", "{0}-{1}.profile.conan".format(pf.system(), platform)))):
        conan.extend(("--profile", "../toolchains/{0}-{1}.profile.conan".format(pf.system(), platform)))

    # Call Conan
    if call(conan) != 0:
        raise Exception("Could not install dependencies.")

    # Generate build files
    cmake = ["cmake", "..", "-G", cmakeGenerators[platform][tag], "-DCMAKE_BUILD_TYPE={0}".format(buildType.upper())]

    # Append platform specific CMake arguments
    for arg in cmakeArgs: cmake.extend(arg)

    # If CMake toolchain exists for the current setup, use it
    if (os.path.isfile(os.path.join(os.path.dirname( __file__ ), "..", "toolchains", "{0}-{1}.toolchain.cmake".format(pf.system(), platform)))):
        cmake.append("-DCMAKE_TOOLCHAIN_FILE=../toolchains/{0}-{1}.toolchain.cmake".format(pf.system(), platform))

    # Call CMake
    if call(cmake) != 0:
        raise Exception("Could not generate build files")

    # Build
    buildArgs = ["cmake", "--build", ".", "--config", buildType]
    if analyze: buildArgs.insert(0, "scan-build")
    if call(buildArgs) != 0:
        raise Exception("Could not build.")

    # Go back to original working directory
    os.chdir(cwd)

def clean():
    if os.path.exists("build"):
        shutil.rmtree("build")
    for file in [ file for file in os.listdir(".") if file.endswith(".pyc") or (file.startswith("lib") and file.endswith(".zip")) ]:
        os.remove(file)

def test():
    # Go into build directory
    cwd = os.getcwd()
    os.chdir("build")

    result = call(["ctest", "--verbose"])
    if result != 0:
        print("\x1b[6;30;41m" + "Tests failed!" + "\x1b[0m")
        sys.exit(result)
    else:
        print("\x1b[6;30;42m" + "All tests passed successfully." + "\x1b[0m")

    # Go back to original working directory
    os.chdir(cwd)

def assembleIncludeDirectory():
    for filePair in includeFiles:
        srcFile = os.path.join(reduce(os.path.join, ["src"] + filePair[0]))
        dstFile = os.path.join(reduce(os.path.join, ["build", "include"] + filePair[1]))
        dstDir = os.path.dirname(dstFile)
        if not os.path.isdir(dstDir):
            os.makedirs(dstDir)
        shutil.copyfile(srcFile, dstFile)

def main():
    if (len(sys.argv) > 1 and sys.argv[1] == "help"): usage()
    elif (len(sys.argv) > 1 and sys.argv[1] == "clean"): clean()
    else:
        mode     = sys.argv[1] if len(sys.argv) > 1 else defaultMode()
        tag      = sys.argv[2] if len(sys.argv) > 2 else defaultTag()
        platform = sys.argv[3] if len(sys.argv) > 3 else defaultPlatform()

        build(mode, tag, platform)
        test()
        assembleIncludeDirectory()
        print("Build complete.")

        if mode == "package":
            fileName = package.assemble(platform, tag)
            print("Package assembled as {0}.".format(fileName))
        elif mode.startswith("publish"):
            fileName = package.assemble(platform, tag)
            password = getpass.getpass() if ':' not in mode else mode.split(':', 1)[1]
            print("Publishing {0}...".format(fileName))
            url = publish.publish(platform, tag, fileName, password)
            os.remove(fileName)
            print("\nSuccessfully published {0}.\n{1}".format(fileName, url))

def usage():
    raise Exception("Usage: python build.py [clean/debug/release/package/publish(:password)] (<tag/architecture>) (<platform>)")

if __name__ == '__main__':
    try:    
        main()
    except Exception as e:
        print(str(e))
