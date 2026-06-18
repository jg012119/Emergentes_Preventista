import zipfile
import xml.etree.ElementTree as ET
import os

def dump_xlsx(file_path, output_path):
    if not os.path.exists(file_path):
        print("File does not exist")
        return
        
    out = open(output_path, 'w', encoding='utf-8')
    
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        # Load shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in zip_ref.namelist():
            ss_content = zip_ref.read('xl/sharedStrings.xml')
            ss_root = ET.fromstring(ss_content)
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for si in ss_root.findall('.//ns:si', ns) or ss_root.findall('.//si'):
                t_elem = si.find('ns:t', ns) or si.find('t')
                if t_elem is not None:
                    shared_strings.append(t_elem.text)
                else:
                    # check for multi-format text (t inside r elements)
                    parts = []
                    for t_part in si.findall('.//ns:t', ns) or si.findall('.//t'):
                        if t_part.text:
                            parts.append(t_part.text)
                    shared_strings.append(''.join(parts) if parts else '')
        
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
        
        out.write(f"SHEETS: {[s[0] for s in sheets]}\n\n")
        
        # We can map sheet file paths from relationships, or search the zip for worksheets.
        # Inside the zip, sheet files are named by sheet index, but workbook.xml contains the sheet names.
        # Let's map them. Relationships are in xl/_rels/workbook.xml.rels
        rels = {}
        if 'xl/_rels/workbook.xml.rels' in zip_ref.namelist():
            rels_content = zip_ref.read('xl/_rels/workbook.xml.rels')
            rels_root = ET.fromstring(rels_content)
            r_ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
            for rel in rels_root.findall('.//r:Relationship', r_ns) or rels_root.findall('.//Relationship'):
                r_id = rel.attrib.get('Id')
                r_target = rel.attrib.get('Target')
                rels[r_id] = r_target
        
        for name, sheet_id, rid in sheets:
            target_path = rels.get(rid, f"worksheets/sheet{sheet_id}.xml")
            if target_path.startswith('worksheets/'):
                zip_path = f"xl/{target_path}"
            elif target_path.startswith('/xl/worksheets/'):
                zip_path = target_path[1:]
            else:
                zip_path = f"xl/worksheets/sheet{sheet_id}.xml"
                
            if zip_path not in zip_ref.namelist():
                # Let's search if sheet_id matches in some way
                possible_paths = [p for p in zip_ref.namelist() if f"sheet{sheet_id}.xml" in p or f"sheet{sheets.index((name, sheet_id, rid))+1}.xml" in p]
                if possible_paths:
                    zip_path = possible_paths[0]
                else:
                    out.write(f"WARNING: Could not find zip path for sheet {name} (rid={rid}, target_path={target_path})\n\n")
                    continue
            
            out.write(f"=========================================\n")
            out.write(f"SHEET: {name} (File: {zip_path})\n")
            out.write(f"=========================================\n")
            
            sheet_content = zip_ref.read(zip_path)
            sheet_root = ET.fromstring(sheet_content)
            
            rows = {}
            for row in sheet_root.findall('.//ns:row', ns) or sheet_root.findall('.//row'):
                row_idx = int(row.attrib.get('r', 1))
                row_cells = []
                for cell in row.findall('.//ns:c', ns) or cell.findall('.//c'):
                    r_attr = cell.attrib.get('r', '') # e.g. A1, B1
                    t_attr = cell.attrib.get('t', '') # e.g. s for shared string, str for inline string
                    val_elem = cell.find('ns:v', ns) or cell.find('v')
                    val = val_elem.text if val_elem is not None else ''
                    
                    if t_attr == 's' and val:
                        try:
                            val = shared_strings[int(val)]
                        except (IndexError, ValueError):
                            pass
                    
                    # Col letter from r_attr
                    col_letter = ''.join([c for c in r_attr if c.isalpha()])
                    row_cells.append((col_letter, val))
                # Sort cells by column letter (simple sort)
                row_cells.sort(key=lambda x: x[0])
                rows[row_idx] = row_cells
            
            for r in sorted(rows.keys()):
                # skip completely empty rows
                cells = rows[r]
                if not any(val for col, val in cells):
                    continue
                cells_str = " | ".join([f"{col}:{val}" for col, val in cells if val])
                out.write(f"Row {r:02d}: {cells_str}\n")
            out.write("\n\n")
            
    out.close()
    print("Done! Dumped to:", output_path)

if __name__ == '__main__':
    dump_xlsx(
        '/home/jairomgr/Proyectos/expo/Emergentes_Preventista/pruebas_usabilidad_estandarizadas (2).xlsx',
        '/home/jairomgr/Proyectos/expo/Emergentes_Preventista/backend/scratch/xlsx_dump.txt'
    )
