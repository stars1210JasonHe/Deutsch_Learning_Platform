#!/usr/bin/env python3
"""
修复数据库中不完整的词汇条目
主要问题：
1. 1781个词汇缺少中文翻译 (63.0%)
2. 1013个词汇缺少例句 (35.8%)

使用OpenAI API批量补充缺失信息
"""
import sqlite3
import asyncio
import json
import sys
import os
from datetime import datetime
import argparse

# 添加项目路径
sys.path.append(os.getcwd())

try:
    from app.services.openai_service import OpenAIService
    from app.core.config import settings
except ImportError as e:
    print(f"❌ 无法导入应用模块: {e}")
    sys.exit(1)

class DatabaseFixerService:
    """数据库修复服务"""
    
    def __init__(self, batch_size=20, delay=2.0):
        self.db_path = 'data/app.db'
        self.openai_service = OpenAIService()
        self.batch_size = batch_size
        self.delay = delay
        self.stats = {
            'words_processed': 0,
            'translations_added': 0,
            'examples_added': 0,
            'errors': 0,
            'skipped': 0,
            'start_time': datetime.now()
        }
        
        print(f"🔧 数据库修复服务初始化")
        print(f"   批次大小: {batch_size}")
        print(f"   延迟: {delay}秒")
        
    def get_incomplete_words(self, fix_type="missing_chinese", limit=50):
        """获取需要修复的词汇列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if fix_type == "missing_chinese":
                # 缺少中文翻译的词汇
                cursor.execute("""
                    SELECT wl.id, wl.lemma, wl.pos, wl.cefr
                    FROM word_lemmas wl
                    WHERE wl.id NOT IN (
                        SELECT DISTINCT lemma_id FROM translations 
                        WHERE lang_code = 'zh'
                    )
                    AND wl.id IN (
                        SELECT DISTINCT lemma_id FROM translations 
                        WHERE lang_code = 'en'
                    )
                    ORDER BY 
                        CASE WHEN wl.cefr IN ('A1', 'A2') THEN 1
                             WHEN wl.cefr IN ('B1', 'B2') THEN 2  
                             ELSE 3 END,
                        wl.frequency DESC NULLS LAST,
                        wl.lemma
                    LIMIT ?
                """, (limit,))
                
            elif fix_type == "missing_examples":
                # 缺少例句的词汇（有翻译但无例句）
                cursor.execute("""
                    SELECT wl.id, wl.lemma, wl.pos, wl.cefr
                    FROM word_lemmas wl
                    WHERE wl.id IN (
                        SELECT DISTINCT lemma_id FROM translations
                    )
                    AND wl.id NOT IN (
                        SELECT DISTINCT lemma_id FROM examples 
                        WHERE de_text IS NOT NULL AND de_text != ''
                    )
                    ORDER BY 
                        CASE WHEN wl.cefr IN ('A1', 'A2') THEN 1
                             WHEN wl.cefr IN ('B1', 'B2') THEN 2  
                             ELSE 3 END,
                        wl.frequency DESC NULLS LAST,
                        wl.lemma
                    LIMIT ?
                """, (limit,))
                
            elif fix_type == "high_priority":
                # 高优先级：A1/A2级别且缺少信息的词汇
                cursor.execute("""
                    SELECT wl.id, wl.lemma, wl.pos, wl.cefr
                    FROM word_lemmas wl
                    WHERE wl.cefr IN ('A1', 'A2')
                    AND (
                        wl.id NOT IN (SELECT DISTINCT lemma_id FROM translations WHERE lang_code = 'zh')
                        OR wl.id NOT IN (SELECT DISTINCT lemma_id FROM examples WHERE de_text IS NOT NULL AND de_text != '')
                    )
                    ORDER BY wl.lemma
                    LIMIT ?
                """, (limit,))
            
            results = cursor.fetchall()
            print(f"📋 找到 {len(results)} 个需要修复的词汇 (类型: {fix_type})")
            return results
            
        finally:
            conn.close()
    
    async def generate_chinese_translation(self, lemma, pos, existing_en_translation):
        """为词汇生成中文翻译"""
        try:
            prompt = f"""
请为德语单词 "{lemma}" ({pos}) 提供准确的中文翻译。

已有英文翻译: {existing_en_translation}

要求:
1. 提供2-3个最常用的中文翻译
2. 翻译应该准确、简洁
3. 考虑词性和语境
4. 避免过于复杂或生僻的译词

请严格按照以下JSON格式返回:
{{
    "translations_zh": ["中文翻译1", "中文翻译2", "中文翻译3"]
}}

只返回JSON，不要其他内容。
"""
            
            response = await self.openai_service._make_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.5
            )
            
            if response and response.get('choices'):
                content = response['choices'][0]['message']['content'].strip()
                data = json.loads(content)
                
                if data.get('translations_zh'):
                    return data['translations_zh']
            
            return None
            
        except Exception as e:
            print(f"   ❌ 生成中文翻译失败: {e}")
            return None
    
    async def generate_example_sentence(self, lemma, pos):
        """为词汇生成例句"""
        try:
            prompt = f"""
为德语单词 "{lemma}" ({pos}) 生成一个实用的例句。

要求:
1. 例句应该是日常生活中常用的场景
2. 语法正确，用词适当  
3. 提供德语、英语、中文三个版本
4. 德语例句长度适中(6-15个单词)
5. 确保例句中包含目标单词

请严格按照以下JSON格式返回:
{{
    "de": "德语例句",
    "en": "English example sentence", 
    "zh": "中文例句"
}}

只返回JSON，不要其他内容。
"""
            
            response = await self.openai_service._make_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            
            if response and response.get('choices'):
                content = response['choices'][0]['message']['content'].strip()
                data = json.loads(content)
                
                if all(key in data and data[key] for key in ['de', 'en', 'zh']):
                    return data
            
            return None
            
        except Exception as e:
            print(f"   ❌ 生成例句失败: {e}")
            return None
    
    def add_chinese_translations(self, lemma_id, translations):
        """添加中文翻译到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for translation in translations:
                cursor.execute("""
                    INSERT INTO translations (lemma_id, lang_code, text, source)
                    VALUES (?, ?, ?, ?)
                """, (lemma_id, "zh", translation.strip(), "openai_batch_fix"))
                
            conn.commit()
            self.stats['translations_added'] += len(translations)
            return True
            
        except Exception as e:
            print(f"   ❌ 保存中文翻译失败: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()
    
    def add_example_sentence(self, lemma_id, example_data):
        """添加例句到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO examples (lemma_id, de_text, en_text, zh_text)
                VALUES (?, ?, ?, ?)
            """, (lemma_id, example_data['de'], example_data['en'], example_data['zh']))
            
            conn.commit()
            self.stats['examples_added'] += 1
            return True
            
        except Exception as e:
            print(f"   ❌ 保存例句失败: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()
    
    def get_existing_english_translation(self, lemma_id):
        """获取现有的英文翻译"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT text FROM translations 
                WHERE lemma_id = ? AND lang_code = 'en'
                LIMIT 1
            """, (lemma_id,))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        finally:
            conn.close()
    
    async def fix_missing_chinese_translations(self, limit=50):
        """修复缺少中文翻译的词汇"""
        print("🔄 修复缺少中文翻译的词汇")
        print("=" * 50)
        
        words_to_fix = self.get_incomplete_words("missing_chinese", limit)
        
        if not words_to_fix:
            print("✅ 没有需要修复中文翻译的词汇")
            return
            
        print(f"📝 将处理 {len(words_to_fix)} 个词汇...")
        
        for i, (lemma_id, lemma, pos, cefr) in enumerate(words_to_fix, 1):
            print(f"[{i}/{len(words_to_fix)}] 处理: {lemma} ({pos})")
            self.stats['words_processed'] += 1
            
            try:
                # 获取现有英文翻译
                en_translation = self.get_existing_english_translation(lemma_id)
                if not en_translation:
                    print(f"   ⚠️  跳过：缺少英文翻译")
                    self.stats['skipped'] += 1
                    continue
                
                # 生成中文翻译
                zh_translations = await self.generate_chinese_translation(lemma, pos, en_translation)
                
                if zh_translations:
                    # 保存到数据库
                    if self.add_chinese_translations(lemma_id, zh_translations):
                        print(f"   ✅ 添加中文翻译: {zh_translations}")
                    else:
                        self.stats['errors'] += 1
                else:
                    print(f"   ❌ 未能生成中文翻译")
                    self.stats['errors'] += 1
                
                # 延迟避免API限制
                if i < len(words_to_fix):
                    await asyncio.sleep(self.delay)
                    
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                self.stats['errors'] += 1
                
            # 每10个词汇显示进度
            if i % 10 == 0:
                print(f"   📊 进度: {i}/{len(words_to_fix)} ({i/len(words_to_fix)*100:.1f}%)")
    
    async def fix_missing_examples(self, limit=30):
        """修复缺少例句的词汇"""
        print("🔄 修复缺少例句的词汇")
        print("=" * 50)
        
        words_to_fix = self.get_incomplete_words("missing_examples", limit)
        
        if not words_to_fix:
            print("✅ 没有需要修复例句的词汇")
            return
            
        print(f"📝 将处理 {len(words_to_fix)} 个词汇...")
        
        for i, (lemma_id, lemma, pos, cefr) in enumerate(words_to_fix, 1):
            print(f"[{i}/{len(words_to_fix)}] 处理: {lemma} ({pos})")
            self.stats['words_processed'] += 1
            
            try:
                # 生成例句
                example_data = await self.generate_example_sentence(lemma, pos)
                
                if example_data:
                    # 保存到数据库
                    if self.add_example_sentence(lemma_id, example_data):
                        print(f"   ✅ 添加例句: {example_data['de']}")
                    else:
                        self.stats['errors'] += 1
                else:
                    print(f"   ❌ 未能生成例句")
                    self.stats['errors'] += 1
                
                # 延迟避免API限制
                if i < len(words_to_fix):
                    await asyncio.sleep(self.delay)
                    
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                self.stats['errors'] += 1
                
            # 每5个词汇显示进度
            if i % 5 == 0:
                print(f"   📊 进度: {i}/{len(words_to_fix)} ({i/len(words_to_fix)*100:.1f}%)")
    
    async def fix_high_priority_words(self, limit=25):
        """修复高优先级词汇（A1/A2级别）"""
        print("🔄 修复高优先级词汇 (A1/A2)")
        print("=" * 50)
        
        words_to_fix = self.get_incomplete_words("high_priority", limit)
        
        if not words_to_fix:
            print("✅ 没有需要修复的高优先级词汇")
            return
            
        print(f"📝 将处理 {len(words_to_fix)} 个A1/A2级别词汇...")
        
        for i, (lemma_id, lemma, pos, cefr) in enumerate(words_to_fix, 1):
            print(f"[{i}/{len(words_to_fix)}] 处理: {lemma} ({pos}) [{cefr}]")
            self.stats['words_processed'] += 1
            
            try:
                # 检查需要什么类型的修复
                needs_chinese = self.needs_chinese_translation(lemma_id)
                needs_example = self.needs_example_sentence(lemma_id)
                
                # 修复中文翻译
                if needs_chinese:
                    en_translation = self.get_existing_english_translation(lemma_id)
                    if en_translation:
                        zh_translations = await self.generate_chinese_translation(lemma, pos, en_translation)
                        if zh_translations and self.add_chinese_translations(lemma_id, zh_translations):
                            print(f"   ✅ 添加中文翻译")
                
                # 修复例句
                if needs_example:
                    example_data = await self.generate_example_sentence(lemma, pos)
                    if example_data and self.add_example_sentence(lemma_id, example_data):
                        print(f"   ✅ 添加例句")
                
                # 延迟避免API限制
                if i < len(words_to_fix):
                    await asyncio.sleep(self.delay)
                    
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                self.stats['errors'] += 1
    
    def needs_chinese_translation(self, lemma_id):
        """检查是否需要中文翻译"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM translations 
                WHERE lemma_id = ? AND lang_code = 'zh'
            """, (lemma_id,))
            
            return cursor.fetchone()[0] == 0
            
        finally:
            conn.close()
    
    def needs_example_sentence(self, lemma_id):
        """检查是否需要例句"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM examples 
                WHERE lemma_id = ? AND de_text IS NOT NULL AND de_text != ''
            """, (lemma_id,))
            
            return cursor.fetchone()[0] == 0
            
        finally:
            conn.close()
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 数据库修复完成!")
        print("=" * 50)
        print(f"处理词汇: {self.stats['words_processed']}")
        print(f"添加翻译: {self.stats['translations_added']}")
        print(f"添加例句: {self.stats['examples_added']}")
        print(f"跳过: {self.stats['skipped']}")
        print(f"错误: {self.stats['errors']}")
        print(f"总用时: {elapsed}")
        
        success_rate = ((self.stats['translations_added'] + self.stats['examples_added']) / 
                       max(self.stats['words_processed'], 1) * 100)
        print(f"成功率: {success_rate:.1f}%")
        
        print(f"\n💡 建议:")
        print("1. 重新运行完整性检查确认修复效果")
        print("2. 测试前端搜索功能验证新增内容")
        print("3. 如需继续修复，可增加批次大小")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='修复数据库不完整词汇条目')
    parser.add_argument('--mode', 
                       choices=['chinese', 'examples', 'priority', 'all'], 
                       default='priority',
                       help='修复模式 (默认: priority)')
    parser.add_argument('--batch-size', type=int, default=30, 
                       help='批次大小 (默认: 30)')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='API调用延迟(秒) (默认: 2.0)')
    parser.add_argument('--limit', type=int, default=50,
                       help='处理词汇数量限制 (默认: 50)')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式，不实际修改数据库')
    
    args = parser.parse_args()
    
    print("🔧 数据库不完整条目修复工具")
    print("=" * 60)
    print(f"⚙️  配置:")
    print(f"   修复模式: {args.mode}")
    print(f"   批次大小: {args.batch_size}")
    print(f"   API延迟: {args.delay}秒")
    print(f"   处理限制: {args.limit}个词汇")
    print(f"   试运行: {'是' if args.dry_run else '否'}")
    
    if args.dry_run:
        print("\n⚠️  试运行模式：不会实际修改数据库")
        # 可以添加试运行逻辑
        return
    
    # 检查OpenAI配置
    if not settings.openai_api_key:
        print("\n❌ 错误: 未配置OpenAI API密钥")
        print("请设置环境变量 OPENAI_API_KEY")
        return
    
    print(f"\n✅ OpenAI配置检查通过")
    print(f"   模型: {settings.openai_model}")
    print(f"   API地址: {settings.openai_base_url}")
    
    fixer = DatabaseFixerService(
        batch_size=args.batch_size,
        delay=args.delay
    )
    
    print()
    
    try:
        if args.mode == 'chinese':
            await fixer.fix_missing_chinese_translations(args.limit)
        elif args.mode == 'examples':
            await fixer.fix_missing_examples(args.limit)
        elif args.mode == 'priority':
            await fixer.fix_high_priority_words(args.limit)
        elif args.mode == 'all':
            print("📋 执行完整修复流程...")
            await fixer.fix_high_priority_words(20)
            await fixer.fix_missing_chinese_translations(30)
            await fixer.fix_missing_examples(20)
        
        fixer.print_final_stats()
        
    except KeyboardInterrupt:
        print("\n⚠️  修复被用户中断")
        fixer.print_final_stats()
    except Exception as e:
        print(f"\n❌ 修复过程出现错误: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())