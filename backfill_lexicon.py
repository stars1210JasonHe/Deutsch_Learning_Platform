#!/usr/bin/env python3
"""
德语词库批量回填脚本
使用OpenAI补全现有词条的缺失字段
"""
import asyncio
import sys
import os
import sqlite3
import json
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(" - Copy.env")
sys.path.append(os.getcwd())

from app.services.lexicon_llm_service import LexiconLLMService

class LexiconBackfillService:
    """词库回填服务"""
    
    def __init__(self):
        self.llm_service = LexiconLLMService()
        self.db_path = 'data/app.db'
        
        # 统计信息
        self.stats = {
            'processed': 0,
            'enriched_nouns': 0,
            'enriched_verbs': 0,
            'enriched_adjectives': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': datetime.now()
        }
    
    def get_incomplete_lemmas(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """获取需要补全的词条"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找缺少重要字段的词条
            query = """
                SELECT 
                    wl.id as lemma_id,
                    wl.lemma,
                    wl.pos,
                    ls.id as sense_id,
                    ls.upos,
                    ls.gender,
                    ls.gloss_en,
                    ls.gloss_zh,
                    np.gen_sg,
                    np.plural,
                    vp.aux,
                    vp.partizip_ii,
                    COUNT(fu.id) as form_count
                FROM word_lemmas wl
                JOIN lemma_senses ls ON ls.lemma_id = wl.id
                LEFT JOIN noun_props np ON np.sense_id = ls.id
                LEFT JOIN verb_props vp ON vp.sense_id = ls.id
                LEFT JOIN forms_unimorph fu ON fu.sense_id = ls.id
                WHERE 
                    -- 名词缺少性别或复数
                    (ls.upos = 'NOUN' AND (ls.gender IS NULL OR np.plural IS NULL))
                    OR
                    -- 动词缺少助动词或过去分词
                    (ls.upos = 'VERB' AND (vp.aux IS NULL OR vp.partizip_ii IS NULL))
                    OR
                    -- 缺少英文或中文释义
                    (ls.gloss_en IS NULL OR ls.gloss_zh IS NULL)
                    OR
                    -- 缺少词形变化
                    (fu.id IS NULL)
                GROUP BY wl.id, ls.id
                ORDER BY 
                    CASE wl.pos 
                        WHEN 'noun' THEN 1
                        WHEN 'verb' THEN 2
                        WHEN 'adjective' THEN 3
                        ELSE 4
                    END,
                    wl.lemma
            """
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            print(f"📊 找到 {len(results)} 个需要补全的词条")
            return results
            
        finally:
            conn.close()
    
    async def enrich_lemma(self, lemma_data: Dict[str, Any]) -> bool:
        """补全单个词条"""
        lemma = lemma_data['lemma']
        upos = lemma_data['upos']
        sense_id = lemma_data['sense_id']
        
        try:
            print(f"\n🔍 处理: {lemma} ({upos})")
            
            if upos == 'NOUN':
                return await self._enrich_noun(lemma_data)
            elif upos == 'VERB':
                return await self._enrich_verb(lemma_data)
            elif upos == 'ADJ':
                return await self._enrich_adjective(lemma_data)
            else:
                print(f"   ⚠️ 跳过不支持的词性: {upos}")
                self.stats['skipped'] += 1
                return False
                
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            self.stats['failed'] += 1
            return False
        finally:
            self.stats['processed'] += 1
    
    async def _enrich_noun(self, lemma_data: Dict[str, Any]) -> bool:
        """补全名词"""
        lemma = lemma_data['lemma']
        sense_id = lemma_data['sense_id']
        
        # 检查是否需要补全
        needs_enrichment = (
            not lemma_data['gender'] or 
            not lemma_data['plural'] or
            not lemma_data['gloss_en'] or
            not lemma_data['gloss_zh'] or
            lemma_data['form_count'] == 0
        )
        
        if not needs_enrichment:
            print(f"   ✅ {lemma} 已完整，跳过")
            self.stats['skipped'] += 1
            return True
        
        # 构建上下文
        context = {}
        if lemma_data.get('gender'):
            context['existing_gender'] = lemma_data['gender']
        
        # 调用LLM获取补全数据
        print(f"   🤖 调用LLM补全名词数据...")
        enrichment_data = await self.llm_service.enrich_noun(lemma, context)
        
        if not enrichment_data:
            print(f"   ❌ LLM返回空数据")
            return False
        
        # 保存到数据库
        return await self._save_noun_data(sense_id, enrichment_data)
    
    async def _enrich_verb(self, lemma_data: Dict[str, Any]) -> bool:
        """补全动词"""
        lemma = lemma_data['lemma']
        sense_id = lemma_data['sense_id']
        
        # 检查是否需要补全
        needs_enrichment = (
            not lemma_data['aux'] or
            not lemma_data['partizip_ii'] or
            not lemma_data['gloss_en'] or
            not lemma_data['gloss_zh'] or
            lemma_data['form_count'] == 0
        )
        
        if not needs_enrichment:
            print(f"   ✅ {lemma} 已完整，跳过")
            self.stats['skipped'] += 1
            return True
        
        # 调用LLM获取补全数据
        print(f"   🤖 调用LLM补全动词数据...")
        enrichment_data = await self.llm_service.enrich_verb(lemma)
        
        if not enrichment_data:
            print(f"   ❌ LLM返回空数据")
            return False
        
        # 保存到数据库
        return await self._save_verb_data(sense_id, enrichment_data)
    
    async def _enrich_adjective(self, lemma_data: Dict[str, Any]) -> bool:
        """补全形容词"""
        lemma = lemma_data['lemma']
        sense_id = lemma_data['sense_id']
        
        # 调用LLM获取补全数据
        print(f"   🤖 调用LLM补全形容词数据...")
        enrichment_data = await self.llm_service.enrich_adjective(lemma)
        
        if not enrichment_data:
            print(f"   ❌ LLM返回空数据")
            return False
        
        # 保存基础数据
        return await self._save_adjective_data(sense_id, enrichment_data)
    
    async def _save_noun_data(self, sense_id: int, data: Dict[str, Any]) -> bool:
        """保存名词数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 更新 lemma_senses
            cursor.execute("""
                UPDATE lemma_senses 
                SET gender = COALESCE(gender, ?),
                    gloss_en = COALESCE(gloss_en, ?),
                    gloss_zh = COALESCE(gloss_zh, ?),
                    confidence = 0.8,
                    source = 'openai_backfill'
                WHERE id = ?
            """, (
                data.get('gender'),
                data.get('gloss_en'),
                data.get('gloss_zh'),
                sense_id
            ))
            
            # 插入或更新 noun_props
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
            
            # 插入词形变化
            forms = data.get('forms', [])
            for form_data in forms:
                cursor.execute("""
                    INSERT OR IGNORE INTO forms_unimorph
                    (sense_id, form, features_json)
                    VALUES (?, ?, ?)
                """, (
                    sense_id,
                    form_data.get('form'),
                    json.dumps(form_data.get('features', {}))
                ))
            
            # 插入例句（如果不存在）
            example = data.get('example')
            if example:
                cursor.execute("""
                    INSERT OR IGNORE INTO examples
                    (lemma_id, sense_id, de_text, en_text, zh_text, level)
                    SELECT ls.lemma_id, ?, ?, ?, ?, 'A1'
                    FROM lemma_senses ls 
                    WHERE ls.id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM examples e2 
                        WHERE e2.sense_id = ? AND e2.de_text = ?
                    )
                """, (
                    sense_id,
                    example.get('de'),
                    example.get('en'),
                    example.get('zh'),
                    sense_id,
                    sense_id,
                    example.get('de')
                ))
            
            conn.commit()
            self.stats['enriched_nouns'] += 1
            print(f"   ✅ 名词数据已保存")
            return True
            
        except Exception as e:
            print(f"   ❌ 保存名词数据失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    async def _save_verb_data(self, sense_id: int, data: Dict[str, Any]) -> bool:
        """保存动词数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 更新 lemma_senses
            cursor.execute("""
                UPDATE lemma_senses 
                SET gloss_en = COALESCE(gloss_en, ?),
                    gloss_zh = COALESCE(gloss_zh, ?),
                    confidence = 0.8,
                    source = 'openai_backfill'
                WHERE id = ?
            """, (
                data.get('gloss_en'),
                data.get('gloss_zh'),
                sense_id
            ))
            
            # 插入或更新 verb_props
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
                json.dumps(data.get('valency', {}))
            ))
            
            # 插入动词变位形式
            tables = data.get('tables', {})
            
            # Präsens
            praesens = tables.get('praesens', {})
            for person, form in praesens.items():
                if form:
                    cursor.execute("""
                        INSERT OR IGNORE INTO forms_unimorph
                        (sense_id, form, features_json)
                        VALUES (?, ?, ?)
                    """, (
                        sense_id,
                        form,
                        json.dumps({"POS": "VERB", "Tense": "Pres", "Person": person})
                    ))
            
            # Präteritum
            praeteritum = tables.get('praeteritum', {})
            for person, form in praeteritum.items():
                if form:
                    cursor.execute("""
                        INSERT OR IGNORE INTO forms_unimorph
                        (sense_id, form, features_json)
                        VALUES (?, ?, ?)
                    """, (
                        sense_id,
                        form,
                        json.dumps({"POS": "VERB", "Tense": "Past", "Person": person})
                    ))
            
            # 插入例句
            example = data.get('example')
            if example:
                cursor.execute("""
                    INSERT OR IGNORE INTO examples
                    (lemma_id, sense_id, de_text, en_text, zh_text, level)
                    SELECT ls.lemma_id, ?, ?, ?, ?, 'A1'
                    FROM lemma_senses ls 
                    WHERE ls.id = ?
                    AND NOT EXISTS (
                        SELECT 1 FROM examples e2 
                        WHERE e2.sense_id = ? AND e2.de_text = ?
                    )
                """, (
                    sense_id,
                    example.get('de'),
                    example.get('en'),
                    example.get('zh'),
                    sense_id,
                    sense_id,
                    example.get('de')
                ))
            
            conn.commit()
            self.stats['enriched_verbs'] += 1
            print(f"   ✅ 动词数据已保存")
            return True
            
        except Exception as e:
            print(f"   ❌ 保存动词数据失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    async def _save_adjective_data(self, sense_id: int, data: Dict[str, Any]) -> bool:
        """保存形容词数据到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 更新基础信息
            cursor.execute("""
                UPDATE lemma_senses 
                SET gloss_en = COALESCE(gloss_en, ?),
                    gloss_zh = COALESCE(gloss_zh, ?),
                    confidence = 0.8,
                    source = 'openai_backfill'
                WHERE id = ?
            """, (
                data.get('gloss_en'),
                data.get('gloss_zh'),
                sense_id
            ))
            
            # 插入例句
            example = data.get('example')
            if example:
                cursor.execute("""
                    INSERT OR IGNORE INTO examples
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
            
            conn.commit()
            self.stats['enriched_adjectives'] += 1
            print(f"   ✅ 形容词数据已保存")
            return True
            
        except Exception as e:
            print(f"   ❌ 保存形容词数据失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def print_stats(self):
        """打印统计信息"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n📊 回填统计:")
        print(f"   处理词条: {self.stats['processed']}")
        print(f"   补全名词: {self.stats['enriched_nouns']}")
        print(f"   补全动词: {self.stats['enriched_verbs']}")
        print(f"   补全形容词: {self.stats['enriched_adjectives']}")
        print(f"   跳过: {self.stats['skipped']}")
        print(f"   失败: {self.stats['failed']}")
        print(f"   用时: {elapsed}")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='德语词库批量回填')
    parser.add_argument('--limit', type=int, default=50, help='处理词条数量限制')
    parser.add_argument('--offset', type=int, default=0, help='开始偏移量')
    parser.add_argument('--dry-run', action='store_true', help='试运行，不保存数据')
    
    args = parser.parse_args()
    
    print("🚀 德语词库批量回填")
    print("=" * 50)
    
    if args.dry_run:
        print("⚠️ 试运行模式 - 不会保存数据")
    
    service = LexiconBackfillService()
    
    # 获取需要补全的词条
    incomplete_lemmas = service.get_incomplete_lemmas(args.limit, args.offset)
    
    if not incomplete_lemmas:
        print("✅ 所有词条都已完整，无需回填")
        return
    
    print(f"开始处理 {len(incomplete_lemmas)} 个词条...")
    
    # 批量处理
    for i, lemma_data in enumerate(incomplete_lemmas, 1):
        print(f"\n[{i}/{len(incomplete_lemmas)}]", end=" ")
        
        if not args.dry_run:
            await service.enrich_lemma(lemma_data)
        else:
            print(f"试运行: {lemma_data['lemma']} ({lemma_data['upos']})")
        
        # 每10个词条休息一下，避免API限制
        if i % 10 == 0:
            print(f"\n💤 已处理 {i} 个词条，休息3秒...")
            await asyncio.sleep(3)
    
    service.print_stats()
    print("\n🎉 批量回填完成！")

if __name__ == "__main__":
    asyncio.run(main())
