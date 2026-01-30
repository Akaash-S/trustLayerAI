"""
TrustLayer AI: File Extraction Pipeline
Modular file-parsing logic for PDF/Excel using PyMuPDF and Pandas
"""
import io
import logging
from typing import Union, BinaryIO
import fitz  # PyMuPDF
import pandas as pd

logger = logging.getLogger(__name__)

class FileExtractor:
    """
    High-speed file content extraction for PDF, Excel, and CSV files
    """
    
    def __init__(self):
        logger.info("File Extractor initialized")
    
    def extract_pdf(self, file_content: Union[bytes, BinaryIO]) -> str:
        """
        Extract text from PDF using PyMuPDF (fitz) for high-speed processing
        """
        try:
            if isinstance(file_content, bytes):
                pdf_stream = io.BytesIO(file_content)
            else:
                pdf_stream = file_content
            
            # Open PDF document
            doc = fitz.open(stream=pdf_stream.read(), filetype="pdf")
            
            extracted_text = ""
            
            # Extract text from each page
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                extracted_text += f"\n--- Page {page_num + 1} ---\n"
                extracted_text += page_text
                
                # Also extract text from images if any (OCR-like functionality)
                image_list = page.get_images()
                if image_list:
                    extracted_text += f"\n[Found {len(image_list)} images on page {page_num + 1}]\n"
            
            doc.close()
            
            logger.info(f"Extracted {len(extracted_text)} characters from PDF ({doc.page_count} pages)")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            return f"[PDF extraction failed: {str(e)}]"
    
    def extract_spreadsheet(self, file_content: Union[bytes, BinaryIO], filename: str) -> str:
        """
        Extract data from Excel/CSV files using Pandas
        """
        try:
            if isinstance(file_content, bytes):
                file_stream = io.BytesIO(file_content)
            else:
                file_stream = file_content
            
            extracted_text = ""
            
            if filename.endswith('.csv'):
                # Handle CSV files
                df = pd.read_csv(file_stream, encoding='utf-8', on_bad_lines='skip')
                extracted_text = self._dataframe_to_text(df, "CSV")
                
            elif filename.endswith(('.xlsx', '.xls')):
                # Handle Excel files
                excel_file = pd.ExcelFile(file_stream)
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    extracted_text += f"\n--- Sheet: {sheet_name} ---\n"
                    extracted_text += self._dataframe_to_text(df, f"Excel Sheet '{sheet_name}'")
            
            logger.info(f"Extracted {len(extracted_text)} characters from {filename}")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting spreadsheet content from {filename}: {e}")
            return f"[Spreadsheet extraction failed: {str(e)}]"
    
    def _dataframe_to_text(self, df: pd.DataFrame, source_type: str) -> str:
        """
        Convert pandas DataFrame to readable text format
        """
        try:
            text_content = f"\n{source_type} Data Summary:\n"
            text_content += f"Rows: {len(df)}, Columns: {len(df.columns)}\n\n"
            
            # Add column headers
            text_content += "Columns: " + ", ".join(df.columns.astype(str)) + "\n\n"
            
            # Add sample data (first 10 rows to avoid overwhelming the AI)
            sample_size = min(10, len(df))
            text_content += f"Sample Data (first {sample_size} rows):\n"
            
            for idx, row in df.head(sample_size).iterrows():
                text_content += f"Row {idx + 1}:\n"
                for col in df.columns:
                    value = str(row[col]) if pd.notna(row[col]) else "[Empty]"
                    text_content += f"  {col}: {value}\n"
                text_content += "\n"
            
            # Add data type information
            text_content += "Data Types:\n"
            for col, dtype in df.dtypes.items():
                text_content += f"  {col}: {dtype}\n"
            
            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                text_content += "\nNumeric Column Statistics:\n"
                stats = df[numeric_cols].describe()
                text_content += stats.to_string()
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error converting DataFrame to text: {e}")
            return f"[DataFrame conversion failed: {str(e)}]"
    
    def extract_text_file(self, file_content: Union[bytes, BinaryIO], encoding: str = 'utf-8') -> str:
        """
        Extract content from plain text files
        """
        try:
            if isinstance(file_content, bytes):
                return file_content.decode(encoding, errors='ignore')
            else:
                return file_content.read().decode(encoding, errors='ignore')
                
        except Exception as e:
            logger.error(f"Error extracting text file content: {e}")
            return f"[Text extraction failed: {str(e)}]"
    
    def get_file_info(self, file_content: Union[bytes, BinaryIO], filename: str) -> dict:
        """
        Get basic information about the uploaded file
        """
        try:
            if isinstance(file_content, bytes):
                size = len(file_content)
            else:
                # Get size by seeking to end
                current_pos = file_content.tell()
                file_content.seek(0, 2)  # Seek to end
                size = file_content.tell()
                file_content.seek(current_pos)  # Restore position
            
            file_extension = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
            
            return {
                'filename': filename,
                'size_bytes': size,
                'size_mb': round(size / (1024 * 1024), 2),
                'extension': file_extension,
                'supported': file_extension in ['pdf', 'xlsx', 'xls', 'csv', 'txt']
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {
                'filename': filename,
                'error': str(e)
            }