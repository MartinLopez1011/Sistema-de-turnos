import unittest
from unittest.mock import MagicMock, patch

from views.components.dialogs import CustomConfirmDialog, CustomAlertDialog
from views.tabs.tab_plan import _confirm_action


class CustomDialogsTests(unittest.TestCase):
    """Pruebas unitarias para CustomConfirmDialog y CustomAlertDialog."""

    @patch("views.components.dialogs.ctk.CTkFont")
    @patch("views.components.dialogs.ctk.CTkButton")
    @patch("views.components.dialogs.ctk.CTkLabel")
    @patch("views.components.dialogs.ctk.CTkFrame")
    @patch("views.components.dialogs.ctk.CTkToplevel")
    def test_custom_confirm_dialog_layout_and_keys(self, mock_top, mock_frame, mock_label, mock_btn, mock_font):
        mock_parent = MagicMock()
        mock_parent.winfo_width.return_value = 800
        mock_parent.winfo_height.return_value = 600
        mock_parent.winfo_x.return_value = 100
        mock_parent.winfo_y.return_value = 100

        # Simular submit al esperar la ventana
        def side_effect_wait(dialog):
            # Obtener el comando del botón de confirmación
            calls = mock_btn.call_args_list
            confirm_btn_kwargs = calls[1][1]
            confirm_btn_kwargs["command"]()

        mock_parent.wait_window.side_effect = side_effect_wait

        res = CustomConfirmDialog.show(
            mock_parent,
            title="Eliminar excepción",
            prompt="¿Deseas eliminar la excepción seleccionada?",
            is_danger=True,
            confirm_text="Eliminar",
            cancel_text="Cancelar"
        )
        self.assertTrue(res)
        mock_top.assert_called_once_with(mock_parent)

    @patch("views.components.dialogs.ctk.CTkFont")
    @patch("views.components.dialogs.ctk.CTkButton")
    @patch("views.components.dialogs.ctk.CTkLabel")
    @patch("views.components.dialogs.ctk.CTkFrame")
    @patch("views.components.dialogs.ctk.CTkToplevel")
    def test_custom_alert_dialog_shows_error_warning_info(self, mock_top, mock_frame, mock_label, mock_btn, mock_font):
        mock_parent = MagicMock()
        mock_parent.winfo_width.return_value = 800
        mock_parent.winfo_height.return_value = 600
        mock_parent.winfo_x.return_value = 100
        mock_parent.winfo_y.return_value = 100

        def side_effect_wait(dialog):
            calls = mock_btn.call_args_list
            calls[-1][1]["command"]()

        mock_parent.wait_window.side_effect = side_effect_wait

        # Prueba con error
        CustomAlertDialog.show(
            mock_parent,
            title="Error de validación",
            message="• Debe seleccionar una persona válida.\n• Fecha requerida.",
            icon="error",
            button_text="Entendido"
        )
        self.assertTrue(mock_top.called)

    def test_confirm_action_delegates_to_custom_dialog_when_not_mocked(self):
        mock_parent = MagicMock()
        with patch("views.tabs.tab_plan.CustomConfirmDialog.show", return_value=True) as mock_custom:
            res = _confirm_action(mock_parent, "Título", "Mensaje de prueba")
            self.assertTrue(res)
            mock_custom.assert_called_once()


if __name__ == "__main__":
    unittest.main()
