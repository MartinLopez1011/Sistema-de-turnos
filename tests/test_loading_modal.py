import unittest
from unittest.mock import MagicMock, patch
import customtkinter as ctk

from views.components.dialogs import LoadingModal


class TestLoadingModal(unittest.TestCase):
    def test_loading_modal_creation_and_methods(self):
        # Mocking CTkToplevel and CTk components to allow testing in headless environments
        mock_parent = MagicMock()
        mock_parent.winfo_x.return_value = 100
        mock_parent.winfo_y.return_value = 100
        mock_parent.winfo_width.return_value = 800
        mock_parent.winfo_height.return_value = 600

        with patch("customtkinter.CTkToplevel") as mock_toplevel_cls, \
             patch("customtkinter.CTkLabel") as mock_label_cls, \
             patch("customtkinter.CTkFrame") as mock_frame_cls, \
             patch("customtkinter.CTkProgressBar") as mock_pb_cls, \
             patch("customtkinter.CTkFont") as mock_font_cls:
            
            mock_dialog = MagicMock()
            mock_dialog.winfo_exists.return_value = True
            mock_toplevel_cls.return_value = mock_dialog
            
            modal = LoadingModal(mock_parent, title="Test Modal", message="Test Msg", icon="⏳")
            
            self.assertEqual(modal.dialog, mock_dialog)
            mock_dialog.title.assert_called_with("Test Modal")
            mock_dialog.protocol.assert_called_with("WM_DELETE_WINDOW", unittest.mock.ANY)

            # Test update_status dispatches to parent.after
            modal.update_status(message="New Msg", title="New Title", icon="📧")
            mock_parent.after.assert_called()

            # Test close dispatches to parent.after
            modal.close()
            self.assertTrue(mock_parent.after.called)


if __name__ == "__main__":
    unittest.main()
