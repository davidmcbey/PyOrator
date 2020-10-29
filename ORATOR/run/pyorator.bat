echo off
rem @ at the begining of a line tells the command processor to be less verbose
@set PYTHONPATH=E:\AbUniv\GlblEcosseModules2
@set initial_working_dir=%cd%
@chdir /D E:\ORATOR\setup
@E:\Python38\python.exe -W ignore E:\AbUniv\PyOrator\PyOratorGUI.py
@chdir /D %initial_working_dir%

