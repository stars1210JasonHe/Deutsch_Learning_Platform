#!/usr/bin/env python3
"""
PDF词汇导入器 - 从DTZ词汇列表PDF中提取德语单词并导入数据库
支持自动去重、词性识别和LLM增强
"""
import asyncio
import sys
import os
import re
import json
import sqlite3
from datetime import datetime
from typing import List, Set, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(".env")
sys.path.append(os.getcwd())

try:
    import PyPDF2
except ImportError:
    print("❌ 需要安装PyPDF2库: pip install PyPDF2")
    sys.exit(1)

from app.services.lexicon_llm_service import LexiconLLMService

class PDFVocabularyExtractor:
    """PDF词汇提取器 - 使用AI进行智能词汇识别"""
    
    def __init__(self):
        self.llm_service = LexiconLLMService()
        # 基本文本清理模式
        self.cleanup_patterns = [
            r'\s+',  # 多个空格
            r'[\x00-\x1f\x7f-\x9f]',  # 控制字符
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF文件提取文本"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                print(f"📖 PDF共有 {len(pdf_reader.pages)} 页")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        
                        if page_num % 10 == 0:
                            print(f"   已处理 {page_num + 1} 页...")
                            
                    except Exception as e:
                        print(f"   ⚠️ 第 {page_num + 1} 页提取失败: {e}")
                        continue
                
                return text
                
        except Exception as e:
            print(f"❌ 读取PDF失败: {e}")
            return ""
    
    async def extract_german_words_with_ai(self, text: str, chunk_size: int = 2000) -> Set[str]:
        """使用AI从文本中智能提取德语单词"""
        words = set()
        
        # 清理文本
        cleaned_text = self._clean_text(text)
        
        # 将文本分块处理，避免超过AI模型限制
        text_chunks = self._split_text_into_chunks(cleaned_text, chunk_size)
        
        print(f"📝 文本分为 {len(text_chunks)} 个块进行AI分析...")
        
        for i, chunk in enumerate(text_chunks):
            print(f"   处理块 {i + 1}/{len(text_chunks)}...")
            
            try:
                chunk_words = await self._extract_words_from_chunk(chunk)
                words.update(chunk_words)
                
                # 避免API速率限制
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ⚠️ 块 {i + 1} 处理失败: {e}")
                continue
        
        return words
    
    def _clean_text(self, text: str) -> str:
        """清理文本，移除不必要的字符"""
        cleaned = text
        
        for pattern in self.cleanup_patterns:
            cleaned = re.sub(pattern, ' ', cleaned)
        
        return cleaned.strip()
    
    def _split_text_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """将文本分割成适合AI处理的块"""
        chunks = []
        words = text.split()
        
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    async def _extract_words_from_chunk(self, text_chunk: str) -> Set[str]:
        """使用AI从文本块中提取德语词汇"""
        system_prompt = """You are a German vocabulary extraction expert. Your task is to identify and extract all German vocabulary words (lemmas) from the given text.

Instructions:
1. Extract ONLY German vocabulary words (nouns, verbs, adjectives, adverbs, etc.)
2. Return the base form (lemma) of each word
3. For nouns: return without articles (e.g., "Haus" not "das Haus")
4. For verbs: return infinitive form (e.g., "gehen" not "geht")
5. For adjectives: return base form (e.g., "schön" not "schöne")
6. Exclude: numbers, punctuation, common function words (articles, prepositions, conjunctions)
7. Include compound words and technical terms
8. Return ONLY a JSON object with a "words" array, no explanation

Example output format:
{"words": ["Haus", "gehen", "schön", "Deutschland", "arbeiten"]}"""

        user_prompt = f"""Extract all German vocabulary words from this text:

{text_chunk}

Return only a JSON object with a "words" array containing German lemmas."""

        try:
            # 使用OpenAI服务
            response = await self.llm_service.openai_service.client.chat.completions.create(
                model=self.llm_service.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # 解析JSON响应
            response_content = response.choices[0].message.content
            response_data = json.loads(response_content.strip())
            
            words_list = response_data.get('words', [])
            if isinstance(words_list, list):
                # 过滤和验证单词
                valid_words = set()
                for word in words_list:
                    if isinstance(word, str) and self._is_valid_german_word(word):
                        valid_words.add(word.strip())
                
                return valid_words
            else:
                print(f"   ⚠️ AI返回格式不正确: {response_content[:100]}...")
                return set()
                
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON解析失败: {e}")
            return set()
        except Exception as e:
            print(f"   ⚠️ AI提取失败: {e}")
            return set()
    
    def _is_valid_german_word(self, word: str) -> bool:
        """验证是否为有效的德语单词"""
        if not word or len(word) < 2 or len(word) > 30:
            return False
        
        # 检查是否包含德语字符
        if not re.match(r'^[A-Za-zÄÖÜäöüß]+$', word):
            return False
        
        # 排除纯数字或过短的单词
        if word.isdigit() or (word.isupper() and len(word) <= 3):
            return False
        
        return True
    
    async def categorize_words_with_ai(self, words: Set[str], batch_size: int = 50) -> Dict[str, List[str]]:
        """使用AI对词汇进行分类"""
        categorized = {
            'nouns': [],
            'verbs': [],
            'adjectives': [],
            'others': []
        }
        
        word_list = list(words)
        total_batches = (len(word_list) + batch_size - 1) // batch_size
        
        print(f"🏷️ 使用AI对 {len(word_list)} 个单词进行词性分类...")
        print(f"   分为 {total_batches} 个批次处理")
        
        for i in range(0, len(word_list), batch_size):
            batch = word_list[i:i + batch_size]
            print(f"   处理批次 {i//batch_size + 1}/{total_batches}...")
            
            try:
                batch_categorized = await self._categorize_word_batch(batch)
                
                # 合并结果
                for category, batch_words in batch_categorized.items():
                    if category in categorized:
                        categorized[category].extend(batch_words)
                
                # 避免API速率限制
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   ⚠️ 批次 {i//batch_size + 1} 分类失败: {e}")
                # 如果AI分类失败，使用简单的启发式方法
                for word in batch:
                    if word[0].isupper():
                        categorized['nouns'].append(word)
                    elif word.lower().endswith('en'):
                        categorized['verbs'].append(word)
                    else:
                        categorized['others'].append(word)
        
        return categorized
    
    async def _categorize_word_batch(self, words: List[str]) -> Dict[str, List[str]]:
        """使用AI对一批单词进行词性分类"""
        system_prompt = """You are a German linguistic expert. Classify the given German words by their part of speech (POS).

Instructions:
1. Classify each word as: NOUN, VERB, ADJECTIVE, or OTHER
2. For nouns: include compound nouns, proper nouns
3. For verbs: include infinitive forms, separable verbs
4. For adjectives: include comparative/superlative forms
5. OTHER: adverbs, prepositions, conjunctions, particles, etc.
6. Return ONLY a JSON object with words categorized by POS

Example output format:
{
  "nouns": ["Haus", "Deutschland", "Arbeit"],
  "verbs": ["gehen", "arbeiten", "verstehen"],
  "adjectives": ["schön", "groß", "wichtig"],
  "others": ["schnell", "aber", "mit"]
}"""

        words_text = ", ".join(words)
        user_prompt = f"""Classify these German words by part of speech:

{words_text}

Return only the JSON categorization."""

        try:
            response = await self.llm_service.openai_service.client.chat.completions.create(
                model=self.llm_service.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            response_content = response.choices[0].message.content
            categorization = json.loads(response_content.strip())
            
            # 标准化键名
            normalized = {}
            for key, word_list in categorization.items():
                normalized_key = key.lower().rstrip('s')  # "nouns" -> "noun"
                if normalized_key in ['noun', 'verb', 'adjective']:
                    normalized[normalized_key + 's'] = word_list
                else:
                    normalized['others'] = normalized.get('others', []) + word_list
            
            return normalized
            
        except Exception as e:
            print(f"   ⚠️ AI分类失败: {e}")
            return {"nouns": [], "verbs": [], "adjectives": [], "others": words}

class PDFDatabaseImporter:
    """PDF词汇数据库导入器"""
    
    def __init__(self):
        self.llm_service = LexiconLLMService()
        self.db_path = 'data/app.db'
        self.stats = {
            'total_words': 0,
            'existing_words': 0,
            'new_words': 0,
            'enhanced_words': 0,
            'failed_words': 0,
            'start_time': datetime.now()
        }
    
    def word_exists_in_database(self, lemma: str) -> bool:
        """检查单词是否已存在于数据库中"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查新架构（lemma_senses表）
            cursor.execute("""
                SELECT COUNT(*) FROM word_lemmas 
                WHERE LOWER(lemma) = LOWER(?)
            """, (lemma,))
            
            new_count = cursor.fetchone()[0]
            if new_count > 0:
                return True
            
            # 检查旧架构（如果存在translations表）
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='translations'
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    SELECT COUNT(*) FROM word_lemmas wl
                    WHERE LOWER(wl.lemma) = LOWER(?)
                """, (lemma,))
                
                old_count = cursor.fetchone()[0]
                return old_count > 0
            
            return False
            
        finally:
            conn.close()
    
    async def insert_word_to_database(self, lemma: str, estimated_pos: str = None) -> bool:
        """将单词插入数据库，使用LLM进行分析"""
        try:
            print(f"🔍 分析单词: {lemma}")
            
            # 使用LLM服务进行词汇消歧
            disambiguation = await self.llm_service.disambiguate_lemma(lemma)
            
            if not disambiguation or not disambiguation.get('senses'):
                print(f"   ❌ 无法分析词汇: {lemma}")
                self.stats['failed_words'] += 1
                return False
            
            # 取第一个（最可能的）词性
            primary_sense = disambiguation['senses'][0]
            upos = primary_sense.get('upos', 'OTHER')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # 插入word_lemmas
                cursor.execute("""
                    INSERT INTO word_lemmas (lemma, pos, cefr, notes, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    lemma,
                    upos.lower(),
                    'A1',  # 默认级别
                    f'Imported from DTZ PDF - estimated: {estimated_pos or "unknown"}',
                    datetime.now().isoformat()
                ))
                
                lemma_id = cursor.lastrowid
                
                # 插入lemma_senses
                cursor.execute("""
                    INSERT INTO lemma_senses 
                    (lemma_id, upos, xpos, gender, gloss_en, gloss_zh, confidence, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lemma_id,
                    upos,
                    primary_sense.get('xpos', 'OTHER'),
                    primary_sense.get('gender'),
                    primary_sense.get('gloss_en'),
                    primary_sense.get('gloss_zh'),
                    0.8,  # 中等置信度
                    'pdf_dtz_import'
                ))
                
                sense_id = cursor.lastrowid
                
                # 根据词性保存特定属性
                if upos == 'NOUN':
                    await self._save_noun_enhanced_data(cursor, sense_id, lemma)
                elif upos == 'VERB':
                    await self._save_verb_enhanced_data(cursor, sense_id, lemma)
                
                conn.commit()
                print(f"   ✅ 成功导入: {lemma} ({upos})")
                self.stats['new_words'] += 1
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"   ❌ 导入失败: {lemma} - {e}")
            self.stats['failed_words'] += 1
            return False
    
    async def _save_noun_enhanced_data(self, cursor, sense_id: int, lemma: str):
        """保存名词的增强数据"""
        try:
            noun_data = await self.llm_service.enrich_noun(lemma)
            if noun_data and noun_data.get('noun_props'):
                props = noun_data['noun_props']
                cursor.execute("""
                    INSERT INTO noun_props 
                    (sense_id, gen_sg, plural, declension_class, dative_plural_ends_n)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    sense_id,
                    props.get('gen_sg'),
                    props.get('plural'),
                    props.get('declension_class'),
                    props.get('dative_plural_ends_n', False)
                ))
                self.stats['enhanced_words'] += 1
        except Exception as e:
            print(f"     ⚠️ 名词增强失败: {e}")
    
    async def _save_verb_enhanced_data(self, cursor, sense_id: int, lemma: str):
        """保存动词的增强数据"""
        try:
            verb_data = await self.llm_service.enrich_verb(lemma)
            if verb_data:
                cursor.execute("""
                    INSERT INTO verb_props 
                    (sense_id, separable, prefix, aux, regularity, partizip_ii, reflexive, valency_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sense_id,
                    verb_data.get('separable', False),
                    verb_data.get('prefix'),
                    verb_data.get('aux'),
                    verb_data.get('regularity'),
                    verb_data.get('partizip_ii'),
                    verb_data.get('reflexive', False),
                    '{}' if not verb_data.get('valency') else str(verb_data.get('valency'))
                ))
                self.stats['enhanced_words'] += 1
        except Exception as e:
            print(f"     ⚠️ 动词增强失败: {e}")
    
    async def batch_import_words(self, words: List[str], estimated_pos: str = None, batch_size: int = 10):
        """批量导入单词"""
        total = len(words)
        print(f"📚 开始批量导入 {total} 个{estimated_pos or ''}单词...")
        
        for i in range(0, total, batch_size):
            batch = words[i:i + batch_size]
            print(f"\n📦 处理批次 {i//batch_size + 1} ({len(batch)} 个单词)")
            
            for word in batch:
                self.stats['total_words'] += 1
                
                # 检查是否已存在
                if self.word_exists_in_database(word):
                    print(f"⏩ '{word}' 已存在，跳过")
                    self.stats['existing_words'] += 1
                    continue
                
                # 插入新单词
                await self.insert_word_to_database(word, estimated_pos)
                
                # 稍作延迟，避免API限制
                await asyncio.sleep(0.5)
            
            # 批次间休息
            if i + batch_size < total:
                print("💤 批次完成，休息2秒...")
                await asyncio.sleep(2)
        
        self._print_final_stats()
    
    def _print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 PDF词汇导入完成！")
        print(f"=" * 50)
        print(f"总处理单词: {self.stats['total_words']}")
        print(f"已存在: {self.stats['existing_words']}")
        print(f"新导入: {self.stats['new_words']}")
        print(f"增强处理: {self.stats['enhanced_words']}")
        print(f"失败: {self.stats['failed_words']}")
        print(f"总用时: {elapsed}")

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从DTZ PDF词汇列表导入德语单词到数据库')
    parser.add_argument('pdf_file', help='DTZ PDF词汇列表文件')
    parser.add_argument('--batch-size', type=int, default=10, help='批次大小')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式（只提取，不导入）')
    parser.add_argument('--limit', type=int, help='限制处理的单词数量')
    parser.add_argument('--category', choices=['nouns', 'verbs', 'adjectives', 'all'], 
                       default='all', help='导入的词汇类别')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_file):
        print(f"❌ 文件不存在: {args.pdf_file}")
        return
    
    print("🚀 DTZ PDF词汇导入工具")
    print("=" * 50)
    
    # 1. 提取PDF文本
    print("📖 提取PDF文本...")
    extractor = PDFVocabularyExtractor()
    text = extractor.extract_text_from_pdf(args.pdf_file)
    
    if not text:
        print("❌ 无法提取PDF文本")
        return
    
    # 2. 使用AI提取德语单词
    print("🤖 使用AI智能提取德语单词...")
    words = await extractor.extract_german_words_with_ai(text)
    print(f"📊 AI提取到 {len(words)} 个德语单词")
    
    # 3. 使用AI分类单词
    categorized = await extractor.categorize_words_with_ai(words)
    
    print("\n📋 词汇分类统计:")
    for category, word_list in categorized.items():
        print(f"   {category}: {len(word_list)} 个")
    
    if args.dry_run:
        print("\n⚠️ 试运行模式 - 显示部分结果:")
        for category, word_list in categorized.items():
            if word_list:
                print(f"\n{category} (前10个):")
                for word in sorted(word_list)[:10]:
                    print(f"   - {word}")
        return
    
    # 4. 导入数据库
    importer = PDFDatabaseImporter()
    
    # 根据用户选择的类别进行导入
    if args.category == 'all':
        for category, word_list in categorized.items():
            if word_list:
                limited_words = word_list[:args.limit] if args.limit else word_list
                await importer.batch_import_words(
                    sorted(limited_words), 
                    category.rstrip('s'),  # "nouns" -> "noun"
                    args.batch_size
                )
    else:
        selected_category = args.category
        if selected_category in categorized and categorized[selected_category]:
            word_list = categorized[selected_category]
            limited_words = word_list[:args.limit] if args.limit else word_list
            await importer.batch_import_words(
                sorted(limited_words),
                selected_category.rstrip('s'),  # "nouns" -> "noun"
                args.batch_size
            )

if __name__ == "__main__":
    asyncio.run(main())
