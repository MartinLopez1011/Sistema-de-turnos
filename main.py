import os
from controllers.main_controller import MainController
from views.gui import TurnosApp

def main():
    import sys
    if getattr(sys, 'frozen', False):
        root_path = os.path.dirname(sys.executable)
    else:
        root_path = os.path.dirname(os.path.abspath(__file__))
        
    controller = MainController(root_path)
    app = TurnosApp(controller)
    app.mainloop()

if __name__ == "__main__":
    main()
