#!/usr/bin/env python3
"""
增强数据库修复器 - 修复所有语法信息
修复内容:
1. 缺少的中文翻译 (1781个词汇)
2. 缺少的例句 (1013个词汇)  
3. 缺少的名词冠词 (878个名词)
4. 缺少的名词复数 (2645个名词)
5. 缺少的动词变位表 (131个动词)
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

class EnhancedDatabaseFixer:
    """增强数据库修复器"""
    
    def __init__(self, batch_size=20, delay=2.5):
        self.db_path = 'data/app.db'
        self.openai_service = OpenAIService()
        self.batch_size = batch_size
        self.delay = delay
        self.stats = {
            'words_processed': 0,
            'chinese_translations_added': 0,
            'examples_added': 0,
            'articles_added': 0,
            'plurals_added': 0,
            'verb_conjugations_added': 0,
            'errors': 0,
            'skipped': 0,
            'start_time': datetime.now()
        }
        
    async def generate_complete_noun_info(self, lemma, existing_notes=None):
        """为名词生成完整信息（冠词、复数、中文翻译、例句）"""
        try:
            prompt = f"""
为德语名词 "{lemma}" 提供完整的语法信息和翻译。

请严格按照以下JSON格式返回:
{{
    "article": "der/die/das",
    "plural": "复数形式",
    "translations_zh": ["中文翻译1", "中文翻译2"],
    "example": {{
        "de": "德语例句 (使用该名词)",
        "en": "English example sentence",
        "zh": "中文例句"
    }}
}}

要求:
1. 冠词必须是 der/die/das 之一
2. 复数形式要准确（如果是不可数名词，返回原形）
3. 中文翻译简洁准确
4. 例句要自然实用，长度适中

只返回JSON，不要其他内容。
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "You are a precise German language assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=300,
                temperature=0.6
            )
            
            if response and response.choices:
                content = response.choices[0].message.content.strip()
                data = json.loads(content)
                
                # 验证数据完整性
                required_fields = ['article', 'plural', 'translations_zh', 'example']
                if all(field in data for field in required_fields):
                    if data['article'] in ['der', 'die', 'das']:
                        return data
            
            return None
            
        except Exception as e:
            print(f"   ❌ 生成名词信息失败: {e}")
            return None
    
    async def generate_complete_verb_info(self, lemma):
        """为动词生成完整信息（变位表、中文翻译、例句）"""
        try:
            prompt = f"""
为德语动词 "{lemma}" 提供完整的语法信息和翻译。

请严格按照以下JSON格式返回:
{{
    "translations_zh": ["中文翻译1", "中文翻译2"],
    "conjugations": {{
        "praesens": {{
            "ich": "form",
            "du": "form", 
            "er_sie_es": "form",
            "wir": "form",
            "ihr": "form",
            "sie_Sie": "form"
        }},
        "praeteritum": {{
            "ich": "form",
            "du": "form",
            "er_sie_es": "form", 
            "wir": "form",
            "ihr": "form",
            "sie_Sie": "form"
        }},
        "perfekt": {{
            "ich": "bin/habe + partizip",
            "du": "bist/hast + partizip",
            "er_sie_es": "ist/hat + partizip",
            "wir": "sind/haben + partizip",
            "ihr": "seid/habt + partizip",
            "sie_Sie": "sind/haben + partizip"
        }},
        "plusquamperfekt": {{
            "ich": "war/hatte + partizip",
            "du": "warst/hattest + partizip",
            "er_sie_es": "war/hatte + partizip",
            "wir": "waren/hatten + partizip",
            "ihr": "wart/hattet + partizip",
            "sie_Sie": "waren/hatten + partizip"
        }},
        "futur_i": {{
            "ich": "werde + infinitiv",
            "du": "wirst + infinitiv",
            "er_sie_es": "wird + infinitiv",
            "wir": "werden + infinitiv",
            "ihr": "werdet + infinitiv",
            "sie_Sie": "werden + infinitiv"
        }},
        "konjunktiv_ii": {{
            "ich": "konjunktiv form",
            "du": "konjunktiv form",
            "er_sie_es": "konjunktiv form",
            "wir": "konjunktiv form",
            "ihr": "konjunktiv form",
            "sie_Sie": "konjunktiv form"
        }},
        "imperativ": {{
            "du": "command form",
            "ihr": "command form",
            "Sie": "command form"
        }}
    }},
    "example": {{
        "de": "德语例句 (使用该动词)",
        "en": "English example sentence",
        "zh": "中文例句"
    }}
}}

要求:
1. 动词变位要准确，包括所有主要时态
2. 包括现在时、过去时、完成时、过去完成时、将来时、虚拟语气、命令式
3. 中文翻译简洁准确
4. 例句要自然实用
5. 助动词选择要正确 (sein/haben)

只返回JSON，不要其他内容。
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "You are a precise German language assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.6
            )
            
            if response and response.choices:
                content = response.choices[0].message.content.strip()
                data = json.loads(content)
                
                # 验证数据完整性
                required_fields = ['translations_zh', 'conjugations', 'example']
                if all(field in data for field in required_fields):
                    if 'praesens' in data['conjugations']:
                        return data
            
            return None
            
        except Exception as e:
            print(f"   ❌ 生成动词信息失败: {e}")
            return None
    
    def save_noun_info_to_database(self, lemma_id, lemma, noun_data):
        """保存名词信息到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            success_count = 0
            
            # 1. 更新notes字段添加冠词和复数
            article = noun_data.get('article')
            plural = noun_data.get('plural')
            
            notes_parts = []
            if article:
                notes_parts.append(f"article:{article}")
            if plural and plural != lemma:  # 避免复数和原形相同时重复
                notes_parts.append(f"plural:{plural}")
            
            if notes_parts:
                notes = " ".join(notes_parts)
                cursor.execute("""
                    UPDATE word_lemmas 
                    SET notes = CASE 
                        WHEN notes IS NULL THEN ?
                        ELSE notes || ' ' || ?
                    END
                    WHERE id = ?
                """, (notes, notes, lemma_id))
                self.stats['articles_added'] += 1
                self.stats['plurals_added'] += 1
                success_count += 1
            
            # 2. 添加中文翻译
            translations_zh = noun_data.get('translations_zh', [])
            for translation in translations_zh:
                cursor.execute("""
                    INSERT INTO translations (lemma_id, lang_code, text, source)
                    VALUES (?, ?, ?, ?)
                """, (lemma_id, "zh", translation.strip(), "openai_enhanced_fix"))
                
            if translations_zh:
                self.stats['chinese_translations_added'] += len(translations_zh)
                success_count += 1
            
            # 3. 添加例句
            example = noun_data.get('example')
            if example and all(key in example for key in ['de', 'en', 'zh']):
                cursor.execute("""
                    INSERT INTO examples (lemma_id, de_text, en_text, zh_text)
                    VALUES (?, ?, ?, ?)
                """, (lemma_id, example['de'], example['en'], example['zh']))
                self.stats['examples_added'] += 1
                success_count += 1
            
            conn.commit()
            return success_count > 0
            
        except Exception as e:
            print(f"   ❌ 保存名词信息失败: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()
    
    def save_verb_info_to_database(self, lemma_id, lemma, verb_data):
        """保存动词信息到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            success_count = 0
            
            # 1. 添加中文翻译
            translations_zh = verb_data.get('translations_zh', [])
            for translation in translations_zh:
                cursor.execute("""
                    INSERT INTO translations (lemma_id, lang_code, text, source)
                    VALUES (?, ?, ?, ?)
                """, (lemma_id, "zh", translation.strip(), "openai_enhanced_fix"))
                
            if translations_zh:
                self.stats['chinese_translations_added'] += len(translations_zh)
                success_count += 1
            
            # 2. 添加动词变位
            conjugations = verb_data.get('conjugations', {})
            conjugation_count = 0
            
            for tense, persons in conjugations.items():
                if isinstance(persons, dict):
                    for person, form in persons.items():
                        if form:
                            cursor.execute("""
                                INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
                                VALUES (?, ?, ?, ?)
                            """, (lemma_id, form, "tense", f"{tense}_{person}"))
                            conjugation_count += 1
            
            if conjugation_count > 0:
                self.stats['verb_conjugations_added'] += conjugation_count
                success_count += 1
            
            # 3. 添加例句
            example = verb_data.get('example')
            if example and all(key in example for key in ['de', 'en', 'zh']):
                cursor.execute("""
                    INSERT INTO examples (lemma_id, de_text, en_text, zh_text)
                    VALUES (?, ?, ?, ?)
                """, (lemma_id, example['de'], example['en'], example['zh']))
                self.stats['examples_added'] += 1
                success_count += 1
            
            conn.commit()
            return success_count > 0
            
        except Exception as e:
            print(f"   ❌ 保存动词信息失败: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()
    
    def get_incomplete_nouns(self, limit=30):
        """获取不完整的名词列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT wl.id, wl.lemma, wl.cefr, wl.frequency, wl.notes
                FROM word_lemmas wl
                WHERE wl.pos = 'noun'
                AND (
                    -- 缺少冠词
                    (wl.notes IS NULL OR wl.notes NOT LIKE '%article:%')
                    -- 或缺少中文翻译
                    OR wl.id NOT IN (SELECT DISTINCT lemma_id FROM translations WHERE lang_code = 'zh')
                    -- 或缺少例句
                    OR wl.id NOT IN (SELECT DISTINCT lemma_id FROM examples WHERE de_text IS NOT NULL)
                )
                ORDER BY 
                    CASE WHEN wl.cefr IN ('A1', 'A2') THEN 1 ELSE 2 END,
                    wl.frequency DESC NULLS LAST,
                    wl.lemma
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            print(f"📋 找到 {len(results)} 个需要修复的名词")
            return results
            
        finally:
            conn.close()
    
    def get_incomplete_verbs(self, limit=20):
        """获取不完整的动词列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT wl.id, wl.lemma, wl.cefr, wl.frequency
                FROM word_lemmas wl
                WHERE wl.pos = 'verb'
                AND (
                    -- 缺少变位
                    wl.id NOT IN (SELECT DISTINCT lemma_id FROM word_forms)
                    -- 或缺少中文翻译
                    OR wl.id NOT IN (SELECT DISTINCT lemma_id FROM translations WHERE lang_code = 'zh')
                    -- 或缺少例句
                    OR wl.id NOT IN (SELECT DISTINCT lemma_id FROM examples WHERE de_text IS NOT NULL)
                )
                ORDER BY 
                    CASE WHEN wl.cefr IN ('A1', 'A2') THEN 1 ELSE 2 END,
                    wl.frequency DESC NULLS LAST,
                    wl.lemma
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            print(f"📋 找到 {len(results)} 个需要修复的动词")
            return results
            
        finally:
            conn.close()
    
    async def fix_incomplete_nouns(self, limit=30):
        """修复不完整的名词"""
        print("🔄 修复不完整名词")
        print("=" * 50)
        
        nouns_to_fix = self.get_incomplete_nouns(limit)
        
        if not nouns_to_fix:
            print("✅ 没有需要修复的名词")
            return
        
        print(f"📝 将处理 {len(nouns_to_fix)} 个名词...")
        
        for i, (lemma_id, lemma, cefr, frequency, notes) in enumerate(nouns_to_fix, 1):
            cefr_str = f" [{cefr}]" if cefr else ""
            freq_str = f" (频率:{frequency})" if frequency else ""
            print(f"[{i}/{len(nouns_to_fix)}] 处理: {lemma}{cefr_str}{freq_str}")
            
            self.stats['words_processed'] += 1
            
            try:
                # 生成完整名词信息
                noun_data = await self.generate_complete_noun_info(lemma, notes)
                
                if noun_data:
                    # 保存到数据库
                    if self.save_noun_info_to_database(lemma_id, lemma, noun_data):
                        article = noun_data.get('article', '?')
                        plural = noun_data.get('plural', '?')
                        print(f"   ✅ {article} {lemma}, 复数: {plural}")
                    else:
                        self.stats['errors'] += 1
                else:
                    print(f"   ❌ 未能生成名词信息")
                    self.stats['errors'] += 1
                
                # 延迟避免API限制
                if i < len(nouns_to_fix):
                    await asyncio.sleep(self.delay)
                    
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                self.stats['errors'] += 1
    
    async def fix_incomplete_verbs(self, limit=20):
        """修复不完整的动词"""
        print("🔄 修复不完整动词")
        print("=" * 50)
        
        verbs_to_fix = self.get_incomplete_verbs(limit)
        
        if not verbs_to_fix:
            print("✅ 没有需要修复的动词")
            return
        
        print(f"📝 将处理 {len(verbs_to_fix)} 个动词...")
        
        for i, (lemma_id, lemma, cefr, frequency) in enumerate(verbs_to_fix, 1):
            cefr_str = f" [{cefr}]" if cefr else ""
            freq_str = f" (频率:{frequency})" if frequency else ""
            print(f"[{i}/{len(verbs_to_fix)}] 处理: {lemma}{cefr_str}{freq_str}")
            
            self.stats['words_processed'] += 1
            
            try:
                # 生成完整动词信息
                verb_data = await self.generate_complete_verb_info(lemma)
                
                if verb_data:
                    # 保存到数据库
                    if self.save_verb_info_to_database(lemma_id, lemma, verb_data):
                        conjugations = verb_data.get('conjugations', {})
                        praesens = conjugations.get('praesens', {})
                        ich_form = praesens.get('ich', '?')
                        print(f"   ✅ {lemma} - ich {ich_form}, 等...")
                    else:
                        self.stats['errors'] += 1
                else:
                    print(f"   ❌ 未能生成动词信息")
                    self.stats['errors'] += 1
                
                # 延迟避免API限制
                if i < len(verbs_to_fix):
                    await asyncio.sleep(self.delay)
                    
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                self.stats['errors'] += 1
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 增强数据库修复完成!")
        print("=" * 60)
        print(f"处理词汇总数: {self.stats['words_processed']}")
        print(f"添加中文翻译: {self.stats['chinese_translations_added']}")
        print(f"添加例句: {self.stats['examples_added']}")
        print(f"添加冠词: {self.stats['articles_added']}")
        print(f"添加复数: {self.stats['plurals_added']}")
        print(f"添加动词变位: {self.stats['verb_conjugations_added']}")
        print(f"错误数量: {self.stats['errors']}")
        print(f"总用时: {elapsed}")
        
        total_improvements = (self.stats['chinese_translations_added'] + 
                            self.stats['examples_added'] + 
                            self.stats['articles_added'] + 
                            self.stats['plurals_added'] + 
                            self.stats['verb_conjugations_added'])
        
        print(f"总改进项目: {total_improvements}")
        
        if total_improvements > 0:
            print(f"\n✅ 修复成功! 用户现在可以在前端看到:")
            print("   • 名词的冠词 (der/die/das)")
            print("   • 名词的复数形式") 
            print("   • 动词的变位表 (现在时/过去时)")
            print("   • 更多中文翻译")
            print("   • 更多例句")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='增强数据库修复器 - 修复所有语法信息')
    parser.add_argument('--mode', 
                       choices=['nouns', 'verbs', 'all'], 
                       default='all',
                       help='修复模式 (默认: all)')
    parser.add_argument('--noun-limit', type=int, default=20, 
                       help='名词处理限制 (默认: 20)')
    parser.add_argument('--verb-limit', type=int, default=15,
                       help='动词处理限制 (默认: 15)')
    parser.add_argument('--delay', type=float, default=3.0,
                       help='API调用延迟(秒) (默认: 3.0)')
    
    args = parser.parse_args()
    
    print("🚀 增强数据库修复器")
    print("=" * 60)
    print("修复内容: 冠词、复数、动词变位、中文翻译、例句")
    print(f"⚙️  配置:")
    print(f"   修复模式: {args.mode}")
    print(f"   名词限制: {args.noun_limit}")
    print(f"   动词限制: {args.verb_limit}")
    print(f"   API延迟: {args.delay}秒")
    
    # 检查OpenAI配置
    if not settings.openai_api_key:
        print("\n❌ 错误: 未配置OpenAI API密钥")
        return
    
    print(f"\n✅ OpenAI配置正常")
    
    fixer = EnhancedDatabaseFixer(delay=args.delay)
    
    try:
        if args.mode in ['nouns', 'all']:
            await fixer.fix_incomplete_nouns(args.noun_limit)
            
        if args.mode in ['verbs', 'all']:
            await fixer.fix_incomplete_verbs(args.verb_limit)
        
        fixer.print_final_stats()
        
        print(f"\n💡 下一步:")
        print("1. 测试前端搜索功能")
        print("2. 验证语法信息显示")
        print("3. 根据需要继续修复更多词汇")
        
    except KeyboardInterrupt:
        print("\n⚠️  修复被用户中断")
        fixer.print_final_stats()
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())