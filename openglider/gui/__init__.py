#!/bin/env python
import os
import signal
import sys

os.environ["FORCE_QT_API"] = "pyside6"
os.environ["QT_API"] = "pyside6"


def start_main_window() -> None:
    from openglider.gui.app import GliderApp

    app = GliderApp(sys.argv)

    #app.tracker = tracker


    if sys.gettrace() != None:
        app.debug = True


    #og_dir = os.path.dirname(os.path.dirname(openglider.__file__))
    #filename = os.path.join(og_dir, "tests/common/demokite.ods")
    
    #if os.path.isfile(filename):
    #    print("loading {}".format(filename))

        #loop = asyncio.get_event_loop()

        #loop.run_until_complete(app.main_window.load_glider(filename))
        #asyncio.create_task()
        
    app.run()



    # cleanup
    #for task in app.task_queue.tasks:
    #    task.stop()

    #os.killpg(0, signal.SIGKILL)
    sys.exit(0)


if __name__ == '__main__':
    start_main_window()