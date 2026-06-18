import zipfile
import xml.etree.ElementTree as ET
import os

def parse_xlsx(file_path):
    print(f"Parsing {file_path}...")
    if not os.path.exists(file_path):
        print("File does not exist")
        return
        
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        # Load shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in zip_ref.namelist():
            ss_content = zip_ref.read('xl/sharedStrings.xml')
            ss_root = ET.fromstring(ss_content)
            # xl/sharedStrings.xml structure: <sst><si><t>string value</t></si></sst>
            # Use namespace handling or just strip it
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for si in ss_root.findall('.//ns:si', ns) or ss_root.findall('.//si'):
                t_elem = si.find('ns:t', ns) or si.find('t')
                if t_elem is not None:
                    shared_strings.append(t_elem.text)
                else:
                    shared_strings.append('')
        
        # Load sheets
        workbook_content = zip_ref.read('xl/workbook.xml')
        wb_root = ET.fromstring(workbook_content)
        sheets = []
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        for sheet in wb_root.findall('.//ns:sheet', ns) or wb_root.findall('.//sheet'):
            name = sheet.attrib.get('name')
            sheet_id = sheet.attrib.get('sheetId')
            rid = sheet.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            sheets.append((name, sheet_id, rid))
        
        print("Sheets found:", sheets)
        
        # Let's read worksheets. They are typically in xl/worksheets/sheet1.xml, etc.
        # We can map relationship ID or just read what's in xl/worksheets/
        for idx, (name, sheet_id, rid) in enumerate(sheets):
            sheet_file = f'xl/worksheets/sheet{idx+1}.xml'
            if sheet_file not in zip_ref.namelist():
                # fallback: check any worksheet XML file
                sheet_files = [f for f in zip_ref.namelist() if f.startswith('xl/worksheets/')]
                if sheet_files:
                    sheet_file = sheet_files[0]
                else:
                    continue
            
            print(f"\n--- Reading Sheet: {name} (File: {sheet_file}) ---")
            sheet_content = zip_ref.read(sheet_file)
            sheet_root = ET.fromstring(sheet_content)
            
            rows = {}
            for row in sheet_root.findall('.//ns:row', ns) or sheet_root.findall('.//row'):
                row_idx = int(row.attrib.get('r', 1))
                row_cells = []
                for cell in row.findall('.//ns:c', ns) or row.findall('.//c'):
                    r_attr = cell.attrib.get('r', '') # e.g. A1, B1
                    t_attr = cell.attrib.get('t', '') # e.g. s for shared string, str for inline string
                    val_elem = cell.find('ns:v', ns) or cell.find('v')
                    val = val_elem.text if val_elem is not None else ''
                    
                    if t_attr == 's' and val:
                        try:
                            val = shared_strings[int(val)]
                        except (IndexError, ValueError):
                            pass
                    row_cells.append((r_attr, val))
                rows[row_idx] = row_cells
            
            # Print first 30 rows
            for r in sorted(rows.keys())[:50]:
                cells_str = ", ".join([f"{r_attr}:{val}" for r_attr, val in rows[r]])
                print(f"Row {r}: {cells_str}")

if __name__ == '__main__':
    parse_xlsx('/home/jairomgr/Proyectos/expo/Emergentes_Preventista/pruebas_usabilidad_estandarizadas (2).xlsx')
