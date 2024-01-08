::===============================================================================
:: Copyright 2014-2019 Intel Corporation.
::
:: This software and the related documents are Intel copyrighted  materials,  and
:: your use of  them is  governed by the  express license  under which  they were
:: provided to you (License).  Unless the License provides otherwise, you may not
:: use, modify, copy, publish, distribute,  disclose or transmit this software or
:: the related documents without Intel's prior written permission.
::
:: This software and the related documents  are provided as  is,  with no express
:: or implied  warranties,  other  than those  that are  expressly stated  in the
:: License.
::===============================================================================

@echo off
set "SCRIPTPATH=%~dp0"
set "SCRIPTPATH=%SCRIPTPATH:~0,-5%"

for /F %%i in ("%SCRIPTPATH%") do @set "VERSION=%%~ni"
for %%F in ("%SCRIPTPATH%") do set "PARENTDIR=%%~dpF"
IF %PARENTDIR:~-1%==\ SET PARENTDIR=%PARENTDIR:~0,-1%
for /F %%i in ("%PARENTDIR%") do @set "CURRENTENV=%%~ni"
set "MAINENV=intelpython"

if defined SETVARS_CALL (
    call "%SCRIPTPATH%\Scripts\activate"
) else (
    if "%VERSION%"=="latest" (
        set "OVERWRITE_CONDA_DEFAULT_ENV=%CURRENTENV%"
    ) else (
        set "OVERWRITE_CONDA_DEFAULT_ENV=%CURRENTENV%-%VERSION%"
    )
    call "%SCRIPTPATH%\Scripts\activate"
    set "OVERWRITE_CONDA_DEFAULT_ENV="
)

set "SCRIPTPATH="
set "VERSION="
set "PARENTDIR="
set "CURRENTENV="
set "MAINENV="

