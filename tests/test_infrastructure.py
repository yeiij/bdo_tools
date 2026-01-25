
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import psutil
from infrastructure.system import PsutilProcessService
from infrastructure.network import TcpNetworkService
from infrastructure.services_map import resolve_service_name, is_game_port
from domain.models import ProcessStatus

# --- Services Map Tests ---
class TestServicesMap(unittest.TestCase):
    def test_resolve_service_name(self):
        self.assertEqual(resolve_service_name(8888), "Game Server (XignCode)")
        self.assertEqual(resolve_service_name(443), "Web/Auth")
        self.assertTrue("Unknown" in resolve_service_name(99999))

    def test_is_game_port(self):
        self.assertTrue(is_game_port(8888))
        self.assertTrue(is_game_port(8889))
        self.assertFalse(is_game_port(443))
        self.assertFalse(is_game_port(80))

# --- System Service Tests ---
class TestPsutilProcessService(unittest.TestCase):
    def setUp(self):
        self.service = PsutilProcessService()

    @patch('psutil.process_iter')
    def test_get_pid_found(self, mock_iter):
        p = MagicMock()
        p.info = {'name': 'target.exe', 'pid': 123}
        mock_iter.return_value = [p]
        
        pid = self.service.get_pid('target.exe')
        self.assertEqual(pid, 123)

    @patch('psutil.process_iter')
    def test_get_pid_not_found(self, mock_iter):
        mock_iter.return_value = []
        pid = self.service.get_pid('target.exe')
        self.assertIsNone(pid)

    @patch('psutil.Process')
    def test_set_priority_success(self, mock_cls):
        mock_proc = MagicMock()
        mock_cls.return_value = mock_proc
        
        # Determine PID first (mocked internally or by helper)
        with patch.object(self.service, 'get_pid', return_value=123):
             with patch('platform.system', return_value="Windows"):
                 with patch('psutil.HIGH_PRIORITY_CLASS', 128, create=True):
                    result = self.service.set_priority('test.exe', "High")
                    self.assertTrue(result)
                    mock_proc.nice.assert_called_with(128)

    @patch('psutil.Process')
    def test_set_affinity_success(self, mock_cls):
        mock_proc = MagicMock()
        mock_cls.return_value = mock_proc
        
        with patch.object(self.service, 'get_pid', return_value=123):
            result = self.service.set_affinity('test.exe', [2, 3])
            self.assertTrue(result)
            mock_proc.cpu_affinity.assert_called_with([2, 3])

    def test_is_admin(self):
        # Mock ctypes only on Windows or if it exists
        import sys
        if sys.platform.startswith('win'):
             with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
                self.assertTrue(self.service.is_admin())
        else:
            # On Linux usually returns False or check implementation
            # Code uses ctypes.windll.shell32, which will fail on Linux if not guarded or mocked fully.
            # But the code is: try: return ctypes.windll... except: return False
            # So on Linux, it should return False because accessing ctypes.windll raises AttributeError
            self.assertFalse(self.service.is_admin())

    def test_is_admin_exception(self):
        # We can test exception handling.
        # But patching ctypes.windll on Linux fails because windll doesn't exist.
        import sys
        if sys.platform.startswith('win'):
            with patch('ctypes.windll.shell32.IsUserAnAdmin', side_effect=Exception("Error")):
                self.assertFalse(self.service.is_admin())
        else:
             # On non-Windows, accessing windll already raises AttributeError caught by code?
             # Actually code catches Exception.
             # We can verify it returns False
             self.assertFalse(self.service.is_admin())

    @patch('psutil.process_iter')
    def test_get_pid_access_denied(self, mock_iter):
        # Simulate accessing a process raises AccessDenied
        # We need an iterator that yields a real object, then one that raises AccessDenied on attr access?
        # psutil.process_iter yields Process objects. The code usually calls proc.info.
        
        # This is tricky because get_pid uses proc.info dict.
        # But if the loop raises exception it continues.
        # psutil.process_iter(['name']) handles errors internally usually, but we catch them manually inside loop.
        
        # Simulating behavior where accessing proc.info raises:
        p1 = MagicMock()
        type(p1).info = PropertyMock(side_effect=psutil.AccessDenied(0))
        mock_iter.return_value = [p1]
        
        pid = self.service.get_pid('target.exe')
        self.assertIsNone(pid)

    def test_get_status_no_pid(self):
        with patch.object(self.service, 'get_pid', return_value=None):
            self.assertEqual(self.service.get_status('foo'), ProcessStatus.NOT_RUNNING)

    @patch('psutil.Process')
    def test_get_status_zombie(self, mock_cls):
        p = MagicMock()
        p.is_running.return_value = True
        p.status.return_value = psutil.STATUS_ZOMBIE
        mock_cls.return_value = p
        
        with patch.object(self.service, 'get_pid', return_value=123):
             # Should fall through to NOT_RUNNING or similar if logic dictates, 
             # code says: if running and not zombie -> RUNNING
             # else -> NOT_RUNNING
             self.assertEqual(self.service.get_status('foo'), ProcessStatus.NOT_RUNNING)
    def test_get_status_running(self):
        with patch.object(self.service, 'get_pid', return_value=123):
             with patch('psutil.Process') as mock_cls:
                 p = MagicMock()
                 p.is_running.return_value = True
                 p.status.return_value = psutil.STATUS_RUNNING
                 mock_cls.return_value = p
                 self.assertEqual(self.service.get_status('foo'), ProcessStatus.RUNNING)

    def test_get_priority_no_pid(self):
        with patch.object(self.service, 'get_pid', return_value=None):
            self.assertEqual(self.service.get_priority('foo'), "Unknown")

    @patch('psutil.Process')
    def test_get_priority_error(self, mock_cls):
        mock_cls.side_effect = psutil.NoSuchProcess(123)
        with patch.object(self.service, 'get_pid', return_value=123):
            self.assertEqual(self.service.get_priority('foo'), "Unknown")

    @patch('psutil.Process')
    def test_get_priority_success_linux(self, mock_cls):
        # Test non-windows path
        with patch('platform.system', return_value="Linux"):
            p = MagicMock()
            p.nice.return_value = 0
            mock_cls.return_value = p
            with patch.object(self.service, 'get_pid', return_value=123):
                self.assertEqual(self.service.get_priority('foo'), "0")

    def test_get_affinity_no_pid(self):
        with patch.object(self.service, 'get_pid', return_value=None):
            self.assertEqual(self.service.get_affinity('foo'), [])

    @patch('psutil.Process')
    def test_get_priority_success_windows_mapping(self, mock_cls):
        with patch('platform.system', return_value="Windows"):
             p = MagicMock()
             mock_cls.return_value = p
             
             # Mock constants if checking on non-Windows env
             # Note: psutil module itself might not have these on Linux
             # But the tested code (infra/system.py) imports them from psutil.
             # We should mock them in the MODULE where they are used or ensure they exist.
             
             # Safest way: Just define dummy values for the test
             # We can patch psutil attributes directly in the test scope
             with patch('psutil.IDLE_PRIORITY_CLASS', 64, create=True), \
                  patch('psutil.BELOW_NORMAL_PRIORITY_CLASS', 16384, create=True), \
                  patch('psutil.NORMAL_PRIORITY_CLASS', 32, create=True), \
                  patch('psutil.ABOVE_NORMAL_PRIORITY_CLASS', 32768, create=True), \
                  patch('psutil.HIGH_PRIORITY_CLASS', 128, create=True), \
                  patch('psutil.REALTIME_PRIORITY_CLASS', 256, create=True):

                 # Test Mapping
                 mappings = [
                     (64, "Idle"),
                     (128, "High"),
                     (32, "Normal"),
                 ]
                 
                 with patch.object(self.service, 'get_pid', return_value=123):
                     for val, expected in mappings:
                         p.nice.return_value = val
                         self.assertEqual(self.service.get_priority('foo'), expected)

    @patch('psutil.Process')
    def test_get_affinity_success(self, mock_cls):
        mock_cls.return_value.cpu_affinity.return_value = [0, 1]
        with patch.object(self.service, 'get_pid', return_value=123):
            self.assertEqual(self.service.get_affinity('foo'), [0, 1])

    @patch('psutil.Process')
    def test_set_priority_normal_windows(self, mock_cls):
         with patch('platform.system', return_value="Windows"):
             p = MagicMock()
             mock_cls.return_value = p
             
             with patch('psutil.NORMAL_PRIORITY_CLASS', 32, create=True):
                 with patch.object(self.service, 'get_pid', return_value=123):
                     self.service.set_priority('foo', "Normal")
                     p.nice.assert_called_with(32)
    def test_set_priority_no_pid(self):
        with patch.object(self.service, 'get_pid', return_value=None):
            self.assertFalse(self.service.set_priority('foo', "High"))

    @patch('psutil.Process')
    def test_set_priority_error(self, mock_cls):
        mock_cls.side_effect = psutil.AccessDenied(123)
        with patch.object(self.service, 'get_pid', return_value=123):
            self.assertFalse(self.service.set_priority('foo', "High"))
            
    @patch('psutil.Process')
    def test_set_priority_invalid_input(self, mock_cls):
        mock_cls.return_value = MagicMock()
        with patch.object(self.service, 'get_pid', return_value=123):
            with patch('platform.system', return_value="Windows"):
                # "Invalid" is not in the mapping
                self.assertFalse(self.service.set_priority('foo', "Invalid"))

    def test_get_cpu_count_fallback(self):
        with patch('psutil.cpu_count', return_value=None):
            self.assertEqual(self.service.get_cpu_count(), 1)
            
    @patch('psutil.Process')
    def test_set_priority_linux(self, mock_cls):
         with patch('platform.system', return_value="Linux"):
            p = MagicMock()
            mock_cls.return_value = p
            with patch.object(self.service, 'get_pid', return_value=123):
                self.service.set_priority('foo', "High")
                p.nice.assert_called_with(-10) # High
                self.service.set_priority('foo', "Normal")
                p.nice.assert_called_with(0) # Normal

    def test_set_affinity_no_pid(self):
        with patch.object(self.service, 'get_pid', return_value=None):
             self.assertFalse(self.service.set_affinity('foo', []))

    @patch('psutil.Process')
    def test_get_status_method_exception(self, mock_cls):
        p = MagicMock()
        p.is_running.side_effect = psutil.NoSuchProcess(123)
        mock_cls.return_value = p
        
        with patch.object(self.service, 'get_pid', return_value=123):
             self.assertEqual(self.service.get_status('foo'), ProcessStatus.NOT_RUNNING)

    @patch('psutil.Process')
    def test_get_affinity_method_exception(self, mock_cls):
        p = MagicMock()
        p.cpu_affinity.side_effect = psutil.AccessDenied(123)
        mock_cls.return_value = p
        
        with patch.object(self.service, 'get_pid', return_value=123):
             self.assertEqual(self.service.get_affinity('foo'), [])

    @patch('psutil.Process')
    def test_set_affinity_error(self, mock_cls):
        mock_cls.side_effect = ValueError()
        with patch.object(self.service, 'get_pid', return_value=123):
            self.assertFalse(self.service.set_affinity('foo', [1]))

# --- Network Service Tests ---
class TestTcpNetworkService(unittest.TestCase):
    def setUp(self):
        self.service = TcpNetworkService()

    @patch('psutil.Process')
    def test_get_connections(self, mock_proc_cls):
        # Mock process instance
        mock_proc = MagicMock()
        mock_proc_cls.return_value = mock_proc
        
        # Mock connection object
        c1 = MagicMock()
        c1.status = psutil.CONN_ESTABLISHED
        c1.laddr = MagicMock()
        c1.laddr.__iter__.return_value = ('127.0.0.1', 5000)
        c1.raddr = MagicMock()
        c1.raddr.__iter__.return_value = ('8.8.8.8', 443)
        # Fix: raddr/laddr behave like named tuples which are iterable
        
        mock_proc.connections.return_value = [c1]
        
        conns = self.service.get_connections(pid=123)
        self.assertEqual(len(conns), 1)

    @patch('psutil.Process')
    def test_get_connections_exception(self, mock_proc_cls):
        mock_proc_cls.side_effect = psutil.NoSuchProcess(123)
        conns = self.service.get_connections(pid=123)
        self.assertEqual(conns, [])

    @patch('psutil.Process')
    @patch('socket.socket')
    def test_get_connections_with_ping_fail(self, mock_socket, mock_proc_cls):
        # Setup socket to fail
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = Exception("Ping fail")
        
        # Setup Process connections
        mock_proc = MagicMock()
        mock_proc_cls.return_value = mock_proc
        c1 = MagicMock()
        c1.status = psutil.CONN_ESTABLISHED
        c1.laddr = ('127.0.0.1', 5000)
        c1.raddr = ('8.8.8.8', 443)
        mock_proc.connections.return_value = [c1]
        
        conns = self.service.get_connections(pid=123)
        self.assertEqual(len(conns), 1)
        self.assertIsNone(conns[0].latency_ms)
    @patch('infrastructure.network.tcp_ping')
    def test_get_connections_with_ping_success(self, mock_ping):
        mock_ping.return_value = 45.5
        
        with patch('psutil.Process') as mock_proc_cls:
            c1 = MagicMock()
            c1.status = psutil.CONN_ESTABLISHED
            c1.laddr = ('127.0.0.1', 5000)
            c1.raddr = ('8.8.8.8', 443)
            mock_proc_cls.return_value.connections.return_value = [c1]
            
            conns = self.service.get_connections(pid=123)
            self.assertEqual(conns[0].latency_ms, 45.5)

    def test_tcp_ping_success(self):
        # We need to test the actual tcp_ping function logic
        from infrastructure.network import tcp_ping
        with patch('socket.socket') as mock_sock:
            mock_sock_inst = MagicMock()
            mock_sock.return_value = mock_sock_inst
            
            # Simulate time passing? No, just ensure it runs through
            # It's hard to mock time.perf_counter effectively in a tight loop without side_effect iterator
            # But the logic is: connect -> success
            
            latency = tcp_ping('1.1.1.1', 80)
            self.assertIsNotNone(latency)

    def test_tcp_ping_all_fail(self):
        from infrastructure.network import tcp_ping
        with patch('socket.socket') as mock_sock:
            mock_sock_inst = MagicMock()
            mock_sock.return_value = mock_sock_inst
            mock_sock_inst.connect.side_effect = Exception("Fail")
            
            latency = tcp_ping('1.1.1.1', 80)
            self.assertIsNone(latency)
