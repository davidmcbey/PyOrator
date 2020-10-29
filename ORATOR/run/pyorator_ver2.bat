rem 
@set PYTHONPATH=E:\AbUniv\EnvModelModules
@set initial_working_dir=%cd%
@chdir /D E:\ORATOR\setup
E:\Python38\python.exe -W ignore E:\AbUniv\PyOratorVer2\PyOratorGUI.py
@chdir /D %initial_working_dir%
