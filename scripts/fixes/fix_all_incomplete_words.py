#!/usr/bin/env python3
"""
修复数据库中所有不完整的词汇
使用OpenAI批量补全所有缺失数据，避免未来重复调用
"""
import asyncio
import sys
import os
import sqlite3
import json
import re
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv(".env")
sys.path.append(os.getcwd())

from app.services.lexicon_llm_service import LexiconLLMService

class DatabaseWordFixer:
    """数据库词汇修复器"""
    
    def __init__(self):
        self.llm_service = LexiconLLMService()
        self.db_path = 'data/app.db'
        self.stats = {
            'total_processed': 0,
            'nouns_fixed': 0,
            'verbs_fixed': 0,
            'adjectives_fixed': 0,
            'other_fixed': 0,
            'already_complete': 0,
            'failed': 0,
            'start_time': datetime.now()
        }
    
    def sanitize_for_json(self, data):
        """清理数据中的无效控制字符，使其可以被JSON序列化"""
        if isinstance(data, str):
            # 移除或替换控制字符（保留换行符、制表符、回车符）
            return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', data)
        elif isinstance(data, dict):
            return {k: self.sanitize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_for_json(item) for item in data]
        else:
            return data
    
    def safe_json_dumps(self, data):
        """安全的JSON序列化，带有错误处理"""
        try:
            sanitized_data = self.sanitize_for_json(data)
            return json.dumps(sanitized_data, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            print(f"   ⚠️ JSON序列化失败: {e}")
            # 如果序列化失败，返回一个空的JSON对象
            return "{}"
    
    def get_incomplete_words(self, limit=None):
        """获取所有不完整的词汇"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找所有不完整的词汇
            query = """
                SELECT 
                    wl.id as lemma_id,
                    wl.lemma,
                    wl.pos as legacy_pos,
                    ls.id as sense_id,
                    ls.upos,
                    ls.gender,
                    ls.gloss_en,
                    ls.gloss_zh,
                    ls.confidence,
                    np.gen_sg,
                    np.plural,
                    vp.aux,
                    vp.partizip_ii,
                    COUNT(fu.id) as form_count,
                    COUNT(ex.id) as example_count
                FROM word_lemmas wl
                JOIN lemma_senses ls ON ls.lemma_id = wl.id
                LEFT JOIN noun_props np ON np.sense_id = ls.id
                LEFT JOIN verb_props vp ON vp.sense_id = ls.id
                LEFT JOIN forms_unimorph fu ON fu.sense_id = ls.id
                LEFT JOIN examples ex ON ex.sense_id = ls.id AND ex.de_text IS NOT NULL AND ex.de_text != ''
                WHERE 
                    -- 基础问题：词性错误或缺少释义
                    (ls.upos IN ('UNKNOWN', 'OTHER') OR ls.upos IS NULL)
                    OR (ls.gloss_en IS NULL OR ls.gloss_zh IS NULL)
                    OR (ls.confidence < 0.8)
                    -- 名词问题：缺少性别或复数
                    OR (ls.upos = 'NOUN' AND (ls.gender IS NULL OR np.plural IS NULL))
                    -- 动词问题：缺少助动词或过去分词
                    OR (ls.upos = 'VERB' AND (vp.aux IS NULL OR vp.partizip_ii IS NULL))
                    -- 缺少例句
                    OR (ex.id IS NULL)
                GROUP BY wl.id, ls.id
                ORDER BY 
                    -- 优先处理明显错误的词汇
                    CASE 
                        WHEN ls.upos IN ('UNKNOWN', 'OTHER') THEN 1
                        WHEN ls.gloss_en IS NULL OR ls.gloss_zh IS NULL THEN 2
                        WHEN ls.upos = 'VERB' AND vp.aux IS NULL THEN 3
                        WHEN ls.upos = 'NOUN' AND ls.gender IS NULL THEN 4
                        ELSE 5
                    END,
                    wl.lemma
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            print(f"📊 找到 {len(results)} 个需要修复的词条")
            return results
            
        finally:
            conn.close()
    
    async def fix_word(self, word_data):
        """修复单个词汇"""
        lemma = word_data['lemma']
        upos = word_data['upos']
        sense_id = word_data['sense_id']
        
        try:
            print(f"\n🔧 修复: {lemma} ({upos})")
            
            # 判断需要修复的类型
            needs_basic_fix = (
                upos in ('UNKNOWN', 'OTHER') or 
                not word_data.get('gloss_en') or 
                not word_data.get('gloss_zh') or
                word_data.get('confidence', 0) < 0.8
            )
            
            if needs_basic_fix:
                # 需要重新识别词性和基础信息
                await self._fix_basic_word_info(word_data)
                # 重新获取更新后的数据
                word_data = await self._get_updated_word_data(word_data['lemma_id'])
                upos = word_data['upos']
            
            # 根据词性进行专门修复
            if upos == 'NOUN':
                await self._fix_noun(word_data)
                self.stats['nouns_fixed'] += 1
            elif upos == 'VERB':
                await self._fix_verb(word_data)
                self.stats['verbs_fixed'] += 1
            elif upos in ('ADJ', 'ADJECTIVE'):
                await self._fix_adjective(word_data)
                self.stats['adjectives_fixed'] += 1
            else:
                await self._fix_other(word_data)
                self.stats['other_fixed'] += 1
            
            print(f"   ✅ 修复完成")
            
        except Exception as e:
            print(f"   ❌ 修复失败: {e}")
            self.stats['failed'] += 1
        finally:
            self.stats['total_processed'] += 1
    
    async def _fix_basic_word_info(self, word_data):
        """修复基础词汇信息（词性识别）"""
        lemma = word_data['lemma']
        
        # 调用OpenAI重新分析词汇
        print(f"   🤖 重新分析词汇基础信息...")
        
        # 使用词汇消歧功能
        disambiguation = await self.llm_service.disambiguate_lemma(lemma)
        
        if disambiguation and disambiguation.get('senses'):
            # 取第一个（最可能的）词性
            primary_sense = disambiguation['senses'][0]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 更新词性
                new_upos = primary_sense.get('upos', 'OTHER')
                new_xpos = primary_sense.get('xpos', 'OTHER')
                
                cursor.execute("""
                    UPDATE word_lemmas 
                    SET pos = ?
                    WHERE id = ?
                """, (new_upos.lower(), word_data['lemma_id']))
                
                cursor.execute("""
                    UPDATE lemma_senses 
                    SET upos = ?, xpos = ?, gender = ?, gloss_en = ?, gloss_zh = ?, 
                        confidence = 0.85, source = 'openai_batch_fix'
                    WHERE id = ?
                """, (
                    new_upos, new_xpos,
                    primary_sense.get('gender'),
                    primary_sense.get('gloss_en'),
                    primary_sense.get('gloss_zh'),
                    word_data['sense_id']
                ))
                
                conn.commit()
                print(f"   ✅ 更新词性: {new_upos}")
                
            finally:
                conn.close()
    
    async def _get_updated_word_data(self, lemma_id):
        """获取更新后的词汇数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    wl.id as lemma_id, wl.lemma, wl.pos as legacy_pos,
                    ls.id as sense_id, ls.upos, ls.gender, ls.gloss_en, ls.gloss_zh, ls.confidence
                FROM word_lemmas wl
                JOIN lemma_senses ls ON ls.lemma_id = wl.id
                WHERE wl.id = ?
            """, (lemma_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
            
        finally:
            conn.close()
    
    async def _fix_noun(self, word_data):
        """修复名词"""
        if word_data.get('gender') and word_data.get('plural'):
            print(f"   ⚠️ 名词已完整，跳过")
            self.stats['already_complete'] += 1
            return
        
        lemma = word_data['lemma']
        context = {'existing_data': word_data}
        
        print(f"   🤖 获取名词属性...")
        noun_data = await self.llm_service.enrich_noun(lemma, context)
        
        if noun_data:
            await self._save_noun_data(word_data['sense_id'], noun_data)
    
    async def _fix_verb(self, word_data):
        """修复动词"""
        if word_data.get('aux') and word_data.get('partizip_ii'):
            print(f"   ⚠️ 动词已完整，跳过")
            self.stats['already_complete'] += 1
            return
        
        lemma = word_data['lemma']
        context = {'existing_data': word_data}
        
        print(f"   🤖 获取动词属性...")
        verb_data = await self.llm_service.enrich_verb(lemma, context)
        
        if verb_data:
            await self._save_verb_data(word_data['sense_id'], verb_data)
    
    async def _fix_adjective(self, word_data):
        """修复形容词"""
        lemma = word_data['lemma']
        context = {'existing_data': word_data}
        
        print(f"   🤖 获取形容词属性...")
        adj_data = await self.llm_service.enrich_adjective(lemma, context)
        
        if adj_data:
            await self._save_adjective_data(word_data['sense_id'], adj_data)
    
    async def _fix_other(self, word_data):
        """修复其他词性"""
        # 对于其他词性，只确保有基础的释义和例句
        if word_data.get('gloss_en') and word_data.get('gloss_zh') and word_data.get('example_count', 0) > 0:
            print(f"   ⚠️ 其他词性已完整，跳过")
            self.stats['already_complete'] += 1
            return
        
        # 生成基础例句
        await self._ensure_example(word_data)
    
    async def _save_noun_data(self, sense_id, data):
        """保存名词数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 更新sense信息
            cursor.execute("""
                UPDATE lemma_senses 
                SET gender = COALESCE(gender, ?),
                    gloss_en = COALESCE(gloss_en, ?),
                    gloss_zh = COALESCE(gloss_zh, ?),
                    confidence = MAX(confidence, 0.9)
                WHERE id = ?
            """, (
                data.get('gender'),
                data.get('gloss_en'),
                data.get('gloss_zh'),
                sense_id
            ))
            
            # 保存名词属性
            noun_props = data.get('noun_props', {})
            if noun_props:
                cursor.execute("""
                    INSERT OR REPLACE INTO noun_props 
                    (sense_id, gen_sg, plural, declension_class, dative_plural_ends_n)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    sense_id,
                    noun_props.get('gen_sg'),
                    noun_props.get('plural'),
                    noun_props.get('declension_class'),
                    noun_props.get('dative_plural_ends_n', False)
                ))
            
            # 保存词形和例句
            await self._save_forms_and_examples(cursor, sense_id, data)
            conn.commit()
            
        finally:
            conn.close()
    
    async def _save_verb_data(self, sense_id, data):
        """保存动词数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 更新sense信息
            cursor.execute("""
                UPDATE lemma_senses 
                SET gloss_en = COALESCE(gloss_en, ?),
                    gloss_zh = COALESCE(gloss_zh, ?),
                    confidence = MAX(confidence, 0.9)
                WHERE id = ?
            """, (
                data.get('gloss_en'),
                data.get('gloss_zh'),
                sense_id
            ))
            
            # 保存动词属性
            cursor.execute("""
                INSERT OR REPLACE INTO verb_props 
                (sense_id, separable, prefix, aux, regularity, partizip_ii, reflexive, valency_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sense_id,
                data.get('separable', False),
                data.get('prefix'),
                data.get('aux'),
                data.get('regularity'),
                data.get('partizip_ii'),
                data.get('reflexive', False),
                self.safe_json_dumps(data.get('valency', {}))
            ))
            
            # 保存变位表
            await self._save_verb_conjugations(cursor, sense_id, data.get('tables', {}))
            
            # 保存例句
            await self._save_forms_and_examples(cursor, sense_id, data)
            conn.commit()
            
        finally:
            conn.close()
    
    async def _save_adjective_data(self, sense_id, data):
        """保存形容词数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 更新sense信息
            cursor.execute("""
                UPDATE lemma_senses 
                SET gloss_en = COALESCE(gloss_en, ?),
                    gloss_zh = COALESCE(gloss_zh, ?),
                    confidence = MAX(confidence, 0.9)
                WHERE id = ?
            """, (
                data.get('gloss_en'),
                data.get('gloss_zh'),
                sense_id
            ))
            
            # 保存例句
            await self._save_forms_and_examples(cursor, sense_id, data)
            conn.commit()
            
        finally:
            conn.close()
    
    async def _save_verb_conjugations(self, cursor, sense_id, tables):
        """保存动词变位"""
        for tense, forms in tables.items():
            if isinstance(forms, dict):
                for person, form in forms.items():
                    if form:
                        cursor.execute("""
                            INSERT OR IGNORE INTO forms_unimorph
                            (sense_id, form, features_json)
                            VALUES (?, ?, ?)
                        """, (
                            sense_id,
                            form,
                            self.safe_json_dumps({
                                "POS": "VERB",
                                "Tense": tense.title(),
                                "Person": person
                            })
                        ))
    
    async def _save_forms_and_examples(self, cursor, sense_id, data):
        """保存词形变化和例句"""
        # 保存词形
        forms = data.get('forms', [])
        for form_data in forms:
            cursor.execute("""
                INSERT OR IGNORE INTO forms_unimorph
                (sense_id, form, features_json)
                VALUES (?, ?, ?)
            """, (
                sense_id,
                form_data.get('form'),
                self.safe_json_dumps(form_data.get('features', {}))
            ))
        
        # 保存例句
        example = data.get('example')
        if example and example.get('de'):
            # 先检查是否已有例句
            cursor.execute("""
                SELECT COUNT(*) FROM examples 
                WHERE sense_id = ? AND de_text IS NOT NULL AND de_text != ''
            """, (sense_id,))
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO examples
                    (lemma_id, sense_id, de_text, en_text, zh_text, level)
                    SELECT ls.lemma_id, ?, ?, ?, ?, 'A1'
                    FROM lemma_senses ls 
                    WHERE ls.id = ?
                """, (
                    sense_id,
                    example.get('de'),
                    example.get('en'),
                    example.get('zh'),
                    sense_id
                ))
    
    async def _ensure_example(self, word_data):
        """确保有例句"""
        if word_data['example_count'] > 0:
            return
        
        # 简单生成例句的逻辑可以在这里实现
        pass
    
    def print_progress(self, current, total):
        """打印进度"""
        percentage = (current / total * 100) if total > 0 else 0
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n📊 进度: {current}/{total} ({percentage:.1f}%)")
        print(f"   已修复名词: {self.stats['nouns_fixed']}")
        print(f"   已修复动词: {self.stats['verbs_fixed']}")
        print(f"   已修复形容词: {self.stats['adjectives_fixed']}")
        print(f"   已修复其他: {self.stats['other_fixed']}")
        print(f"   已完整: {self.stats['already_complete']}")
        print(f"   失败: {self.stats['failed']}")
        print(f"   用时: {elapsed}")
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 批量修复完成！")
        print(f"=" * 50)
        print(f"总处理词条: {self.stats['total_processed']}")
        print(f"修复名词: {self.stats['nouns_fixed']}")
        print(f"修复动词: {self.stats['verbs_fixed']}")
        print(f"修复形容词: {self.stats['adjectives_fixed']}")
        print(f"修复其他: {self.stats['other_fixed']}")
        print(f"已完整: {self.stats['already_complete']}")
        print(f"失败: {self.stats['failed']}")
        print(f"总用时: {elapsed}")

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量修复数据库中的不完整词汇')
    parser.add_argument('--limit', type=int, help='限制处理的词条数量')
    parser.add_argument('--batch-size', type=int, default=10, help='批次大小')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式')
    
    args = parser.parse_args()
    
    print("🚀 批量修复数据库词汇")
    print("=" * 50)
    
    if args.dry_run:
        print("⚠️ 试运行模式 - 不会保存数据")
    
    fixer = DatabaseWordFixer()
    
    # 获取需要修复的词汇
    incomplete_words = fixer.get_incomplete_words(args.limit)
    
    if not incomplete_words:
        print("✅ 所有词汇都已完整！")
        return
    
    print(f"开始批量修复 {len(incomplete_words)} 个词条...")
    print(f"批次大小: {args.batch_size}")
    
    # 分批处理，避免API限制
    for i in range(0, len(incomplete_words), args.batch_size):
        batch = incomplete_words[i:i + args.batch_size]
        
        print(f"\n📦 处理批次 {i//args.batch_size + 1} ({len(batch)} 个词条)")
        
        for j, word_data in enumerate(batch):
            if not args.dry_run:
                await fixer.fix_word(word_data)
            else:
                print(f"   试运行: {word_data['lemma']} ({word_data['upos']})")
            
            # 每个词之间稍作延迟
            await asyncio.sleep(0.5)
        
        # 批次间休息
        if i + args.batch_size < len(incomplete_words):
            print(f"💤 批次完成，休息1秒...")
            await asyncio.sleep(1)
        
        # 显示进度
        fixer.print_progress(min(i + args.batch_size, len(incomplete_words)), len(incomplete_words))
    
    fixer.print_final_stats()

if __name__ == "__main__":
    asyncio.run(main())
