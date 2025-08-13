#!/usr/bin/env python3
"""
简单的Excel文件分析器，不依赖pandas
"""
import os
import zipfile
import xml.etree.ElementTree as ET

def analyze_xlsx_structure(file_path):
    """分析XLSX文件结构（XLSX实际上是ZIP文件）"""
    
    print(f"📊 分析文件: {os.path.basename(file_path)}")
    print("=" * 50)
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # 列出所有文件
            files = zip_ref.namelist()
            print(f"包含的文件: {len(files)} 个")
            
            # 查看工作表信息
            if 'xl/sharedStrings.xml' in files:
                with zip_ref.open('xl/sharedStrings.xml') as f:
                    content = f.read().decode('utf-8')
                    print(f"字符串表大小: {len(content)} 字符")
                    
                    # 尝试解析一些字符串
                    try:
                        root = ET.fromstring(content)
                        strings = []
                        for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                            if si.text and len(strings) < 20:  # 只取前20个
                                strings.append(si.text)
                        
                        if strings:
                            print(f"前20个字符串示例:")
                            for i, s in enumerate(strings[:20]):
                                print(f"  {i+1}. {s}")
                    except:
                        print("无法解析字符串内容")
            
            # 查看工作表
            if 'xl/worksheets/sheet1.xml' in files:
                print(f"\n有工作表1")
                
        print(f"文件大小: {os.path.getsize(file_path)} 字节")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def main():
    """分析所有Excel文件"""
    
    excel_files = [
        "/mnt/e/LanguageLearning/german_vocabulary_A1_sample.xlsx",
        "/mnt/e/LanguageLearning/german_vocabulary_A2_sample.xlsx", 
        "/mnt/e/LanguageLearning/german_vocabulary_B1_sample.xlsx"
    ]
    
    print("🔍 Excel文件基本信息分析")
    print("=" * 60)
    
    for file_path in excel_files:
        if os.path.exists(file_path):
            analyze_xlsx_structure(file_path)
            print()
        else:
            print(f"⚠️ 文件不存在: {file_path}")

if __name__ == "__main__":
    main()