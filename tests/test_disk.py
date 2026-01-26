
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from infrastructure.disk import DiskOptimizerService

class TestDiskOptimizerService(unittest.TestCase):
    def setUp(self):
        self.service = DiskOptimizerService()

    @patch('os.environ.get')
    @patch('pathlib.Path.is_dir')
    def test_find_bdo_documents_folder_success(self, mock_is_dir, mock_get):
        mock_get.return_value = "C:\\Users\\Test"
        mock_is_dir.side_effect = [False, True] # First fails, second (OneDrive) succeeds
        
        path = self.service.find_bdo_documents_folder()
        self.assertIsNotNone(path)
        self.assertIn("OneDrive", str(path))

    @patch('os.environ.get', return_value=None)
    def test_find_bdo_documents_folder_no_profile(self, mock_get):
        self.assertIsNone(self.service.find_bdo_documents_folder())

    @patch('os.environ.get', return_value="C:\\Users\\Test")
    @patch('pathlib.Path.is_dir', side_effect=Exception("Crash"))
    def test_find_bdo_documents_folder_exception(self, mock_is_dir, mock_get):
        self.assertIsNone(self.service.find_bdo_documents_folder())

    def test_clear_cache_not_found(self):
        with patch.object(self.service, 'find_bdo_documents_folder', return_value=None):
            success, msg = self.service.clear_cache()
            self.assertFalse(success)
            self.assertIn("Could not find", msg)

    @patch('pathlib.Path.exists', return_value=False)
    def test_clear_cache_already_clean(self, mock_exists):
        with patch.object(self.service, 'find_bdo_documents_folder', return_value=Path("/test")):
            success, msg = self.service.clear_cache()
            self.assertTrue(success)
            self.assertEqual(msg, "Cache already clean.")

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('shutil.rmtree')
    def test_clear_cache_success_dir(self, mock_rmtree, mock_is_dir, mock_exists):
        with patch.object(self.service, 'find_bdo_documents_folder', return_value=Path("/test")):
            success, msg = self.service.clear_cache()
            self.assertTrue(success)
            self.assertIn("Successfully cleared", msg)
            self.assertEqual(mock_rmtree.call_count, 3) # UserCache, Cache, xcache

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_dir', return_value=False)
    @patch('pathlib.Path.unlink')
    def test_clear_cache_success_file(self, mock_unlink, mock_is_dir, mock_exists):
        with patch.object(self.service, 'find_bdo_documents_folder', return_value=Path("/test")):
            success, msg = self.service.clear_cache()
            self.assertTrue(success)
            self.assertEqual(mock_unlink.call_count, 3)

    @patch('pathlib.Path.exists', return_value=True)
    @patch('shutil.rmtree', side_effect=Exception("Access Denied"))
    def test_clear_cache_errors(self, mock_rmtree, mock_exists):
        with patch.object(self.service, 'find_bdo_documents_folder', return_value=Path("/test")):
            success, msg = self.service.clear_cache()
            self.assertFalse(success)
            self.assertIn("Errors:", msg)
