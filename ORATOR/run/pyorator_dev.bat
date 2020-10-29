rem 
@set PYTHONPATH=E:\AbUniv\GlblEcosseModules2;E:\AbUniv\PyOrator
@set initial_working_dir=%cd%
@chdir /D E:\ORATOR\setup
E:\Python38\python.exe -W ignore E:\AbUniv\PyOratorDev\PyOratorDevGUI.py
@chdir /D %initial_working_dir%
