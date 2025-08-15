#!/usr/bin/env python3
"""
清理无效词条
1. 检测英语词条并删除
2. 检测复数形式的主词条，重新指向单数
3. 检测无效/错误词条
使用OpenAI来判断词条的有效性
"""
import sqlite3
import asyncio
import json
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.getcwd())

try:
    from app.services.openai_service import OpenAIService
    from app.core.config import settings
except ImportError as e:
    print(f"❌ 无法导入应用模块: {e}")
    sys.exit(1)

class WordCleaner:
    
    def __init__(self, batch_size=50, delay=1.5):
        self.db_path = 'data/app.db'
        self.openai_service = OpenAIService()
        self.batch_size = batch_size
        self.delay = delay
        self.stats = {
            'words_analyzed': 0,
            'english_words_deleted': 0,
            'plurals_redirected': 0,
            'invalid_words_deleted': 0,
            'corrections_made': 0,
            'start_time': datetime.now()
        }
    
    async def analyze_word_validity(self, words_batch):
        """使用OpenAI分析一批词条的有效性"""
        try:
            words_list = [{"id": w[0], "lemma": w[1], "pos": w[2]} for w in words_batch]
            
            prompt = f"""
分析以下德语词条的有效性。对每个词条，判断：
1. 是否是有效的德语词汇
2. 是否是英语词汇（应该删除）
3. 是否是复数形式（应该重定向到单数）
4. 正确的词性和基础形式

词条列表: {json.dumps(words_list, ensure_ascii=False)}

返回JSON格式:
{{
    "analyses": [
        {{
            "id": 词条ID,
            "lemma": "原词条",
            "status": "valid|english|plural|invalid|correct_lemma",
            "reason": "判断理由",
            "suggestion": {{
                "action": "keep|delete|redirect|correct",
                "target_lemma": "如果需要重定向，目标词条",
                "correct_pos": "正确的词性",
                "notes": "额外说明"
            }}
        }}
    ]
}}

判断标准：
- "english": 这是英语词汇，不是德语
- "plural": 这是德语复数形式，应重定向到单数
- "invalid": 不是有效词汇或严重错误
- "correct_lemma": 词条正确但词性可能需要修正
- "valid": 词条完全正确

只返回JSON，不要其他内容。
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "You are a German language expert. Analyze word validity precisely and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.3
            )
            
            if response and response.choices:
                content = response.choices[0].message.content.strip()
                data = json.loads(content)
                return data.get('analyses', [])
            
            return []
            
        except Exception as e:
            print(f"   ❌ OpenAI分析失败: {e}")
            return []
    
    def get_suspicious_words(self, limit=100):
        """获取可疑的词条"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找可能有问题的词条
            cursor.execute("""
                SELECT id, lemma, pos, cefr, frequency, notes
                FROM word_lemmas 
                WHERE 
                    -- 英语词汇模式
                    lemma REGEXP '^[a-zA-Z]+ing$'  -- -ing结尾
                    OR lemma REGEXP '^[a-zA-Z]+ed$'   -- -ed结尾
                    OR lemma REGEXP '^[a-zA-Z]+tion$' -- -tion结尾
                    OR lemma REGEXP '^[a-zA-Z]+ly$'   -- -ly结尾
                    -- 可能的复数形式
                    OR (pos = 'noun' AND lemma LIKE '%en' AND LENGTH(lemma) > 4)
                    OR (pos = 'noun' AND lemma LIKE '%er' AND LENGTH(lemma) > 4) 
                    OR (pos = 'noun' AND lemma LIKE '%e' AND LENGTH(lemma) > 3)
                    -- 可疑的词
                    OR lemma IN ('the', 'and', 'or', 'but', 'with', 'for', 'to', 'of', 'in', 'on', 'at')
                    -- 没有CEFR级别的可疑词
                    OR (cefr IS NULL AND frequency IS NULL AND LENGTH(lemma) < 3)
                ORDER BY 
                    CASE WHEN cefr IS NULL THEN 1 ELSE 0 END,
                    LENGTH(lemma),
                    lemma
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            print(f"📋 找到 {len(results)} 个可疑词条进行分析")
            return results
            
        except sqlite3.OperationalError:
            # SQLite可能不支持REGEXP，使用简化查询
            cursor.execute("""
                SELECT id, lemma, pos, cefr, frequency, notes
                FROM word_lemmas 
                WHERE 
                    lemma GLOB '*ing'
                    OR lemma GLOB '*ed'
                    OR lemma GLOB '*tion'
                    OR lemma GLOB '*ly'
                    OR lemma IN ('the', 'and', 'or', 'but', 'with', 'for', 'to', 'of', 'in', 'on', 'at')
                    OR (cefr IS NULL AND frequency IS NULL AND LENGTH(lemma) < 3)
                ORDER BY LENGTH(lemma), lemma
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            print(f"📋 找到 {len(results)} 个可疑词条进行分析")
            return results
            
        finally:
            conn.close()
    
    def get_random_words_for_check(self, limit=50):
        """随机获取一些词条进行质量检查"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, lemma, pos, cefr, frequency, notes
                FROM word_lemmas 
                WHERE pos IN ('noun', 'verb')
                ORDER BY RANDOM()
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            print(f"📋 随机选择 {len(results)} 个词条进行质量检查")
            return results
            
        finally:
            conn.close()
    
    async def process_word_batch(self, words_batch):
        """处理一批词条"""
        print(f"🔍 分析 {len(words_batch)} 个词条...")
        
        # 使用OpenAI分析
        analyses = await self.analyze_word_validity(words_batch)
        
        if not analyses:
            print("   ❌ 未能获取分析结果")
            return
        
        # 处理分析结果
        for analysis in analyses:
            await self.apply_word_fix(analysis)
            self.stats['words_analyzed'] += 1
    
    async def apply_word_fix(self, analysis):
        """应用词条修复"""
        word_id = analysis.get('id')
        lemma = analysis.get('lemma')
        status = analysis.get('status')
        suggestion = analysis.get('suggestion', {})
        action = suggestion.get('action', 'keep')
        reason = analysis.get('reason', '')
        
        print(f"   📝 {lemma} ({status}): {reason}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if action == 'delete':
                # 删除词条及相关数据
                self.delete_word_completely(cursor, word_id)
                if status == 'english':
                    self.stats['english_words_deleted'] += 1
                else:
                    self.stats['invalid_words_deleted'] += 1
                print(f"     ❌ 已删除")
                
            elif action == 'redirect':
                # 重定向到目标词条
                target_lemma = suggestion.get('target_lemma')
                if target_lemma:
                    success = self.redirect_to_target(cursor, word_id, lemma, target_lemma)
                    if success:
                        self.stats['plurals_redirected'] += 1
                        print(f"     ↗️  重定向到: {target_lemma}")
                    else:
                        print(f"     ❌ 重定向失败")
                
            elif action == 'correct':
                # 修正词条信息
                correct_pos = suggestion.get('correct_pos')
                notes = suggestion.get('notes', '')
                if correct_pos:
                    cursor.execute("""
                        UPDATE word_lemmas 
                        SET pos = ?, notes = COALESCE(notes || ' | ', '') || ?
                        WHERE id = ?
                    """, (correct_pos, f"corrected: {notes}", word_id))
                    self.stats['corrections_made'] += 1
                    print(f"     ✏️  修正词性: {correct_pos}")
            
            conn.commit()
            
        except Exception as e:
            print(f"     ❌ 处理失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def delete_word_completely(self, cursor, word_id):
        """完全删除词条及相关数据"""
        # 删除相关数据
        cursor.execute("DELETE FROM word_forms WHERE lemma_id = ?", (word_id,))
        cursor.execute("DELETE FROM translations WHERE lemma_id = ?", (word_id,))
        cursor.execute("DELETE FROM examples WHERE lemma_id = ?", (word_id,))
        
        # 删除主词条
        cursor.execute("DELETE FROM word_lemmas WHERE id = ?", (word_id,))
    
    def redirect_to_target(self, cursor, word_id, lemma, target_lemma):
        """将词条重定向到目标词条"""
        # 查找目标词条
        cursor.execute("SELECT id FROM word_lemmas WHERE lemma = ? AND pos = 'noun'", (target_lemma,))
        target = cursor.fetchone()
        
        if target:
            target_id = target[0]
            
            # 迁移数据到目标词条
            cursor.execute("""
                INSERT OR IGNORE INTO translations (lemma_id, lang_code, text, source)
                SELECT ?, lang_code, text, source 
                FROM translations WHERE lemma_id = ?
            """, (target_id, word_id))
            
            cursor.execute("""
                INSERT OR IGNORE INTO examples (lemma_id, de_text, en_text, zh_text, level)
                SELECT ?, de_text, en_text, zh_text, level
                FROM examples WHERE lemma_id = ?
            """, (target_id, word_id))
            
            # 将当前词条转为词形
            cursor.execute("""
                INSERT OR IGNORE INTO word_forms (lemma_id, form, feature_key, feature_value)
                VALUES (?, ?, ?, ?)
            """, (target_id, lemma, "plural", "plural_form"))
            
            # 更新目标词条的复数信息
            cursor.execute("""
                UPDATE word_lemmas 
                SET notes = CASE 
                    WHEN notes IS NULL THEN ? 
                    WHEN notes NOT LIKE '%plural:%' THEN notes || ' ' || ?
                    ELSE notes
                END
                WHERE id = ?
            """, (f"plural:{lemma}", f"plural:{lemma}", target_id))
            
            # 删除原词条
            self.delete_word_completely(cursor, word_id)
            return True
        else:
            # 目标词条不存在，先创建
            cursor.execute("""
                INSERT INTO word_lemmas (lemma, pos, cefr, notes)
                VALUES (?, 'noun', 'A1', ?)
            """, (target_lemma, f"plural:{lemma}"))
            
            new_target_id = cursor.lastrowid
            
            # 迁移数据
            cursor.execute("""
                UPDATE translations SET lemma_id = ? WHERE lemma_id = ?
            """, (new_target_id, word_id))
            
            cursor.execute("""
                UPDATE examples SET lemma_id = ? WHERE lemma_id = ?
            """, (new_target_id, word_id))
            
            cursor.execute("""
                UPDATE word_forms SET lemma_id = ? WHERE lemma_id = ?
            """, (new_target_id, word_id))
            
            # 删除原词条
            cursor.execute("DELETE FROM word_lemmas WHERE id = ?", (word_id,))
            
            return True
    
    async def run_cleaning(self, include_random_check=True):
        """运行清理流程"""
        print("🚀 词条清理工具")
        print("=" * 60)
        
        # 1. 分析可疑词条
        suspicious_words = self.get_suspicious_words(200)
        
        if suspicious_words:
            print(f"🔍 分析 {len(suspicious_words)} 个可疑词条...")
            
            # 分批处理
            for i in range(0, len(suspicious_words), self.batch_size):
                batch = suspicious_words[i:i + self.batch_size]
                await self.process_word_batch(batch)
                
                # 延迟避免API限制
                if i + self.batch_size < len(suspicious_words):
                    await asyncio.sleep(self.delay)
        
        # 2. 随机质量检查
        if include_random_check:
            print(f"\n🎲 随机质量检查...")
            random_words = self.get_random_words_for_check(30)
            
            if random_words:
                await self.process_word_batch(random_words)
        
        self.print_final_stats()
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 词条清理完成!")
        print("=" * 50)
        print(f"分析词条总数: {self.stats['words_analyzed']}")
        print(f"删除英语词条: {self.stats['english_words_deleted']}")
        print(f"重定向复数词条: {self.stats['plurals_redirected']}")
        print(f"删除无效词条: {self.stats['invalid_words_deleted']}")
        print(f"修正词条信息: {self.stats['corrections_made']}")
        print(f"总用时: {elapsed}")
        
        total_changes = (self.stats['english_words_deleted'] + 
                        self.stats['plurals_redirected'] + 
                        self.stats['invalid_words_deleted'] + 
                        self.stats['corrections_made'])
        
        print(f"总改进项目: {total_changes}")
        
        if total_changes > 0:
            print(f"\n✅ 清理成功! 数据库现在更加干净:")
            print("   • 英语词条已删除")
            print("   • 复数词条已重定向到单数") 
            print("   • 无效词条已清理")
            print("   • 词性错误已修正")

async def main():
    """主函数"""
    print("🧹 自动词条清理工具")
    print("=" * 60)
    print("功能:")
    print("1. 检测并删除英语词条")
    print("2. 将复数词条重定向到单数")
    print("3. 删除无效/错误词条")
    print("4. 修正词性错误")
    print()
    
    # 检查OpenAI配置
    if not settings.openai_api_key:
        print("❌ 错误: 未配置OpenAI API密钥")
        return
    
    print("✅ OpenAI配置正常")
    
    cleaner = WordCleaner(batch_size=30, delay=2.0)
    
    try:
        await cleaner.run_cleaning(include_random_check=True)
        
        print(f"\n💡 建议:")
        print("1. 测试前端搜索功能")
        print("2. 验证复数词条重定向")
        print("3. 检查删除的词条是否合理")
        
    except KeyboardInterrupt:
        print("\n⚠️  清理被用户中断")
        cleaner.print_final_stats()
    except Exception as e:
        print(f"\n❌ 清理失败: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())