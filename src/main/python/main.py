import os
import sys
from radui import *
from fbs_runtime.application_context.PyQt5 import ApplicationContext


class AppContext(ApplicationContext):
    def run(self):
        window = RadUIForm(self)
        window.setWindowTitle("RadUI")
        window.resize(1920, 1080)
        window.show()
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            window.load_file(sys.argv[1])
        return self.app.exec_()


if __name__ == "__main__":
    matplotlib.rcParams["font.sans-serif"] = ["SimHei"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    appctxt = AppContext()
    exit_code = appctxt.run()
    sys.exit(exit_code)
