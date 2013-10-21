:: Goes through all .spec files in the directory and feeds them to PyInstaller,
:: or selects files given in first argument.
::
:: @author    Erki Suurjaak
:: @created   15.01.2013
:: @modified  15.06.2013
@echo off
set SOURCE_DIR=%CD%
set PYINSTALLERDIR=C:\Program Files\Python\Tools\pyinstaller
if not exist "%PYINSTALLERDIR%" set PYINSTALLERDIR=C:\Program Files (x86)\Python\Tools\pyinstaller
if not exist "%PYINSTALLERDIR%" echo PyInstaller not found. & goto :EOF
set WILDCARD=*.spec
if not "%1" == "" set WILDCARD=%1

for %%X IN (%WILDCARD%) do call :LOOPBODY %%X
goto :EOF

:LOOPBODY
:: Runs pyinstaller with %1 spec, copies exe, cleans up.
echo Making EXE for %1.
python "%PYINSTALLERDIR%\pyinstaller.py" "%1" >> "makeexe.log" 2>&1
if exist dist\*.exe (
    FOR %%E IN (dist\*.exe) DO (
        move %%E . > NUL
        echo Found %%~nE.exe for %1.
    )
    del makeexe.log logdict*.final.*.log
    if exist build rd /q /s build
    if exist dist rd /q /s dist
) else (
    echo No new EXE found for %1, check %SOURCE_DIR%\makeexe.log for errors.
)
echo.
goto :EOF
