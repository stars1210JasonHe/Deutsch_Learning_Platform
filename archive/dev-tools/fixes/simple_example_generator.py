#!/usr/bin/env python3
"""
简化的例句生成器
直接使用OpenAI API为缺少例句的词汇生成例句
"""
import sqlite3
import asyncio
import json
import os
from datetime import datetime

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    print("❌ 错误: 请安装openai包")
    print("运行: pip install openai")
    exit(1)

class SimpleExampleGenerator:
    def __init__(self):
        self.db_path = 'data/app.db'
        
        # 获取API密钥
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("❌ 错误: 请设置环境变量 OPENAI_API_KEY")
            exit(1)
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"  # 使用现有配置
        )
        
        self.stats = {
            'words_processed': 0,
            'examples_generated': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    async def generate_example_for_word(self, lemma, pos):
        """为单个词汇生成例句"""
        print(f"🎯 生成例句: {lemma} ({pos})")
        
        try:
            # 构建提示词
            prompt = f"""为德语单词 "{lemma}" ({pos}) 生成一个实用的例句。

要求:
1. 例句应该是日常生活中常用的场景
2. 语法正确，用词适当  
3. 提供德语、英语、中文三个版本
4. 德语例句长度适中(5-15个单词)
5. 如果是动词，使用常见的时态和人称
6. 如果是名词，使用适当的冠词

请严格按照以下JSON格式返回:
{{
    "de": "德语例句",
    "en": "English example sentence", 
    "zh": "中文例句"
}}

只返回JSON，不要其他内容。"""
            
            # 调用OpenAI API
            response = await self.client.chat.completions.create(
                model="meta-llama/llama-3.1-8b-instruct:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            
            if not response or not response.choices:
                raise Exception("API返回空响应")
                
            content = response.choices[0].message.content.strip()
            
            # 解析JSON响应
            try:
                example_data = json.loads(content)
                if not all(key in example_data for key in ['de', 'en', 'zh']):
                    raise ValueError("响应缺少必要字段")
                    
                # 验证例句质量
                if not example_data['de'] or lemma.lower() not in example_data['de'].lower():
                    print(f"   ⚠️  警告: 生成的例句可能不包含目标词汇")
                
                return example_data
                
            except json.JSONDecodeError:
                raise Exception(f"无法解析JSON响应: {content}")
                
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
            self.stats['errors'] += 1
            return None
    
    def save_example_to_database(self, lemma_id, example_data):
        """保存例句到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO examples (lemma_id, de_text, en_text, zh_text)
                VALUES (?, ?, ?, ?)
            """, (
                lemma_id,
                example_data['de'],
                example_data['en'], 
                example_data['zh']
            ))
            
            conn.commit()
            self.stats['examples_generated'] += 1
            print(f"   ✅ 保存成功")
            print(f"      DE: {example_data['de']}")
            print(f"      EN: {example_data['en']}")
            print(f"      ZH: {example_data['zh']}")
            
        except Exception as e:
            print(f"   ❌ 保存失败: {e}")
            conn.rollback()
            raise
            
        finally:
            conn.close()
    
    def get_priority_words_without_examples(self):
        """获取优先词汇中没有例句的"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 优先处理用户关心的词汇
            priority_words = [
                'bezahlen', 'kreuzen', 'arbeiten', 'leben', 'kaufen', 'verkaufen',
                'schlafen', 'fahren', 'laufen', 'machen', 'sagen', 'wissen',
                'kommen', 'geben', 'nehmen', 'denken', 'finden', 'spielen',
                'lernen', 'verstehen', 'sprechen', 'hören', 'lesen', 'schreiben',
                'essen', 'trinken', 'gehen', 'stehen', 'sitzen', 'liegen'
            ]
            
            # 获取这些词汇中缺少例句的
            placeholders = ','.join('?' * len(priority_words))
            cursor.execute(f"""
                SELECT wl.id, wl.lemma, wl.pos
                FROM word_lemmas wl
                LEFT JOIN examples e ON e.lemma_id = wl.id
                WHERE wl.lemma IN ({placeholders})
                  AND e.id IS NULL
                ORDER BY wl.lemma
            """, priority_words)
            
            results = cursor.fetchall()
            print(f"📋 找到 {len(results)} 个优先词汇需要生成例句")
            
            return results
            
        finally:
            conn.close()
    
    async def generate_examples_for_priority_words(self):
        """为优先词汇生成例句"""
        print("🚀 开始为优先词汇生成例句")
        print("=" * 50)
        
        words_without_examples = self.get_priority_words_without_examples()
        
        if not words_without_examples:
            print("✅ 所有优先词汇都已有例句!")
            return
        
        print(f"📝 将处理 {len(words_without_examples)} 个词汇:")
        for lemma_id, lemma, pos in words_without_examples:
            print(f"   • {lemma} ({pos})")
        print()
        
        for i, (lemma_id, lemma, pos) in enumerate(words_without_examples, 1):
            print(f"[{i}/{len(words_without_examples)}] ", end="")
            self.stats['words_processed'] += 1
            
            try:
                # 生成例句
                example_data = await self.generate_example_for_word(lemma, pos)
                
                if example_data:
                    # 保存到数据库
                    self.save_example_to_database(lemma_id, example_data)
                
                # 延迟以避免API限制
                if i < len(words_without_examples):
                    await asyncio.sleep(2.0)
                    
            except Exception as e:
                print(f"   ❌ 处理 {lemma} 时出错: {e}")
                self.stats['errors'] += 1
                continue
        
        self.print_final_stats()
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 例句生成完成!")
        print("=" * 50)
        print(f"处理词汇: {self.stats['words_processed']}")
        print(f"生成例句: {self.stats['examples_generated']}")
        print(f"错误数量: {self.stats['errors']}")
        success_rate = (self.stats['examples_generated']/self.stats['words_processed']*100) if self.stats['words_processed'] > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        print(f"总用时: {elapsed}")
        
        # 检查bezahlen是否已有例句
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT e.de_text FROM examples e
                JOIN word_lemmas wl ON wl.id = e.lemma_id  
                WHERE wl.lemma = 'bezahlen'
                LIMIT 1
            """)
            bezahlen_example = cursor.fetchone()
            
            if bezahlen_example:
                print(f"\n✅ bezahlen现在有例句: {bezahlen_example[0]}")
                print("🚀 刷新浏览器，搜索'bezahlen'应该能看到例句了!")
            else:
                print(f"\n⚠️  bezahlen仍然没有例句")
                
        finally:
            conn.close()

async def main():
    print("🧪 简化例句生成器")
    print("=" * 30)
    
    generator = SimpleExampleGenerator()
    await generator.generate_examples_for_priority_words()

if __name__ == "__main__":
    asyncio.run(main())