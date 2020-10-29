echo off
rem @ at the begining of a line tells the command processor to be less verbose
rem @set PYTHONPATH=E:\AbUniv\GlblEcosseModules2
@set initial_working_dir=%cd%
@chdir /D E:\ORATOR\setup
@E:\Python38\python.exe -W ignore E:\AbUniv\LiveStock\LivestockGUI.py
@chdir /D %initial_working_dir%

