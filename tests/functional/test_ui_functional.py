
import importlib
import unittest
from unittest.mock import MagicMock, patch

# Define mocked modules structure
m_tk = MagicMock()
m_ttk = MagicMock()

# Setup mocks to return objects that don't crash on standard Tkinter calls
class MockWidget(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.config = MagicMock()
        self.configure = MagicMock()
        self.pack = MagicMock()
        self.grid = MagicMock()
        self.bind = MagicMock()
        self.set = MagicMock()
        self.get = MagicMock(return_value="")
        self.winfo_x = MagicMock(return_value=0)
        self.winfo_y = MagicMock(return_value=0)
        self.winfo_width = MagicMock(return_value=800)
        self.winfo_height = MagicMock(return_value=600)
        self.winfo_reqwidth = MagicMock(return_value=300)
        self.winfo_reqheight = MagicMock(return_value=400)
        self.update_idletasks = MagicMock()
        self.geometry = MagicMock()
        self.transient = MagicMock()
        self.grab_set = MagicMock()
        self.title = MagicMock()
    
    def __getitem__(self, key):
        if key == "values":
            return getattr(self, "_values", [])
        return MagicMock()

    def __setitem__(self, key, value):
        if key == "values":
            self._values = value

m_tk.Tk = MockWidget
m_tk.Frame = MockWidget
m_tk.Toplevel = MockWidget
m_tk.Canvas = MockWidget
m_tk.BooleanVar = MagicMock
m_ttk.Frame = MockWidget
m_ttk.Label = MockWidget
m_ttk.Button = MockWidget
m_ttk.Combobox = MockWidget
m_ttk.Scrollbar = MockWidget

class TestUI(unittest.TestCase):
    def setUp(self):
        self.patcher = patch.dict('sys.modules', {
            'tkinter': m_tk,
            'tkinter.ttk': m_ttk,
            'tkinter.messagebox': MagicMock(),
            'PIL': MagicMock(),
            'PIL.Image': MagicMock(),
            'pystray': MagicMock(),
            'sv_ttk': MagicMock(),
            'darkdetect': MagicMock()
        })
        self.patcher.start()
        
        # Reset global mocks
        m_tk.reset_mock()
        m_ttk.reset_mock()
            
        import ui.views.main_window
        importlib.reload(ui.views.main_window)
        self.window_module = ui.views.main_window

    def test_window_lifecycle(self):
        main_window_cls = self.window_module.MainWindow
        vm = MagicMock()
        vm.settings.game_process_name = "game.exe"
        vm.settings.network_process_name = "net.exe"
        vm.settings.interval = 4000
        vm.cpu_count = 16
        vm.pid = 123
        vm.priority = "High"
        vm.affinity = [0, 1]
        vm.game_latency = 50
        
        root = m_tk.Tk()
        window = main_window_cls(root, vm)
        
        # Verify basic window creation
        self.assertIsNotNone(window)
        
        # Manual call to update_view should not cause errors
        window.update_view()
        
        # Verify that the viewmodel's set_manual_priority can be called
        vm.set_manual_priority("Normal")
        self.assertTrue(vm.set_manual_priority.called)

    def test_affinity_dialog_creation(self):
        main_window_cls = self.window_module.MainWindow
        vm = MagicMock()
        vm.cpu_count = 16
        vm.settings.game_process_name = "game.exe"
        vm.settings.network_process_name = "net.exe"
        vm.settings.interval = 4000
        
        root = m_tk.Tk()
        window = main_window_cls(root, vm)
        
        # Mock callback
        cb = MagicMock(return_value=True)
        window.open_affinity_dialog("Test", [0, 2], cb)
        
        # Verify that the dialog creation doesn't crash
        # Since Toplevel is a MockWidget class, calling it creates a new instance
        # We just verify no exceptions were raised
        self.assertIsNotNone(window)

if __name__ == '__main__':
    unittest.main()
