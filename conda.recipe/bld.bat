%PYTHON% setup.py install --single-version-externally-managed --record=record.txt

if errorlevel 1 exit 1

set MENU_DIR=%PREFIX%\Menu
IF NOT EXIST (%MENU_DIR%) mkdir %MENU_DIR%
copy %RECIPE_DIR%\menu-windows.json %MENU_DIR%\pwspy_shortcut.json
if errorlevel 1 exit 1
