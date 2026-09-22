import openpyxl
from openpyxl.styles import PatternFill, Alignment, Border, Side, Font
from datetime import timedelta

class ExcelHandler:
    def __init__(self, output_path, personal):
        self.output_path = output_path
        self.personal = personal
        self.wb = None
        self.sheet = None

    def load_template(self):
        self.wb = openpyxl.Workbook()
        self.sheet = self.wb.active
        self.sheet.title = "Turnos"

        title_cell = self.sheet["A1"]
        title_cell.value = "PLANIFICACION DE TURNOS"
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        header_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        border = Border(
            left=Side(style="thin", color="808080"),
            right=Side(style="thin", color="808080"),
            top=Side(style="thin", color="808080"),
            bottom=Side(style="thin", color="808080"),
        )
        self.sheet["A2"] = "DIA"
        self.sheet["A3"] = "FUNCIONARIO"
        for row in (2, 3):
            self.sheet.cell(row=row, column=1).font = Font(bold=True)
            self.sheet.cell(row=row, column=1).fill = header_fill
            self.sheet.cell(row=row, column=1).alignment = Alignment(horizontal="center", vertical="center")
            self.sheet.cell(row=row, column=1).border = border

        for day in range(1, 32):
            cell = self.sheet.cell(row=2, column=day + 1, value=day)
            cell.font = Font(bold=True)
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        for row_idx, person in enumerate(self.personal, 4):
            name = person.get("nombre", "") if isinstance(person, dict) else str(person)
            cell = self.sheet.cell(row=row_idx, column=1, value=name)
            cell.border = border
            for column_idx in range(2, 33):
                self.sheet.cell(row=row_idx, column=column_idx).border = border

        self.sheet.column_dimensions["A"].width = 38
        for column_idx in range(2, 33):
            self.sheet.column_dimensions[openpyxl.utils.get_column_letter(column_idx)].width = 5
        self.sheet.freeze_panes = "B4"
        self.sheet.row_dimensions[1].height = 24
        

    def save_report(self):
        self.wb.save(self.output_path)

    def write_shifts(self, shifts, exceptions, year, month):
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        nombre_mes = meses[month - 1]
        
        # Estilos mejorados
        red_fill = PatternFill(start_color="FF3B30", end_color="FF3B30", fill_type="solid")
        da_fill = PatternFill(start_color="B45309", end_color="B45309", fill_type="solid")
        fl_fill = PatternFill(start_color="5B21B6", end_color="5B21B6", fill_type="solid")
        lic_fill = PatternFill(start_color="0E7490", end_color="0E7490", fill_type="solid")
        otr_fill = PatternFill(start_color="374151", end_color="374151", fill_type="solid")
        for_fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
        center_align = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin', color="000000"),
            right=Side(style='thin', color="000000"),
            top=Side(style='thin', color="000000"),
            bottom=Side(style='thin', color="000000")
        )
        bold_font = Font(bold=True)

        # Buscamos la fila de los días
        days_row_index = None
        for i, row in enumerate(self.sheet.iter_rows(values_only=True), 1):
            row_vals = [str(val).strip() if val is not None else "" for val in row]
            if any(val in ("1", "1.0", "01") for val in row_vals) and \
               any(val in ("2", "2.0", "02") for val in row_vals) and \
               any(val in ("3", "3.0", "03") for val in row_vals):
                days_row_index = i
                break
                
        if not days_row_index:
            raise Exception("No se encontró la fila con los días del mes (1, 2, 3...)")
            
        # Determinar en qué columna está cada día del mes
        day_columns = {}
        for col_idx, cell in enumerate(self.sheet[days_row_index], 1):
            val = cell.value
            if val is not None:
                try:
                    val_int = int(float(str(val).strip()))
                    if 1 <= val_int <= 31:
                        if val_int not in day_columns:
                            day_columns[val_int] = col_idx
                except ValueError:
                    pass

        # 0. Combinar y formatear título principal
        self.sheet.merge_cells("A1:AF1")
        title_cell = self.sheet["A1"]
        title_cell.value = f"PLANIFICACIÓN DE TURNOS — {nombre_mes} {year}"
        title_cell.font = Font(bold=True, size=13, color="1F2937")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        title_cell.fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        self.sheet.row_dimensions[1].height = 28

        # Encontrar en qué fila está cada persona.
        names_col_idx = min(day_columns.values()) - 1
        if names_col_idx < 1:
            names_col_idx = 1
            
        person_rows = {}
        for row_idx in range(days_row_index + 1, self.sheet.max_row + 1):
            name = self.sheet.cell(row=row_idx, column=names_col_idx).value
            if name:
                person_rows[str(name).strip()] = row_idx

        # 1. LIMPIAR LA GRILLA Y DIBUJAR FINES DE SEMANA DINAMICOS
        gray_fill = openpyxl.styles.PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        white_fill = openpyxl.styles.PatternFill(fill_type=None)
        invalid_day_fill = openpyxl.styles.PatternFill(start_color="595959", end_color="595959", fill_type="solid")
        import datetime
        import calendar
        
        _, days_in_month = calendar.monthrange(year, month)

        for day_val, col_idx in day_columns.items():
            if day_val > days_in_month:
                # Día no perteneciente al mes (ej: 29-31 en Feb, o 31 en Sep)
                header_cell = self.sheet.cell(row=days_row_index, column=col_idx)
                header_cell.fill = invalid_day_fill
                header_cell.value = "-"
                for row_idx in person_rows.values():
                    cell = self.sheet.cell(row=row_idx, column=col_idx)
                    cell.value = None
                    cell.fill = invalid_day_fill
                continue

            # Determinar si es fin de semana
            is_weekend = False
            try:
                date_obj = datetime.date(year, month, day_val)
                if date_obj.weekday() >= 5: # 5=Sat, 6=Sun
                    is_weekend = True
            except ValueError:
                pass
                
            fill_to_apply = gray_fill if is_weekend else white_fill
            
            # Pintar el encabezado
            header_cell = self.sheet.cell(row=days_row_index, column=col_idx)
            header_cell.fill = fill_to_apply
            header_cell.value = day_val
            
            # Pintar las filas del personal y vaciar texto
            for row_idx in person_rows.values():
                cell = self.sheet.cell(row=row_idx, column=col_idx)
                cell.value = None
                cell.fill = fill_to_apply

        # Escribir los turnos
        for shift in shifts:
            person = shift['persona']
            if not person or person not in person_rows:
                continue
            
            row_idx = person_rows[person]
            start_date, end_date = shift['semana']
            
            current_day = start_date
            while current_day <= end_date:
                if current_day.month == month and current_day.year == year:
                    day_val = current_day.day
                    if day_val in day_columns:
                        col_idx = day_columns[day_val]
                        cell = self.sheet.cell(row=row_idx, column=col_idx)
                        cell.fill = red_fill
                        cell.border = thin_border
                current_day += timedelta(days=1)

        # Escribir las excepciones (DA, FL)
        for exc in exceptions:
            person = exc['persona']
            exc_date = exc['fecha']
            
            if person in person_rows and exc_date.month == month and exc_date.year == year:
                row_idx = person_rows[person]
                day_val = exc_date.day
                if day_val in day_columns:
                    col_idx = day_columns[day_val]
                    cell = self.sheet.cell(row=row_idx, column=col_idx)
                    cell.value = exc['tipo']
                    _exc_fills = {'DA': da_fill, 'FL': fl_fill, 'LIC': lic_fill, 'OTR': otr_fill, 'FOR': for_fill}
                    cell.fill = _exc_fills.get(exc['tipo'], otr_fill)
                    cell.alignment = center_align
                    cell.font = bold_font
                    cell.border = thin_border

        # 4. DIBUJAR LEYENDA EXPLICATIVA DE COLORES
        max_person_row = max(person_rows.values()) if person_rows else (days_row_index + len(self.personal))
        legend_title_row = max_person_row + 3

        title_lbl = self.sheet.cell(row=legend_title_row, column=1, value="CONVENCIONES Y LEYENDA")
        title_lbl.font = Font(bold=True, size=10, color="1F2937")
        self.sheet.row_dimensions[legend_title_row].height = 22

        left_items = [
            ("Turno de Guardia", red_fill, "■", "FFFFFF"),
            ("DA: Día Administrativo", da_fill, "DA", "FFFFFF"),
            ("FL: Feriado Legal", fl_fill, "FL", "FFFFFF"),
            ("LIC: Licencia Médica", lic_fill, "LIC", "FFFFFF"),
        ]
        right_items = [
            ("OTR: Otro Permiso", otr_fill, "OTR", "FFFFFF"),
            ("FOR: Asignación Forzada", for_fill, "FOR", "FFFFFF"),
            ("Fin de Semana", gray_fill, " ", "000000"),
        ]

        for idx, (label, fill_style, mark, text_color) in enumerate(left_items):
            r = legend_title_row + 1 + idx
            self.sheet.row_dimensions[r].height = 20
            # Muestra de color
            chip = self.sheet.cell(row=r, column=2, value=mark)
            chip.fill = fill_style
            chip.alignment = center_align
            chip.font = Font(bold=True, size=9, color=text_color)
            chip.border = thin_border
            # Texto explicativo
            self.sheet.merge_cells(start_row=r, start_column=3, end_row=r, end_column=8)
            desc = self.sheet.cell(row=r, column=3, value=label)
            desc.font = Font(size=9.5, color="374151")
            desc.alignment = Alignment(horizontal="left", vertical="center")

        for idx, (label, fill_style, mark, text_color) in enumerate(right_items):
            r = legend_title_row + 1 + idx
            # Muestra de color
            chip = self.sheet.cell(row=r, column=10, value=mark)
            chip.fill = fill_style
            chip.alignment = center_align
            chip.font = Font(bold=True, size=9, color=text_color)
            chip.border = thin_border
            # Texto explicativo
            self.sheet.merge_cells(start_row=r, start_column=11, end_row=r, end_column=17)
            desc = self.sheet.cell(row=r, column=11, value=label)
            desc.font = Font(size=9.5, color="374151")
            desc.alignment = Alignment(horizontal="left", vertical="center")
