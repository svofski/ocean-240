@echo off
del/q testwork\*.* 2>nul
rmdir testwork 2>nul
mkdir testwork 2>nul

call :runtest test_p0
call :runtest test_p1
call :runtest test_p2
call :runtest test_p3
call :runtest test_p4
call :runtest test_p5
call :runtest test_p6

goto :eof

:runtest
setlocal

..\png2ok.py -base64 -stub inputs\%1.png testwork\%1.inc

rem fc /b testdata\%1.bas testwork\%1.bas >testwork\%1.diff
rem if ERRORLEVEL 1 (
rem	echo %1 ERROR
rem	exit /b %errorlevel%
rem )
rem if ERRORLEVEL 0 (
rem 	echo %1 PASS
rem )

endlocal

:eof