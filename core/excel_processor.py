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
        
        # Crear directorios si no existen
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
    
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
                .str.replace(',', '', regex=False)
                .str.strip(),
                errors='coerce'
            ).fillna(0)
        
        if '$ Asig.' in df.columns:
            df['$ Asig.'] = pd.to_numeric(
                df['$ Asig.']
                .astype(str)
                .str.replace('$', '', regex=False)
                .str.replace(',', '', regex=False)
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
        # Buscar columna Telefono_1
        if 'Telefono_1' not in df.columns:
            return df
        
        expanded_rows = []
        
        for _, row in df.iterrows():
            phone = str(row['Telefono_1'])
            
            # Si contiene guión, separar
            if '-' in phone:
                phones = [p.strip() for p in phone.split('-') if p.strip()]
                
                # Crear una fila por cada teléfono
                for phone_num in phones:
                    new_row = row.copy()
                    new_row['Telefono_1'] = phone_num
                    expanded_rows.append(new_row)
            else:
                expanded_rows.append(row)
        
        return pd.DataFrame(expanded_rows)
    
    def get_processed_files(self):
        """Retorna lista de archivos procesados."""
        files = []
        for file in os.listdir(self.processed_dir):
            if file.endswith('.json'):
                files.append(file)
        return files
    
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
