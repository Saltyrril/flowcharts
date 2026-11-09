#!/usr/bin/env python3
"""Запуск:  python flowchart.py            – веб-интерфейс
            python flowchart.py prog.c     – схемы в каталог ./flowcharts"""
import sys
from gostflow.cli import main

if __name__ == "__main__":
    sys.exit(main())
