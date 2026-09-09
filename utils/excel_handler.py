import openpyxl
from openpyxl.styles import PatternFill, Alignment, Border, Side, Font
from datetime import timedelta

class ExcelHandler:
    def __init__(self, template_path, output_path):
        self.template_path = template_path
        self.output_path = output_path
        self.wb = None
        self.sheet = None

    def load_template(self):
        self.wb = openpyxl.load_workbook(self.template_path)
        self.sheet = self.wb.active
        

    def save_report(self):
        self.wb.save(self.output_path)

    def write_shifts(self, shifts, exceptions, year, month):
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        nombre_mes = meses[month - 1]
        
        # Estilos mejorados
        red_fill = PatternFill(start_color="FF3B30", end_color="FF3B30", fill_type="solid")
        da_fill = PatternFill(start_color="B45309", end_color="B45309", fill_type="solid")
        fl_fill = PatternFill(start_color="5B21B6", end_color="5B21B6", fill_type="solid")
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

        # Escribir el nombre del mes en la primera fila visible de los días
        if 1 in day_columns:
            # Ponemos el nombre del mes un poco arriba de los días
            first_day_col = day_columns[1]
            if days_row_index > 1:
                mes_cell = self.sheet.cell(row=days_row_index - 1, column=first_day_col)
                mes_cell.value = f"{nombre_mes} {year}"
                mes_cell.font = Font(bold=True, size=14)
                mes_cell.alignment = center_align

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
        import datetime
        
        for day_val, col_idx in day_columns.items():
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
                    cell.fill = da_fill if exc['tipo'] == 'DA' else fl_fill
                    cell.alignment = center_align
                    cell.font = bold_font
                    cell.border = thin_border
