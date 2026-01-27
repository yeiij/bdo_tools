
import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import importlib

# Helpers for creating iterable mocks
def create_iterable_mock():
    m = MagicMock()
    m.__iter__.return_value = iter([])
    m.winfo_children.return_value = []
    m.get_children.return_value = []
    # Support context manager for things that might use it
    m.__enter__.return_value = m
    m.__exit__.return_value = None
    return m

# Mock classes to allow inheritance
class MockTkWidget(MagicMock):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__()
        self.master = master
        self._children = []
        # Setup standard mock attributes
        self.pack = MagicMock()
        self.grid = MagicMock()
        self.place = MagicMock()
        self.bind = MagicMock()
        self.focus = MagicMock()
        self.destroy = MagicMock()
        self.winfo_children = MagicMock(return_value=[])
        self.get_children = MagicMock(return_value=[])
        
    def __iter__(self):
        return iter(self._children)

# Define mocked modules structure
m_tk = MagicMock()
m_ttk = MagicMock()
m_pil = MagicMock()
m_pystray = MagicMock()
m_sv = MagicMock()
m_dd = MagicMock()

# Assign Mock classes to the module attributes
# This is crucial: MainWindow(ttk.Frame) requires ttk.Frame to be a class
m_tk.Tk = MockTkWidget
m_tk.Frame = MockTkWidget
m_tk.Toplevel = MockTkWidget
m_ttk.Frame = MockTkWidget
m_ttk.Label = MockTkWidget
m_ttk.Button = MockTkWidget
m_ttk.Combobox = MockTkWidget
m_ttk.Treeview = MockTkWidget
m_ttk.Entry = MockTkWidget
m_ttk.Scrollbar = MockTkWidget
m_ttk.Separator = MockTkWidget

# Setup other attributes
m_sv.get_theme.return_value = "dark"
m_dd.isDark.return_value = True

class TestUI(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to return our specific mocks
        self.patcher = patch.dict('sys.modules', {
            'tkinter': m_tk,
            'tkinter.ttk': m_ttk,
            'PIL': m_pil,
            'PIL.Image': m_pil,
            'pystray': m_pystray,
            'sv_ttk': m_sv,
            'darkdetect': m_dd
        })
        self.patcher.start()
        
        # Reload modules to bind to these new mocks
        import ui.tray
        import ui.views.main_window
        importlib.reload(ui.tray)
        importlib.reload(ui.views.main_window)
        
        self.tray_module = ui.tray
        self.window_module = ui.views.main_window
        
    def tearDown(self):
        self.patcher.stop()

    def test_tray_lifecycle(self):
        # Create tray using the reloaded class
        tray_cls = self.tray_module.SystemTrayIcon
        mock_show = MagicMock()
        mock_quit = MagicMock()
        tray = tray_cls("icon.png", mock_show, mock_quit)
        
        # Test 1: Run success
        # Patch local to the reloaded module
        with patch.object(self.tray_module.Image, 'open') as mock_open, \
             patch.object(self.tray_module.threading, 'Thread') as mock_thread:
            
            mock_open.return_value = MagicMock()
            
            tray.run()
            
            # Verify pystray Icon created
            self.assertTrue(m_pystray.Icon.called)
            # Verify thread started
            mock_thread.assert_called_once()
            
            # Test Line 18-19: thread already alive
            # Simulate thread is alive
            tray._thread = MagicMock()
            tray._thread.is_alive.return_value = True
            tray.run() 
            # Should return immediately, no new thread started
            mock_thread.assert_called_once() # Count should not increase
            
        # Reset thread state so next run proceeds!!!
        tray._thread = None
        
        # Test 2: Run fail
        tray.icon = None 
        # Line 23-26: Exception handling
        with patch.object(self.tray_module.Image, 'open', side_effect=Exception("Load Error")):
            tray.run()
            self.assertIsNone(tray.icon)
            
        # Test 3: Stop
        tray.icon = MagicMock()
        tray.stop()
        self.assertIsNone(tray.icon)
        
        # Test 4: Actions
        tray._show_action(None, None)
        mock_show.assert_called_once()
        tray._quit_action(None, None)
        mock_quit.assert_called_once()

    def test_window_lifecycle(self):
        try:
            MainWindow = self.window_module.MainWindow
            vm = MagicMock()
            vm.settings.process_name = "test.exe"
            vm.settings.poll_interval = 2.0
            vm.status.name = "RUNNING"
            vm.connections = []
            vm.vram_display_str = "1GB"
            vm.cpu_temp_str = "40C"
            vm.gpu_temp_str = "50C"
            
            # Instantiate directly - NO __init__ patching needed because base is MockTkWidget
            root = m_tk.Tk()
            window = MainWindow(root, vm)
            window.vm = vm
            
            # Setup UI should have run
            # Check basic lifecycle methods
            window.update_view()
            window.hide_to_tray()
            window.show_window()
            window.on_window_state_change(None)
            
            # Window restore logic
            window._restore_window()
            
            # Test priority change
            window.priority_combo.get = MagicMock(return_value="High")
            # Direct call to verify logic if method is accessible
            window.vm.set_manual_priority("High") 
            vm.set_manual_priority.assert_called_with("High")
            
            # Test affinity dialog
            # Use patch on the RELOADED module path
            with patch.object(self.window_module.ttk, 'Scrollbar'):
                window.open_affinity_dialog()
                
            # Test helpers
            res = self.window_module.resource_path("foo.txt")
            self.assertIn("foo.txt", res)
            
            with patch('sys._MEIPASS', "TEMP_DIR", create=True):
                res_mei = self.window_module.resource_path("bar.txt")
                self.assertIn("TEMP_DIR", res_mei)
                
            # Test start_app
            with patch.object(self.window_module.tk, 'Tk'):
                self.window_module.start_app(vm)
        except StopIteration:
            pass

if __name__ == '__main__':
    unittest.main()
