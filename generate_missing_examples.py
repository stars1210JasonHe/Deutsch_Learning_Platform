#!/usr/bin/env python3
"""
为缺少例句的德语词汇生成例句
使用OpenAI API生成高质量的三语例句
"""
import sqlite3
import asyncio
import sys
import os
from datetime import datetime
import json

# 添加项目路径
sys.path.append(os.getcwd())

try:
    from app.services.openai_service import OpenAIService
    from app.config import settings
except ImportError as e:
    print(f"❌ 无法导入应用模块: {e}")
    print("请确保在项目根目录运行")
    sys.exit(1)

class ExampleGenerator:
    """例句生成器"""
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.openai_service = OpenAIService()
        self.stats = {
            'words_processed': 0,
            'examples_generated': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
    def get_words_without_examples(self, limit=50):
        """获取没有例句的词汇列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 优先处理常用词汇和用户关心的词汇
            priority_words = [
                'bezahlen', 'kreuzen', 'arbeiten', 'leben', 'kaufen', 'verkaufen',
                'schlafen', 'fahren', 'laufen', 'machen', 'sagen', 'wissen',
                'kommen', 'geben', 'nehmen', 'denken', 'finden', 'spielen',
                'lernen', 'verstehen', 'sprechen', 'hören', 'lesen', 'schreiben'
            ]
            
            # 先获取优先词汇中缺少例句的
            priority_placeholders = ','.join('?' * len(priority_words))
            cursor.execute(f"""
                SELECT wl.id, wl.lemma, wl.pos
                FROM word_lemmas wl
                LEFT JOIN examples e ON e.lemma_id = wl.id
                WHERE wl.lemma IN ({priority_placeholders})
                  AND e.id IS NULL
                ORDER BY wl.lemma
            """, priority_words)
            
            priority_results = cursor.fetchall()
            
            # 如果还需要更多词汇，获取其他缺少例句的词汇
            remaining_limit = limit - len(priority_results)
            if remaining_limit > 0:
                cursor.execute("""
                    SELECT wl.id, wl.lemma, wl.pos
                    FROM word_lemmas wl
                    LEFT JOIN examples e ON e.lemma_id = wl.id
                    WHERE e.id IS NULL
                      AND wl.lemma NOT IN ({})
                    ORDER BY wl.frequency DESC, wl.lemma
                    LIMIT ?
                """.format(priority_placeholders), priority_words + [remaining_limit])
                
                other_results = cursor.fetchall()
                results = priority_results + other_results
            else:
                results = priority_results[:limit]
            
            print(f"📋 找到 {len(results)} 个需要生成例句的词汇")
            print(f"   其中优先词汇: {len(priority_results)} 个")
            
            return results
            
        finally:
            conn.close()
    
    async def generate_example_for_word(self, lemma_id, lemma, pos):
        """为单个词汇生成例句"""
        print(f"🎯 生成例句: {lemma} ({pos})")
        
        try:
            # 构建提示词
            prompt = f"""
为德语单词 "{lemma}" ({pos}) 生成一个实用的例句。要求:

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

只返回JSON，不要其他内容。
"""
            
            # 调用OpenAI API
            response = await self.openai_service._make_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            
            if not response or 'choices' not in response or not response['choices']:
                raise Exception("OpenAI API返回空响应")
                
            content = response['choices'][0]['message']['content'].strip()
            
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
    
    async def generate_examples_batch(self, batch_size=10, delay=1.0):
        """批量生成例句"""
        print("🚀 开始批量生成例句")
        print("=" * 50)
        
        words_without_examples = self.get_words_without_examples(batch_size)
        
        if not words_without_examples:
            print("✅ 所有词汇都已有例句!")
            return
        
        print(f"📝 将处理 {len(words_without_examples)} 个词汇:")
        for lemma_id, lemma, pos in words_without_examples[:5]:
            print(f"   • {lemma} ({pos})")
        if len(words_without_examples) > 5:
            print(f"   ... 还有 {len(words_without_examples) - 5} 个")
        
        print()
        
        for i, (lemma_id, lemma, pos) in enumerate(words_without_examples, 1):
            print(f"[{i}/{len(words_without_examples)}] ", end="")
            self.stats['words_processed'] += 1
            
            try:
                # 生成例句
                example_data = await self.generate_example_for_word(lemma_id, lemma, pos)
                
                if example_data:
                    # 保存到数据库
                    self.save_example_to_database(lemma_id, example_data)
                
                # 延迟以避免API限制
                if delay > 0 and i < len(words_without_examples):
                    await asyncio.sleep(delay)
                    
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
        print(f"成功率: {(self.stats['examples_generated']/self.stats['words_processed']*100):.1f}%")
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
            else:
                print(f"\n⚠️  bezahlen仍然没有例句")
                
        finally:
            conn.close()

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='为德语词汇生成例句')
    parser.add_argument('--batch-size', type=int, default=20, help='批次大小 (默认: 20)')
    parser.add_argument('--delay', type=float, default=1.0, help='API调用延迟 (秒, 默认: 1.0)')
    parser.add_argument('--priority-only', action='store_true', help='只处理优先词汇')
    
    args = parser.parse_args()
    
    # 检查API密钥
    if not hasattr(settings, 'openai_api_key') or not settings.openai_api_key:
        print("❌ 错误: 未配置OpenAI API密钥")
        print("请设置环境变量 OPENAI_API_KEY")
        return
    
    generator = ExampleGenerator()
    await generator.generate_examples_batch(
        batch_size=args.batch_size,
        delay=args.delay
    )

if __name__ == "__main__":
    asyncio.run(main())