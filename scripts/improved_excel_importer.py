"""
改进的Excel词汇导入器
基于实际Excel文件结构，支持自动补全缺失的语法形式
"""
import asyncio
import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.models.word import WordLemma, Translation, Example, WordForm
from app.services.openai_service import OpenAIService
import zipfile
import xml.etree.ElementTree as ET


class ImprovedExcelImporter:
    def __init__(self):
        self.db = SessionLocal()
        self.openai_service = OpenAIService()
        self.statistics = {
            'imported': 0,
            'skipped': 0,
            'enhanced': 0,
            'errors': 0
        }

    def parse_xlsx_simple(self, file_path):
        """简单解析XLSX文件"""
        
        words_data = []
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # 读取共享字符串
                shared_strings = []
                if 'xl/sharedStrings.xml' in zip_ref.namelist():
                    with zip_ref.open('xl/sharedStrings.xml') as f:
                        content = f.read().decode('utf-8')
                        root = ET.fromstring(content)
                        for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                            shared_strings.append(si.text if si.text else "")
                
                # 读取工作表数据
                if 'xl/worksheets/sheet1.xml' in zip_ref.namelist():
                    with zip_ref.open('xl/worksheets/sheet1.xml') as f:
                        content = f.read().decode('utf-8')
                        root = ET.fromstring(content)
                        
                        # 解析所有行
                        rows = []
                        for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                            row_data = []
                            for cell in row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                                value = ""
                                v_element = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                                if v_element is not None:
                                    if cell.get('t') == 's':
                                        try:
                                            string_index = int(v_element.text)
                                            if string_index < len(shared_strings):
                                                value = shared_strings[string_index]
                                        except (ValueError, IndexError):
                                            value = v_element.text if v_element.text else ""
                                    else:
                                        value = v_element.text if v_element.text else ""
                                row_data.append(value)
                            if row_data:  # 只添加非空行
                                rows.append(row_data)
                        
                        return rows
                        
        except Exception as e:
            print(f"❌ 解析Excel文件失败: {e}")
            return []

    def process_b1_file(self, file_path):
        """处理B1级别的Excel文件（标准格式）"""
        
        print(f"📚 处理B1文件: {os.path.basename(file_path)}")
        
        rows = self.parse_xlsx_simple(file_path)
        if not rows:
            return []
        
        # B1文件的列结构：
        # 0: German Word, 1: Article, 2: Noun Only, 3: Translation, 4: Example Sentence, 5: Classification, 6: Page Number
        
        words_data = []
        headers = rows[0] if rows else []
        print(f"检测到的标题: {headers}")
        
        for row in rows[1:]:  # 跳过标题行
            if len(row) >= 6:  # 确保有足够的列
                word_info = {
                    'german_word': row[0].strip() if row[0] else '',
                    'article': row[1].strip() if len(row) > 1 and row[1] else '',
                    'noun_only': row[2].strip() if len(row) > 2 and row[2] else '',
                    'translation': row[3].strip() if len(row) > 3 and row[3] else '',
                    'example_de': row[4].strip() if len(row) > 4 and row[4] else '',
                    'classification': row[5].strip() if len(row) > 5 and row[5] else '',
                    'pos': 'noun',  # B1文件主要是名词
                    'level': 'B1'
                }
                
                if word_info['german_word']:  # 只处理有德语词汇的行
                    words_data.append(word_info)
        
        print(f"从B1文件提取了 {len(words_data)} 个词汇")
        return words_data

    def determine_pos_from_classification(self, classification):
        """根据分类确定词性"""
        
        if not classification:
            return 'noun'  # 默认为名词
        
        classification_lower = classification.lower()
        
        # 动词标识
        if any(keyword in classification_lower for keyword in ['verb', 'action', '动词']):
            return 'verb'
        
        # 形容词标识
        if any(keyword in classification_lower for keyword in ['adjective', 'adj', 'quality', '形容词']):
            return 'adjective'
        
        # 副词标识
        if any(keyword in classification_lower for keyword in ['adverb', 'adv', '副词']):
            return 'adverb'
        
        # 其他都当作名词
        return 'noun'

    async def import_word_to_database(self, word_info):
        """将单词导入数据库"""
        
        german_word = word_info.get('german_word', '').strip()
        if not german_word:
            return False
        
        try:
            # 清理德语单词，提取lemma
            lemma = self._extract_lemma(german_word, word_info.get('article', ''))
            
            # 检查是否已存在
            existing = self.db.query(WordLemma).filter(
                WordLemma.lemma.ilike(lemma)
            ).first()
            
            if existing:
                print(f"⏩ '{lemma}' 已存在，跳过")
                self.statistics['skipped'] += 1
                return False
            
            # 确定词性
            pos = self.determine_pos_from_classification(word_info.get('classification', ''))
            
            # 创建词条
            word = WordLemma(
                lemma=lemma,
                pos=pos,
                cefr=word_info.get('level', 'B1'),
                notes=f"Imported from Excel - {word_info.get('classification', 'unknown')}"
            )
            
            self.db.add(word)
            self.db.commit()
            self.db.refresh(word)
            
            # 添加英文翻译
            translation_text = word_info.get('translation', '').strip()
            if translation_text:
                translation = Translation(
                    lemma_id=word.id,
                    lang_code="en",
                    text=translation_text,
                    source="excel_import"
                )
                self.db.add(translation)
            
            # 添加例句
            example_de = word_info.get('example_de', '').strip()
            if example_de:
                example = Example(
                    lemma_id=word.id,
                    de_text=example_de,
                    level=word_info.get('level', 'B1')
                )
                self.db.add(example)
            
            # 处理名词的冠词信息
            article = word_info.get('article', '').strip()
            if pos == 'noun' and article and article.lower() in ['der', 'die', 'das']:
                article_form = WordForm(
                    lemma_id=word.id,
                    form=f"{article} {lemma}",
                    feature_key="article",
                    feature_value=article
                )
                self.db.add(article_form)
                
                # 如果有"Noun Only"信息，也保存
                noun_only = word_info.get('noun_only', '').strip()
                if noun_only and noun_only != lemma:
                    expansion_form = WordForm(
                        lemma_id=word.id,
                        form=noun_only,
                        feature_key="expansion",
                        feature_value="full_form"
                    )
                    self.db.add(expansion_form)
            
            self.db.commit()
            
            # 使用OpenAI补全缺失信息（特别是动词和缺少中文翻译的词）
            enhanced = await self._enhance_with_openai(word, word_info)
            
            print(f"✅ 导入: {lemma} ({pos})" + (" [增强]" if enhanced else ""))
            self.statistics['imported'] += 1
            if enhanced:
                self.statistics['enhanced'] += 1
            
            return True
            
        except Exception as e:
            print(f"❌ 导入 '{german_word}' 失败: {e}")
            self.statistics['errors'] += 1
            self.db.rollback()
            return False

    def _extract_lemma(self, german_word, article):
        """提取词汇的lemma形式"""
        
        german_word = german_word.strip()
        
        # 如果词汇以冠词开头，去掉冠词
        for art in ['der ', 'die ', 'das ', 'Der ', 'Die ', 'Das ']:
            if german_word.startswith(art):
                return german_word[len(art):].strip()
        
        return german_word

    async def _enhance_with_openai(self, word: WordLemma, word_info: dict):
        """使用OpenAI增强词汇信息"""
        
        try:
            # 检查是否需要增强
            needs_chinese = not any(t.lang_code == 'zh' for t in word.translations)
            needs_verb_forms = word.pos == 'verb'
            
            if not (needs_chinese or needs_verb_forms):
                return False
            
            print(f"🔍 OpenAI增强: {word.lemma}")
            analysis = await self.openai_service.analyze_word(word.lemma)
            
            enhanced = False
            
            # 添加中文翻译
            if needs_chinese:
                translations_zh = analysis.get("translations_zh", [])
                for trans in translations_zh:
                    translation = Translation(
                        lemma_id=word.id,
                        lang_code="zh",
                        text=trans,
                        source="openai_enhancement"
                    )
                    self.db.add(translation)
                    enhanced = True
            
            # 添加动词变位
            if needs_verb_forms and analysis.get("tables"):
                tables = analysis["tables"]
                for tense, forms in tables.items():
                    if isinstance(forms, dict):
                        for person, form in forms.items():
                            if form and person not in ["aux", "partizip_ii"]:
                                word_form = WordForm(
                                    lemma_id=word.id,
                                    form=form,
                                    feature_key="tense",
                                    feature_value=f"{tense}_{person}"
                                )
                                self.db.add(word_form)
                                enhanced = True
            
            # 如果没有例句且OpenAI提供了例句，添加英文和中文翻译
            if not word.examples and analysis.get("example"):
                example_data = analysis["example"]
                if word.examples:  # 更新现有例句
                    existing_example = word.examples[0]
                    if not existing_example.en_text:
                        existing_example.en_text = example_data.get("en", "")
                    if not existing_example.zh_text:
                        existing_example.zh_text = example_data.get("zh", "")
                    enhanced = True
            
            if enhanced:
                self.db.commit()
            
            # API速率限制
            await asyncio.sleep(1)
            
            return enhanced
            
        except Exception as e:
            print(f"⚠️ OpenAI增强失败 '{word.lemma}': {e}")
            return False

    async def import_file(self, file_path, max_words=None):
        """导入单个文件"""
        
        level = "B1"  # 目前主要处理B1文件
        if "A1" in file_path:
            level = "A1"
        elif "A2" in file_path:
            level = "A2"
        
        print(f"\n📚 导入文件: {os.path.basename(file_path)} (级别: {level})")
        print("=" * 60)
        
        # 根据文件类型选择处理方法
        if "B1" in file_path:
            words_data = self.process_b1_file(file_path)
        else:
            print("⚠️ A1/A2文件格式暂未实现，跳过")
            return
        
        if not words_data:
            print("❌ 未找到可导入的词汇数据")
            return
        
        # 限制导入数量（用于测试）
        if max_words:
            words_data = words_data[:max_words]
            print(f"限制导入前 {max_words} 个词汇")
        
        print(f"准备导入 {len(words_data)} 个词汇...")
        
        # 批量导入
        for i, word_info in enumerate(words_data):
            print(f"\n处理 {i+1}/{len(words_data)}: {word_info.get('german_word', 'N/A')}")
            await self.import_word_to_database(word_info)
            
            # 每10个词汇休息一下
            if (i + 1) % 10 == 0:
                print(f"已处理 {i+1} 个词汇，休息2秒...")
                await asyncio.sleep(2)
        
        print(f"\n✅ 文件导入完成: {os.path.basename(file_path)}")

    async def import_all_files(self, max_words_per_file=None):
        """导入所有文件"""
        
        files_to_process = [
            "/mnt/e/LanguageLearning/german_vocabulary_B1_sample.xlsx"  # 先只处理B1文件
        ]
        
        print("🚀 开始批量导入Excel词汇文件")
        print("=" * 60)
        
        for file_path in files_to_process:
            if os.path.exists(file_path):
                await self.import_file(file_path, max_words_per_file)
            else:
                print(f"⚠️ 文件不存在: {file_path}")
        
        # 显示统计
        print(f"\n📊 导入统计:")
        print(f"   - 成功导入: {self.statistics['imported']}")
        print(f"   - 跳过已存在: {self.statistics['skipped']}")
        print(f"   - OpenAI增强: {self.statistics['enhanced']}")
        print(f"   - 错误: {self.statistics['errors']}")
        
        self.db.close()


async def main():
    """主函数"""
    
    importer = ImprovedExcelImporter()
    
    print("Excel词汇导入器")
    print("本次导入将处理B1级别的Excel文件")
    print("每个词汇都会尝试使用OpenAI补全中文翻译和动词变位")
    print()
    
    # 询问是否限制导入数量（用于测试）
    try:
        max_words = input("限制导入数量（回车跳过，数字限制）: ").strip()
        max_words = int(max_words) if max_words else None
    except ValueError:
        max_words = None
    
    if max_words:
        print(f"将限制每个文件导入前 {max_words} 个词汇")
    else:
        print("将导入所有词汇（可能需要较长时间和API费用）")
    
    print("\n开始导入...")
    await importer.import_all_files(max_words)
    
    print("\n🎉 导入完成！")


if __name__ == "__main__":
    asyncio.run(main())