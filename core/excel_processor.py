"""
Procesador de archivos Excel/CSV.
Maneja la lectura, limpieza y procesamiento de contactos.
"""

import json
import os
import pandas as pd
from pathlib import Path


class ExcelProcessor:
    """Procesador de archivos Excel/CSV con contactos."""
    
    def __init__(self):
        """Inicializa el procesador."""
        self.uploads_dir = "data/uploads"
        self.processed_dir = "data/processed"
        self.preferences_file = os.path.join(self.processed_dir, "preferences.json")
        
        # Crear directorios si no existen
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        if not os.path.exists(self.preferences_file):
            self.save_preferences()
    
    def get_uploaded_files(self):
        """Retorna lista de archivos Excel/CSV en el directorio de uploads."""
        files = []
        for file in os.listdir(self.uploads_dir):
            if file.endswith(('.xlsx', '.xls', '.csv')):
                files.append(file)
        return files
    
    def process_file(self, filename):
        """
        Procesa un archivo Excel/CSV.
        
        Args:
            filename: Nombre del archivo a procesar
            
        Returns:
            tuple: (success, message, processed_count)
        """
        filepath = os.path.join(self.uploads_dir, filename)
        
        if not os.path.exists(filepath):
            return False, "Archivo no encontrado", 0
        
        try:
            # Leer archivo
            if filename.lower().endswith('.csv'):
                # IMPORTANTE: usar separador ; y encoding latin1
                df = pd.read_csv(
                    filepath,
                    sep=';',
                    encoding='latin1'
                )
            else:
                # Para .xls / .xlsx dejamos el lector por defecto
                df = pd.read_excel(filepath)
            
            # Procesar datos
            df_processed = self._process_dataframe(df)
            
            # Guardar como JSON
            output_filename = f"{Path(filename).stem}_processed.json"
            output_path = os.path.join(self.processed_dir, output_filename)
            
            # Convertir a lista de diccionarios
            records = df_processed.to_dict('records')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            
            return True, f"Archivo procesado exitosamente: {len(records)} registros", len(records)
            
        except Exception as e:
            return False, f"Error al procesar archivo: {str(e)}", 0
    
    def _process_dataframe(self, df):
        """
        Procesa el DataFrame aplicando las reglas de negocio.
        
        Args:
            df: DataFrame de pandas
            
        Returns:
            DataFrame procesado
        """
        # Crear copia para no modificar original
        df = df.copy()

        # Expandir teléfonos separados por guión
        df = self._expand_phone_numbers(df)
        
        # Convertir columnas monetarias a número
        if '$ Hist.' in df.columns:
            df['$ Hist.'] = pd.to_numeric(
                df['$ Hist.']
                .astype(str)
                .str.replace('$', '', regex=False)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip(),
                errors='coerce'
            ).fillna(0)

        if '$ Asig.' in df.columns:
            df['$ Asig.'] = pd.to_numeric(
                df['$ Asig.']
                .astype(str)
                .str.replace('$', '', regex=False)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip(),
                errors='coerce'
            ).fillna(0)
            
            # Ordenar por $ Asig. descendente
            df = df.sort_values('$ Asig.', ascending=False)
        
        # Resetear índice
        df = df.reset_index(drop=True)
        
        return df

    def _expand_phone_numbers(self, df):
        """
        Expande filas cuando hay múltiples teléfonos separados por guión.
        
        Args:
            df: DataFrame de pandas
            
        Returns:
            DataFrame expandido
        """
        phone_columns = self._get_phone_columns(df.columns)

        if not phone_columns:
            return df

        expanded_rows = []

        for _, row in df.iterrows():
            found_numbers = False

            for phone_col in phone_columns:
                raw_value = row.get(phone_col, None)

                if pd.isna(raw_value):
                    continue

                phone_text = str(raw_value).strip()

                if not phone_text:
                    continue

                numbers = self._split_phone_values(phone_text)

                for phone_num in numbers:
                    new_row = row.copy()
                    new_row['Telefono_1'] = phone_num
                    new_row['Telefono_origen'] = phone_col
                    new_row['Telefono_seleccionado'] = phone_num
                    expanded_rows.append(new_row)
                    found_numbers = True

            if not found_numbers:
                expanded_rows.append(row)

        return pd.DataFrame(expanded_rows)

    def _split_phone_values(self, phone_text):
        """Divide un texto de teléfonos por '-', limpiando espacios y vacíos."""
        return [
            segment.strip()
            for segment in str(phone_text).split('-')
            if segment and segment.strip().lower() not in ("nan", "none")
        ]

    def _get_phone_columns(self, columns):
        """Retorna las columnas que coinciden con el patrón Telefono_1 a Telefono_9."""
        return [
            col for col in columns
            if isinstance(col, str) and col.startswith('Telefono_') and col.split('_')[-1].isdigit()
        ]

    def get_phone_fields_from_contacts(self, contacts):
        """Detecta los campos de teléfono disponibles en la lista de contactos."""
        if not contacts:
            return []

        columns = contacts[0].keys()
        return self._get_phone_columns(columns)

    def collect_numbers(self, contacts, allowed_phone_fields=None):
        """Extrae una lista de números únicos según los campos seleccionados."""
        if not contacts:
            return []

        allowed = set(allowed_phone_fields or [])

        numbers = {
            str(contact.get('Telefono_1', '')).strip()
            for contact in contacts
            if str(contact.get('Telefono_1', '')).strip()
            and (
                not allowed
                or contact.get('Telefono_origen', 'Telefono_1') in allowed
            )
        }

        return sorted(numbers)

    def save_preferences(self, selected_phone_fields=None, selected_variables=None, last_file=None):
        """Guarda las preferencias de campos telefónicos y variables disponibles."""
        data = {
            "selected_phone_fields": selected_phone_fields or [],
            "selected_variables": selected_variables or [],
            "last_file": last_file or None,
        }

        with open(self.preferences_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_preferences(self):
        """Carga las preferencias guardadas para campos y variables."""
        if not os.path.exists(self.preferences_file):
            return {
                "selected_phone_fields": [],
                "selected_variables": [],
                "last_file": None,
            }

        try:
            with open(self.preferences_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {
                "selected_phone_fields": [],
                "selected_variables": [],
                "last_file": None,
            }

    def update_preferences(self, new_values):
        """Actualiza parcialmente las preferencias guardadas."""
        prefs = self.load_preferences()
        prefs.update({k: v for k, v in new_values.items() if v is not None})
        with open(self.preferences_file, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
    
    def get_processed_files(self):
        """Retorna lista de archivos procesados."""
        files = []
        for file in os.listdir(self.processed_dir):
            if file.endswith('.json'):
                files.append(file)
        return files

    def get_latest_processed_file(self):
        """Retorna el archivo procesado más reciente según fecha de modificación."""
        processed_files = self.get_processed_files()

        if not processed_files:
            return None

        def file_mtime(filename):
            return os.path.getmtime(os.path.join(self.processed_dir, filename))

        return max(processed_files, key=file_mtime)
    
    def load_processed_file(self, filename):
        """Carga un archivo procesado."""
        filepath = os.path.join(self.processed_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar archivo procesado: {e}")
            return None
