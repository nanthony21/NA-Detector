#!/bin/bash

$PYTHON setup.py install --single-version-externally-managed --record=record.txt

MENU_DIR="$PREFIX/Menu"
if [ ! -d "$MENU_DIR" ]
then
  mkdir "$MENU_DIR"
fi

cp "$RECIPE_DIR/menu-windows.json" "$MENU_DIR/nadetector_shortcut.json"
