import zipfile
import xml.etree.ElementTree as ET
import os

def dump_xlsx_robust(file_path, output_path):
    if not os.path.exists(file_path):
        print("File does not exist:", file_path)
        return
        
    out = open(output_path, 'w', encoding='utf-8')
    
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        # Load shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in zip_ref.namelist():
            ss_content = zip_ref.read('xl/sharedStrings.xml')
            ss_root = ET.fromstring(ss_content)
            # Find all <t> in <si>
            # The namespace for sharedStrings is also openxmlformats
            ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            for si in ss_root.findall('.//x:si', ns) or ss_root.findall('.//si'):
                # a shared string can be in a single <t> or multiple <r><t>
                t_elems = si.findall('.//x:t', ns) or si.findall('.//t')
                val = "".join([t.text for t in t_elems if t.text is not None])
                shared_strings.append(val)
        
        print(f"Loaded {len(shared_strings)} shared strings.")
        
        # Load sheets
        workbook_content = zip_ref.read('xl/workbook.xml')
        wb_root = ET.fromstring(workbook_content)
        sheets = []
        ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        for sheet in wb_root.findall('.//x:sheet', ns) or wb_root.findall('.//sheet'):
            name = sheet.attrib.get('name')
            sheet_id = sheet.attrib.get('sheetId')
            rid = sheet.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            sheets.append((name, sheet_id, rid))
            
        print("Sheets in workbook:", [s[0] for s in sheets])
        
        for name, sheet_id, rid in sheets:
            # We know worksheets are named xl/worksheets/sheet{sheet_index}.xml
            # Let's find it in namelist
            idx = sheets.index((name, sheet_id, rid))
            zip_path = f"xl/worksheets/sheet{idx+1}.xml"
            if zip_path not in zip_ref.namelist():
                # fallback: find sheet file that matches
                candidates = [p for p in zip_ref.namelist() if f"sheet{sheet_id}.xml" in p or f"sheet{idx+1}.xml" in p]
                if candidates:
                    zip_path = candidates[0]
                else:
                    out.write(f"\nCould not find sheet file for {name}\n")
                    continue
            
            out.write(f"\n================================================================================\n")
            out.write(f"SHEET: {name} (Zip File: {zip_path})\n")
            out.write(f"================================================================================\n")
            
            sheet_content = zip_ref.read(zip_path)
            sheet_root = ET.fromstring(sheet_content)
            
            rows = {}
            for row in sheet_root.findall('.//x:row', ns) or sheet_root.findall('.//row'):
                row_idx = int(row.attrib.get('r', 1))
                row_cells = []
                for cell in row.findall('.//x:c', ns) or cell.findall('.//c'):
                    r_attr = cell.attrib.get('r', '') # e.g. A1, B1
                    t_attr = cell.attrib.get('t', '') # type: s, inlineStr, n, b, etc.
                    
                    val = ""
                    # 1. Check for inlineStr
                    if t_attr == 'inlineStr':
                        t_elems = cell.findall('.//x:t', ns) or cell.findall('.//t')
                        val = "".join([t.text for t in t_elems if t.text is not None])
                    else:
                        # 2. Check for value tag <v>
                        v_elem = cell.find('x:v', ns) or cell.find('v')
                        if v_elem is not None and v_elem.text is not None:
                            v_val = v_elem.text
                            if t_attr == 's': # shared string index
                                try:
                                    val = shared_strings[int(v_val)]
                                except (IndexError, ValueError):
                                    val = f"[SS_INDEX_ERROR:{v_val}]"
                            elif t_attr == 'b': # boolean
                                val = "TRUE" if v_val == '1' else "FALSE"
                            else:
                                val = v_val
                                
                    col_letter = ''.join([c for c in r_attr if c.isalpha()])
                    row_cells.append((col_letter, val))
                    
                row_cells.sort(key=lambda x: x[0])
                rows[row_idx] = row_cells
                
            for r in sorted(rows.keys()):
                cells = rows[r]
                # Filter out cells that have no value
                filtered_cells = [(col, val) for col, val in cells if val.strip()]
                if not filtered_cells:
                    continue
                cells_str = " | ".join([f"{col}: {val}" for col, val in filtered_cells])
                out.write(f"Row {r:03d}: {cells_str}\n")
                
    out.close()
    print("Done! Dumped to:", output_path)

if __name__ == '__main__':
    dump_xlsx_robust(
        '/home/jairomgr/Proyectos/expo/Emergentes_Preventista/pruebas_usabilidad_estandarizadas (2).xlsx',
        '/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend/scratch/xlsx_dump_robust.txt'
    )
