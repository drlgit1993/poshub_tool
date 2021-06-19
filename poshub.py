# _*_ coding:UTF-8 _*_

# !/usr/bin/python
# Python:   3.6.5
# Platform: Windows
# Author:   drl
# History:  2021-03-15 Ver:1.0 [drl] Initialization

import sys
from PyQt5.QtWidgets import QApplication
from drivers.tool_Main import  tool_main

if __name__ == '__main__':
    app = QApplication(sys.argv)
    Main_Window=tool_main()
    Main_Window.show()

    sys.exit(app.exec_())
