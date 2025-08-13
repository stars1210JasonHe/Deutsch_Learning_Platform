#!/usr/bin/env python3
"""
独立的Excel预览器 - 不依赖外部库
"""
import os
import zipfile
import xml.etree.ElementTree as ET


def parse_xlsx_file(file_path):
    """解析XLSX文件，提取词汇数据"""
    
    words_data = []
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # 读取共享字符串
            shared_strings = []
            if 'xl/sharedStrings.xml' in zip_ref.namelist():
                with zip_ref.open('xl/sharedStrings.xml') as f:
                    content = f.read().decode('utf-8')
                    root = ET.fromstring(content)
                    for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                        shared_strings.append(si.text if si.text else "")
            
            # 读取工作表数据
            if 'xl/worksheets/sheet1.xml' in zip_ref.namelist():
                with zip_ref.open('xl/worksheets/sheet1.xml') as f:
                    content = f.read().decode('utf-8')
                    root = ET.fromstring(content)
                    
                    # 解析所有行
                    rows = []
                    for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                        row_data = []
                        for cell in row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                            value = ""
                            v_element = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                            if v_element is not None:
                                # 检查是否是共享字符串引用
                                if cell.get('t') == 's':
                                    try:
                                        string_index = int(v_element.text)
                                        if string_index < len(shared_strings):
                                            value = shared_strings[string_index]
                                    except (ValueError, IndexError):
                                        value = v_element.text if v_element.text else ""
                                else:
                                    value = v_element.text if v_element.text else ""
                            row_data.append(value)
                        rows.append(row_data)
                    
                    return rows
                    
    except Exception as e:
        print(f"❌ 解析Excel文件失败: {e}")
        return []
    
    return rows


def map_columns(headers):
    """映射列标题到标准字段名"""
    
    column_mapping = {}
    
    for i, header in enumerate(headers):
        header_lower = header.lower().strip()
        
        # 德语词汇列
        if any(keyword in header_lower for keyword in ['german', 'deutsch', 'word', 'lemma', '词汇']):
            column_mapping['german_word'] = i
        
        # 冠词列
        elif any(keyword in header_lower for keyword in ['article', 'der/die/das', '冠词']):
            column_mapping['article'] = i
        
        # 翻译列
        elif any(keyword in header_lower for keyword in ['translation', 'english', 'meaning', '翻译', '意思']):
            column_mapping['translation'] = i
        
        # 例句列
        elif any(keyword in header_lower for keyword in ['example', 'sentence', '例句']):
            column_mapping['example'] = i
        
        # 词性/分类列
        elif any(keyword in header_lower for keyword in ['classification', 'pos', 'type', '词性', '分类']):
            column_mapping['classification'] = i
        
        # 只有名词列
        elif any(keyword in header_lower for keyword in ['noun only', 'noun', '名词']):
            column_mapping['noun_only'] = i
    
    return column_mapping


def preview_excel_file(file_path, limit=10):
    """预览Excel文件内容"""
    
    print(f"\n📊 预览文件: {os.path.basename(file_path)}")
    print("=" * 60)
    
    rows = parse_xlsx_file(file_path)
    
    if not rows:
        print("❌ 无法读取文件内容")
        return
    
    # 显示基本信息
    print(f"总行数: {len(rows)}")
    
    if len(rows) > 0:
        headers = rows[0]
        print(f"列数: {len(headers)}")
        print(f"列标题: {headers}")
        
        # 映射列
        column_mapping = map_columns(headers)
        print(f"识别的列映射: {column_mapping}")
        
        # 显示数据预览
        print(f"\n前{limit}行数据:")
        print("-" * 40)
        
        for i, row in enumerate(rows[1:limit+1]):
            print(f"\n第{i+1}行:")
            
            # 根据映射显示重要信息
            if 'german_word' in column_mapping:
                idx = column_mapping['german_word']
                if idx < len(row):
                    print(f"  德语词汇: {row[idx]}")
            
            if 'article' in column_mapping:
                idx = column_mapping['article']
                if idx < len(row):
                    print(f"  冠词: {row[idx]}")
            
            if 'translation' in column_mapping:
                idx = column_mapping['translation']
                if idx < len(row):
                    print(f"  翻译: {row[idx]}")
            
            if 'example' in column_mapping:
                idx = column_mapping['example']
                if idx < len(row):
                    print(f"  例句: {row[idx]}")
            
            if 'classification' in column_mapping:
                idx = column_mapping['classification']
                if idx < len(row):
                    print(f"  分类: {row[idx]}")
            
            # 显示所有列的原始数据
            print(f"  原始数据: {row}")


def main():
    """主函数"""
    
    excel_files = [
        "/mnt/e/LanguageLearning/german_vocabulary_A1_sample.xlsx",
        "/mnt/e/LanguageLearning/german_vocabulary_A2_sample.xlsx", 
        "/mnt/e/LanguageLearning/german_vocabulary_B1_sample.xlsx"
    ]
    
    print("🔍 Excel词汇文件预览器")
    print("=" * 60)
    
    for file_path in excel_files:
        if os.path.exists(file_path):
            preview_excel_file(file_path)
        else:
            print(f"⚠️ 文件不存在: {file_path}")


if __name__ == "__main__":
    main()