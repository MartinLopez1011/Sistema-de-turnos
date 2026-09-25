import unittest
from unittest.mock import MagicMock, patch
from views.tabs.tab_settings import TabSettings


class TestTabSettingsSmtpLock(unittest.TestCase):
    def test_smtp_lock_and_toggle(self):
        # Create minimal mock structure for TabSettings without rendering real Tk widgets
        mock_parent = MagicMock()
        mock_app = MagicMock()
        mock_app.controller.get_starting_person.return_value = "PERSONA 1"
        mock_app.controller.get_personal_list.return_value = ["PERSONA 1"]
        mock_app.controller.get_all_persons.return_value = []
        mock_app.controller.get_notification_settings.return_value = {}

        with patch("customtkinter.CTkFrame"), \
             patch("customtkinter.CTkLabel"), \
             patch("customtkinter.CTkButton"), \
             patch("customtkinter.CTkEntry"), \
             patch("customtkinter.CTkOptionMenu"), \
             patch("customtkinter.CTkScrollableFrame"), \
             patch("customtkinter.CTkFont"), \
             patch("customtkinter.StringVar"), \
             patch("customtkinter.CTkTextbox"):
            
            tab = TabSettings(mock_parent, mock_app)

            # Check initial state: protected and disabled
            self.assertFalse(tab._smtp_editing)
            tab.smtp_host_entry.configure.assert_called_with(state="disabled")
            tab.smtp_port_entry.configure.assert_called_with(state="disabled")
            tab.smtp_user_entry.configure.assert_called_with(state="disabled")
            tab.smtp_pass_entry.configure.assert_called_with(state="disabled")

            # Toggle edit -> should enable fields and save button
            tab._toggle_edit_smtp()
            self.assertTrue(tab._smtp_editing)
            tab.smtp_host_entry.configure.assert_called_with(state="normal")
            tab.btn_save_smtp.configure.assert_called_with(state="normal")

            # Toggle cancel -> should restore and lock fields
            with patch("views.tabs.tab_settings.get_smtp_config", return_value={"host": "smtp.gmail.com", "port": 587, "user": "test@gmail.com", "password": "pwd"}):
                tab._toggle_edit_smtp()
                self.assertFalse(tab._smtp_editing)
                tab.smtp_host_entry.configure.assert_called_with(state="disabled")
                tab.btn_save_smtp.configure.assert_called_with(state="disabled")

    def test_advanced_settings_toggle(self):
        mock_parent = MagicMock()
        mock_app = MagicMock()
        mock_app.controller.get_starting_person.return_value = "PERSONA 1"
        mock_app.controller.get_personal_list.return_value = ["PERSONA 1"]
        mock_app.controller.get_all_persons.return_value = []
        mock_app.controller.get_notification_settings.return_value = {}

        with patch("customtkinter.CTkFrame"), \
             patch("customtkinter.CTkLabel"), \
             patch("customtkinter.CTkButton"), \
             patch("customtkinter.CTkEntry"), \
             patch("customtkinter.CTkOptionMenu"), \
             patch("customtkinter.CTkScrollableFrame"), \
             patch("customtkinter.CTkFont"), \
             patch("customtkinter.StringVar"), \
             patch("customtkinter.CTkTextbox"):
            
            tab = TabSettings(mock_parent, mock_app)

            # Check initial state: collapsed/hidden
            self.assertFalse(tab._advanced_expanded)
            self.assertIsNotNone(tab.advanced_container)
            self.assertIsNotNone(tab.btn_toggle_advanced)

            # Toggle expand
            tab._toggle_advanced()
            self.assertTrue(tab._advanced_expanded)
            tab.advanced_container.grid.assert_called_with(row=4, column=0, sticky="ew", pady=(10, 24))
            tab.btn_toggle_advanced.configure.assert_called()
            # Verify button text is 'Ocultar  ▲'
            configure_kwargs = tab.btn_toggle_advanced.configure.call_args[1]
            self.assertEqual(configure_kwargs.get("text"), "Ocultar  ▲")

            # Toggle collapse
            tab._toggle_advanced()
            self.assertFalse(tab._advanced_expanded)
            tab.advanced_container.grid_remove.assert_called()
            configure_kwargs = tab.btn_toggle_advanced.configure.call_args[1]
            self.assertEqual(configure_kwargs.get("text"), "Mostrar  ▼")


if __name__ == "__main__":
    unittest.main()

