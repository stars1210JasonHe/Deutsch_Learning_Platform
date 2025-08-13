"""
Excel词汇导入器 - 支持自动补全缺失的语法形式
从Excel文件导入词汇到数据库，并使用OpenAI自动补全缺失的动词变位等
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


class ExcelVocabularyImporter:
    def __init__(self):
        self.db = SessionLocal()
        self.openai_service = OpenAIService()
        self.statistics = {
            'imported': 0,
            'skipped': 0,
            'enhanced': 0,
            'errors': 0
        }

    def parse_xlsx_file(self, file_path):
        """解析XLSX文件，提取词汇数据"""
        
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
                                    # 检查是否是共享字符串引用
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
                            rows.append(row_data)
                        
                        # 处理数据（假设第一行是标题）
                        if len(rows) > 1:
                            headers = rows[0] if rows[0] else []
                            print(f"检测到的列标题: {headers}")
                            
                            # 映射常见的列名
                            column_mapping = self._map_columns(headers)
                            print(f"列映射: {column_mapping}")
                            
                            for row_data in rows[1:]:
                                if len(row_data) > 0 and any(cell.strip() for cell in row_data if cell):
                                    word_info = self._extract_word_info(row_data, column_mapping)
                                    if word_info and word_info.get('german_word'):
                                        words_data.append(word_info)
                
        except Exception as e:
            print(f"❌ 解析Excel文件失败: {e}")
        
        return words_data

    def _map_columns(self, headers):
        """映射列标题到标准字段名"""
        
        column_mapping = {}
        
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            
            # 德语词汇列
            if any(keyword in header_lower for keyword in ['german', 'deutsch', 'word', 'lemma', '词汇']):
                column_mapping['german_word'] = i
            
            # 冠词列
            elif any(keyword in header_lower for keyword in ['article', 'der/die/das', '冠词']):
                column_mapping['article'] = i
            
            # 翻译列
            elif any(keyword in header_lower for keyword in ['translation', 'english', 'meaning', '翻译', '意思']):
                column_mapping['translation'] = i
            
            # 例句列
            elif any(keyword in header_lower for keyword in ['example', 'sentence', '例句']):
                column_mapping['example'] = i
            
            # 词性/分类列
            elif any(keyword in header_lower for keyword in ['classification', 'pos', 'type', '词性', '分类']):
                column_mapping['classification'] = i
            
            # 只有名词列（用于判断是否为名词）
            elif any(keyword in header_lower for keyword in ['noun only', 'noun', '名词']):
                column_mapping['noun_only'] = i
        
        return column_mapping

    def _extract_word_info(self, row_data, column_mapping):
        """从行数据中提取词汇信息"""
        
        word_info = {}
        
        # 获取基本信息
        if 'german_word' in column_mapping:
            german_word = row_data[column_mapping['german_word']].strip()
            word_info['german_word'] = german_word
        
        if 'article' in column_mapping and column_mapping['article'] < len(row_data):
            article = row_data[column_mapping['article']].strip()
            word_info['article'] = article
        
        if 'translation' in column_mapping and column_mapping['translation'] < len(row_data):
            translation = row_data[column_mapping['translation']].strip()
            word_info['translation'] = translation
        
        if 'example' in column_mapping and column_mapping['example'] < len(row_data):
            example = row_data[column_mapping['example']].strip()
            word_info['example_de'] = example
        
        if 'classification' in column_mapping and column_mapping['classification'] < len(row_data):
            classification = row_data[column_mapping['classification']].strip()
            word_info['classification'] = classification
        
        # 判断词性
        word_info['pos'] = self._determine_pos(word_info)
        
        return word_info

    def _determine_pos(self, word_info):
        """根据可用信息判断词性"""
        
        german_word = word_info.get('german_word', '')
        article = word_info.get('article', '')
        classification = word_info.get('classification', '')
        
        # 如果有冠词，很可能是名词
        if article and article.lower() in ['der', 'die', 'das']:
            return 'noun'
        
        # 根据分类判断
        if classification:
            classification_lower = classification.lower()
            if any(keyword in classification_lower for keyword in ['noun', '名词']):
                return 'noun'
            elif any(keyword in classification_lower for keyword in ['verb', '动词']):
                return 'verb'
            elif any(keyword in classification_lower for keyword in ['adj', 'adjective', '形容词']):
                return 'adjective'
        
        # 根据德语单词特征判断
        if german_word:
            # 德语名词通常首字母大写
            if german_word[0].isupper() and not german_word.startswith(('Der ', 'Die ', 'Das ')):
                return 'noun'
            
            # 常见动词结尾
            if german_word.endswith(('en', 'ern', 'eln')):
                return 'verb'
        
        return 'unknown'

    async def import_word_to_database(self, word_info, level):
        """将单词导入数据库，并自动补全缺失的形式"""
        
        german_word = word_info.get('german_word')
        if not german_word:
            return False
        
        try:
            # 清理德语单词（去除可能的冠词前缀）
            lemma = self._clean_german_word(german_word)
            
            # 检查是否已存在
            existing = self.db.query(WordLemma).filter(
                WordLemma.lemma.ilike(lemma)
            ).first()
            
            if existing:
                print(f"⏩ '{lemma}' 已存在，跳过")
                self.statistics['skipped'] += 1
                return False
            
            # 创建基本词条
            word = WordLemma(
                lemma=lemma,
                pos=word_info.get('pos', 'unknown'),
                cefr=level,
                notes=f"Imported from Excel ({level})"
            )
            
            self.db.add(word)
            self.db.commit()
            self.db.refresh(word)
            
            # 添加已有的翻译
            translation_text = word_info.get('translation')
            if translation_text:
                # 假设翻译是英文，后续可以改进语言检测
                translation = Translation(
                    lemma_id=word.id,
                    lang_code="en",
                    text=translation_text,
                    source="excel_import"
                )
                self.db.add(translation)
            
            # 添加例句
            example_de = word_info.get('example_de')
            if example_de:
                example = Example(
                    lemma_id=word.id,
                    de_text=example_de,
                    level=level
                )
                self.db.add(example)
            
            # 处理名词特殊信息
            if word_info.get('pos') == 'noun' and word_info.get('article'):
                article_form = WordForm(
                    lemma_id=word.id,
                    form=f"{word_info['article']} {lemma}",
                    feature_key="article",
                    feature_value=word_info['article']
                )
                self.db.add(article_form)
            
            self.db.commit()
            
            # 使用OpenAI补全缺失的信息
            enhanced = await self._enhance_word_with_openai(word, word_info)
            
            print(f"✅ 导入: {lemma} ({word_info.get('pos', 'unknown')})" + 
                  (" [增强]" if enhanced else ""))
            
            self.statistics['imported'] += 1
            if enhanced:
                self.statistics['enhanced'] += 1
            
            return True
            
        except Exception as e:
            print(f"❌ 导入 '{german_word}' 失败: {e}")
            self.statistics['errors'] += 1
            self.db.rollback()
            return False

    async def _enhance_word_with_openai(self, word: WordLemma, word_info: dict):
        """使用OpenAI补全缺失的词汇信息"""
        
        try:
            # 只对动词和需要补充信息的词汇调用OpenAI
            needs_enhancement = (
                word.pos == 'verb' or  # 动词需要变位表
                not word.translations or  # 缺少翻译
                not word.examples  # 缺少例句
            )
            
            if not needs_enhancement:
                return False
            
            print(f"🔍 使用OpenAI增强词汇: {word.lemma}")
            analysis = await self.openai_service.analyze_word(word.lemma)
            
            enhanced = False
            
            # 补充翻译
            if not word.translations:
                translations_en = analysis.get("translations_en", [])
                translations_zh = analysis.get("translations_zh", [])
                
                for trans in translations_en:
                    translation = Translation(
                        lemma_id=word.id,
                        lang_code="en",
                        text=trans,
                        source="openai_enhancement"
                    )
                    self.db.add(translation)
                    enhanced = True
                
                for trans in translations_zh:
                    translation = Translation(
                        lemma_id=word.id,
                        lang_code="zh",
                        text=trans,
                        source="openai_enhancement"
                    )
                    self.db.add(translation)
                    enhanced = True
            
            # 补充动词变位表
            if word.pos == 'verb' and analysis.get("tables"):
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
            
            # 补充例句
            if not word.examples and analysis.get("example"):
                example_data = analysis["example"]
                example = Example(
                    lemma_id=word.id,
                    de_text=example_data.get("de", ""),
                    en_text=example_data.get("en", ""),
                    zh_text=example_data.get("zh", ""),
                    level=word.cefr or "A1"
                )
                self.db.add(example)
                enhanced = True
            
            if enhanced:
                self.db.commit()
            
            # 限制API调用频率
            await asyncio.sleep(1)
            
            return enhanced
            
        except Exception as e:
            print(f"⚠️ OpenAI增强失败: {e}")
            return False

    def _clean_german_word(self, word):
        """清理德语单词，移除冠词前缀等"""
        
        word = word.strip()
        
        # 移除冠词
        for article in ['der ', 'die ', 'das ', 'Der ', 'Die ', 'Das ']:
            if word.startswith(article):
                return word[len(article):].strip()
        
        return word

    async def import_excel_file(self, file_path):
        """导入单个Excel文件"""
        
        # 确定级别
        level = "A1"
        if "A2" in file_path:
            level = "A2"
        elif "B1" in file_path:
            level = "B1"
        
        print(f"\n📚 导入Excel文件: {os.path.basename(file_path)} (级别: {level})")
        print("=" * 60)
        
        # 解析Excel文件
        words_data = self.parse_xlsx_file(file_path)
        
        if not words_data:
            print("❌ 未找到词汇数据")
            return
        
        print(f"📊 找到 {len(words_data)} 个词汇条目")
        
        # 导入词汇
        for i, word_info in enumerate(words_data):
            print(f"处理 {i+1}/{len(words_data)}: {word_info.get('german_word', 'N/A')}")
            await self.import_word_to_database(word_info, level)
            
            # 每处理10个词汇休息一下，避免API限制
            if (i + 1) % 10 == 0:
                print(f"已处理 {i+1} 个词汇，休息2秒...")
                await asyncio.sleep(2)
        
        print(f"\n✅ {os.path.basename(file_path)} 导入完成")

    async def import_all_excel_files(self):
        """导入所有Excel文件"""
        
        excel_files = [
            "/mnt/e/LanguageLearning/german_vocabulary_A1_sample.xlsx",
            "/mnt/e/LanguageLearning/german_vocabulary_A2_sample.xlsx", 
            "/mnt/e/LanguageLearning/german_vocabulary_B1_sample.xlsx"
        ]
        
        print("🚀 开始批量导入Excel词汇文件")
        print("=" * 60)
        
        for file_path in excel_files:
            if os.path.exists(file_path):
                await self.import_excel_file(file_path)
            else:
                print(f"⚠️ 文件不存在: {file_path}")
        
        # 显示最终统计
        print(f"\n📊 导入统计:")
        print(f"   - 成功导入: {self.statistics['imported']}")
        print(f"   - 跳过已存在: {self.statistics['skipped']}")
        print(f"   - OpenAI增强: {self.statistics['enhanced']}")
        print(f"   - 错误: {self.statistics['errors']}")
        
        self.db.close()

    def show_preview(self, file_path, limit=5):
        """预览Excel文件内容"""
        
        print(f"\n👀 预览文件: {os.path.basename(file_path)}")
        print("=" * 40)
        
        words_data = self.parse_xlsx_file(file_path)
        
        for i, word_info in enumerate(words_data[:limit]):
            print(f"\n词汇 {i+1}:")
            for key, value in word_info.items():
                print(f"  {key}: {value}")


async def main():
    """主函数"""
    
    if len(sys.argv) < 2:
        print("Excel词汇导入器使用方法:")
        print("  python excel_vocabulary_importer.py preview      # 预览所有文件")
        print("  python excel_vocabulary_importer.py import       # 导入所有文件")
        print("  python excel_vocabulary_importer.py import A1    # 只导入A1文件")
        return
    
    importer = ExcelVocabularyImporter()
    command = sys.argv[1]
    
    if command == "preview":
        excel_files = [
            "/mnt/e/LanguageLearning/german_vocabulary_A1_sample.xlsx",
            "/mnt/e/LanguageLearning/german_vocabulary_A2_sample.xlsx", 
            "/mnt/e/LanguageLearning/german_vocabulary_B1_sample.xlsx"
        ]
        
        for file_path in excel_files:
            if os.path.exists(file_path):
                importer.show_preview(file_path)
                
    elif command == "import":
        if len(sys.argv) > 2:
            level = sys.argv[2].upper()
            file_path = f"/mnt/e/LanguageLearning/german_vocabulary_{level}_sample.xlsx"
            if os.path.exists(file_path):
                await importer.import_excel_file(file_path)
            else:
                print(f"❌ 文件不存在: {file_path}")
        else:
            await importer.import_all_excel_files()
    
    else:
        print("❌ 无效的命令")


if __name__ == "__main__":
    asyncio.run(main())