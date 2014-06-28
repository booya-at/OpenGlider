from __future__ import print_function
#import os
from IPython.lib import guisupport
from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.qt.inprocess import QtInProcessKernelManager
import openglider


def ipy_widget():

    # Create an in-process kernel
    # >>> print_process_id()
    # will print the same process ID as the main process
    kernel_manager = QtInProcessKernelManager()
    kernel_manager.start_kernel()
    kernel = kernel_manager.kernel
    kernel.gui = 'qt4'
    kernel.shell.push({'openglider': openglider})

    kernel_client = kernel_manager.client()
    kernel_client.start_channels()

    def stop():
        kernel_client.stop_channels()
        kernel_manager.shutdown_kernel()

    print(12)
    #control = ConsoleWidget()
    print(23)
    control = RichIPythonWidget()
    print(24)
    control.kernel_manager = kernel_manager
    control.kernel_client = kernel_client
    #control.exit_requested.connect(stop)

    return control

if __name__ == '__main__':
    app = guisupport.get_app_qt4()
    c = ipy_widget()
    c.show()
    print(dir(c))
    app.exec_()