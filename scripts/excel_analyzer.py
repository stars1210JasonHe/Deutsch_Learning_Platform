"""
Excel词汇文件分析器
分析Excel文件结构，为导入做准备
"""
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def analyze_excel_file(file_path):
    """分析Excel文件结构"""
    
    print(f"\n📊 分析文件: {file_path}")
    print("=" * 50)
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        print(f"总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")
        print(f"\n列名:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")
        
        print(f"\n前5行数据预览:")
        print(df.head().to_string())
        
        print(f"\n数据类型:")
        print(df.dtypes.to_string())
        
        print(f"\n缺失值统计:")
        missing = df.isnull().sum()
        for col, count in missing.items():
            if count > 0:
                print(f"  {col}: {count} 个缺失值")
        
        # 分析可能的词性分布
        if 'pos' in df.columns or 'part_of_speech' in df.columns or '词性' in df.columns:
            pos_col = None
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['pos', 'speech', '词性']):
                    pos_col = col
                    break
            
            if pos_col:
                print(f"\n词性分布:")
                pos_counts = df[pos_col].value_counts()
                print(pos_counts.to_string())
        
        # 检查可能的德语词汇列
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['german', 'deutsch', 'lemma', '德语', '词汇']):
                print(f"\n{col} 列示例:")
                sample_words = df[col].dropna().head(10).tolist()
                for word in sample_words:
                    print(f"  - {word}")
                break
        
        return df
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None

def main():
    """分析所有Excel文件"""
    
    excel_files = [
        "/mnt/e/LanguageLearning/german_vocabulary_A1_sample.xlsx",
        "/mnt/e/LanguageLearning/german_vocabulary_A2_sample.xlsx", 
        "/mnt/e/LanguageLearning/german_vocabulary_B1_sample.xlsx"
    ]
    
    print("🔍 Excel词汇文件分析器")
    print("=" * 50)
    
    all_dfs = {}
    
    for file_path in excel_files:
        if os.path.exists(file_path):
            df = analyze_excel_file(file_path)
            if df is not None:
                level = "A1" if "A1" in file_path else "A2" if "A2" in file_path else "B1"
                all_dfs[level] = df
        else:
            print(f"⚠️ 文件不存在: {file_path}")
    
    # 综合分析
    if all_dfs:
        print(f"\n📈 综合统计:")
        print("=" * 30)
        total_words = sum(len(df) for df in all_dfs.values())
        print(f"总词汇量: {total_words}")
        
        for level, df in all_dfs.items():
            print(f"{level}级别: {len(df)} 个词汇")
        
        # 分析列名的一致性
        print(f"\n📋 列名对比:")
        all_columns = set()
        for level, df in all_dfs.items():
            all_columns.update(df.columns)
            print(f"\n{level}级别列名: {list(df.columns)}")
        
        print(f"\n所有唯一列名: {sorted(all_columns)}")

if __name__ == "__main__":
    # 确保安装了pandas和openpyxl
    try:
        import pandas as pd
        import openpyxl
    except ImportError:
        print("❌ 请先安装依赖: pip install pandas openpyxl")
        sys.exit(1)
    
    main()