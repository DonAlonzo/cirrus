@echo off
setlocal enableextensions enabledelayedexpansion

if defined VCInstallDir (
    if not ["%~2"]==[""] if ^
       not ["%~2"]==["arm"] if ^
       not ["%~2"]==["x86"] if ^
       not ["%~2"]==["x64"] (
        echo %~2 is not a valid architecture.
        goto :eof
    )

    rem Change compiler if applicable
    if not ["%~2"]==[""] if not ["%VSCMD_ARG_TGT_ARCH%"]==["%~2"] (
        set "CWD=%cd%"
        
        set VCVARSALL="%VCInstallDir%vcvarsall.bat"
        if not exist !VCVARSALL! set VCVARSALL="%VCInstallDir%Auxiliary\Build\vcvarsall.bat"
        if not exist !VCVARSALL! (
            echo Target architecture must be changed to continue but vcvarsall.bat can't be located.
            goto :eof
        )

        rem x86 amd64 x86_amd64 x86_arm x86_arm64 amd64_x86 amd64_arm amd64_arm64
        if ["%~2"]==["x86"] (
            call !VCVARSALL! x86
        ) else if ["%~2"]==["x64"] (
            call !VCVARSALL! x64
        ) else if ["%~2"]==["arm"] (
            call !VCVARSALL! x64_arm
        ) else (
            echo Can't compile for architecture %~2 on this (%VSCMD_ARG_TGT_ARCH%^) machine.
            goto :eof
        )
        
        if not errorlevel 0 goto :eof
        cd /d !CWD!
    )

    call python build.py %*
) else (
    echo You must run this script from a Visual Studio Command Prompt.
)

endlocal
