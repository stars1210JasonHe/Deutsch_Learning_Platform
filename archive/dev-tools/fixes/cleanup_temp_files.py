#!/usr/bin/env python3
"""
清理临时调试脚本，只保留项目有用的文件
"""
import os

def cleanup_temp_files():
    """清理临时文件"""
    print("🧹 清理临时调试脚本...")
    
    # 需要删除的临时调试脚本
    temp_files_to_delete = [
        # 调试脚本
        "debug_aus_word.py",
        "debug_search.py", 
        "fix_aus_word.py",
        "fix_common_words.py",
        "fix_unknown_words.py",
        "validate_and_fix_data.py",
        "check_example_quality.py",
        "generate_missing_examples.py",
        
        # 测试脚本
        "test_api_search.py",
        "test_copy_env_api.py", 
        "test_database_search.py",
        "test_fixed_examples.py",
        "test_fixed_words.py",
        "test_frontend_search.py",
        "test_full_search.py",
        "test_search_debug.py",
        "test_search_direct.py",
        "test_search_fix.py",
        "verify_search_fix.py",
        
        # 简单测试
        "simple_db_test.py",
        "simple_test.py",
        "minimal_test_server.py",
        
        # 其他临时文件
        "fix_database_data.py",
        
        # 这个清理脚本本身也要删除
        "cleanup_temp_files.py"
    ]
    
    # 保留的有用脚本
    useful_scripts = [
        # 核心应用
        "app/",
        "frontend/",
        "tests/",
        "scripts/",
        "data/",
        
        # 配置文件
        "pyproject.toml",
        "uv.lock", 
        "README.md",
        "german-learning-platform.md",
        
        # 启动脚本
        "start.bat",
        "frontend/start-frontend.bat",
        
        # 词汇导入相关
        "import_excel_vocabulary.py",
        "import_vocabulary.bat",
        "preview_excel.py",
        "analyze_excel.py",
        
        # 数据库管理
        "inspect_database.py",
        "migrate_phase2.py",
        
        # 测试相关
        "run_tests.py",
        "run_tests.bat",
        "test_phase2.py",
        "test_phase2_api.py", 
        "test_phase2_backend.py",
        
        # 词汇数据
        "german_vocabulary_A1_sample.xlsx",
        "german_vocabulary_A2_sample.xlsx", 
        "german_vocabulary_B1_sample.xlsx",
        
        # 环境配置
        " - Copy.env",
        
        # 日志文件
        "uvicorn.out",
        "uvicorn.err"
    ]
    
    deleted_count = 0
    kept_count = 0
    
    print("\n🗑️ 删除临时文件:")
    for file_name in temp_files_to_delete:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"   ✅ 删除: {file_name}")
                deleted_count += 1
            except Exception as e:
                print(f"   ❌ 删除失败: {file_name} - {e}")
        else:
            print(f"   ⚠️ 文件不存在: {file_name}")
    
    print(f"\n📊 清理结果:")
    print(f"   删除文件: {deleted_count} 个")
    
    print(f"\n📁 保留的有用文件和目录:")
    for item in useful_scripts:
        if os.path.exists(item):
            if os.path.isdir(item):
                print(f"   📁 {item}")
            else:
                print(f"   📄 {item}")
            kept_count += 1
    
    print(f"\n✅ 项目清理完成!")
    print(f"   保留有用文件/目录: {kept_count} 个")
    print(f"   删除临时文件: {deleted_count} 个")
    
    print(f"\n💡 项目现在只包含:")
    print(f"   - 核心应用代码 (app/, frontend/)")
    print(f"   - 测试代码 (tests/)")
    print(f"   - 词汇管理脚本 (scripts/, import_*.py)")
    print(f"   - 配置和文档文件")
    print(f"   - 启动脚本 (start.bat)")

if __name__ == "__main__":
    cleanup_temp_files()

