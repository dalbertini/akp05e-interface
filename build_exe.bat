@echo off
rem ====================================================================
rem  akp05e-interface - Build de l'EXE "zero console" (PyInstaller)
rem  Double-clique ce fichier (a cote d'akp05e_app.py). Le resultat est
rem  copie ici : akp05e_interface.exe (lancement sans console).
rem  v2.21.0 : les logs sont ecrits dans akp05e_log.txt a cote de l'EXE.
rem ====================================================================
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Python introuvable. Installe Python 3.9+ en cochant "Add to PATH".
  pause & exit /b 1
)
python -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
  echo Installation de PyInstaller...
  python -m pip install --upgrade pyinstaller
  if errorlevel 1 ( echo [ERREUR] installation de PyInstaller echouee & pause & exit /b 1 )
)
echo Build en cours (1 a 3 minutes)...
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name akp05e_interface --collect-all pywinusb --collect-all comtypes --collect-all pycaw akp05e_app.py
if errorlevel 1 ( echo [ERREUR] build echoue & pause & exit /b 1 )
copy /y "dist\akp05e_interface.exe" . >nul
echo.
echo OK : akp05e_interface.exe a ete cree ici.
echo - place-le ou tu veux, avec akp05e_config.json a cote ;
echo - double-clic = lancement SANS console ;
echo - apres une session, les logs/diagnostics sont dans akp05e_log.txt a cote de l'EXE ;
echo - depuis un terminal, les options marchent toujours : --setup-lms, --identify, --install-autostart...
pause
