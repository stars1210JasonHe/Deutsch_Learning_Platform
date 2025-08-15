# 德语词库补全与在线查词增强规范（给 Claude Code，用 OpenAI 模型运行）

**日期：** 2025-08-13  
**背景：** 当前系统已实现 *先查本地数据库*，未命中再用 **OpenAI** 模型回退查询；但**已命中的词条信息不完整**（例如缺少词性细分、名词性别/复数、动词全人称变位、Präteritum/Perfekt、可分前缀、助动词等）。本规范要求：**批量回填现有词条**；以及在**在线查词时对缺字段进行即时补全并落库**。

**受众：** Claude Code（用于生成迁移脚本、回填脚本、后端服务代码与最小前端改动）。

---

## 0) 现有数据库快照（自动检测）
**表：** exam_attempts, exam_questions, exam_responses, exam_sections, examples, exams, learning_sessions, search_cache, search_history, srs_cards, translations, user_progress, users, word_forms, word_lemmas, word_list_items, word_lists

**行数统计：** {"exam_attempts": 4, "exam_questions": 44, "exam_responses": 5, "exam_sections": 7, "examples": 1814, "exams": 5, "learning_sessions": 2, "search_cache": 3, "search_history": 107, "srs_cards": 1, "translations": 2141, "user_progress": 1, "users": 8, "word_forms": 159, "word_lemmas": 1814, "word_list_items": 0, "word_lists": 0}

**关键表结构预览（如存在）：**
- **word_lemmas**: [(0, 'id', 'INTEGER', 1, None, 1), (1, 'lemma', 'VARCHAR', 1, None, 0), (2, 'pos', 'VARCHAR', 0, None, 0), (3, 'cefr', 'VARCHAR', 0, None, 0), (4, 'ipa', 'VARCHAR', 0, None, 0), (5, 'frequency', 'INTEGER', 0, None, 0), (6, 'notes', 'TEXT', 0, None, 0), (7, 'created_at', 'DATETIME', 0, 'CURRENT_TIMESTAMP', 0)]
- **word_forms**: [(0, 'id', 'INTEGER', 1, None, 1), (1, 'lemma_id', 'INTEGER', 0, None, 0), (2, 'form', 'VARCHAR', 0, None, 0), (3, 'feature_key', 'VARCHAR', 0, None, 0), (4, 'feature_value', 'VARCHAR', 0, None, 0)]
- **translations**: [(0, 'id', 'INTEGER', 1, None, 1), (1, 'lemma_id', 'INTEGER', 0, None, 0), (2, 'lang_code', 'VARCHAR', 0, None, 0), (3, 'text', 'TEXT', 0, None, 0), (4, 'source', 'VARCHAR', 0, None, 0)]
- **examples**: [(0, 'id', 'INTEGER', 1, None, 1), (1, 'lemma_id', 'INTEGER', 0, None, 0), (2, 'de_text', 'TEXT', 1, None, 0), (3, 'en_text', 'TEXT', 0, None, 0), (4, 'zh_text', 'TEXT', 0, None, 0), (5, 'level', 'VARCHAR', 0, None, 0)]

**样本词条：**

|   id | lemma    | pos       | notes                                         |
|-----:|:---------|:----------|:----------------------------------------------|
|    1 | sein     | verb      | Most important German verb - 'to be'          |
|    2 | haben    | verb      | Second most important German verb - 'to have' |
|    3 | Tisch    | noun      | article:der                                   |
|    4 | gehen    | verb      | Seed data - verb                              |
|    5 | Haus     | noun      | article:das                                   |
|    6 | Wasser   | noun      | article:das                                   |
|    7 | gut      | adjective | Seed data - adjective                         |
|    8 | groß     | adjective | Seed data - adjective                         |
|    9 | arbeiten | verb      | Seed data - verb                              |
|   10 | Zeit     | noun      | article:die                                   |

---

## 1) 目标（用户可见行为与数据完备定义）
查询一个德语词：
1. **词性**：展示**所有**可能词性（NOUN/VERB/ADJ/ADV/…），并按词性分组。
2. **名词**：必须有 **性别（der/die/das）**、**复数**、**属格单数（Gen.Sg.）**，必要时注明 **弱变化 n-名词**、**与格复数加 -n** 等。
3. **动词**：展示 **Präsens & Präteritum 全人称**；**Perfekt**（助动词 + Partizip II）；标注 **可分/不可分**、**前缀**、**助动词 haben/sein**、**强/弱/混合变化**、是否 **反身**、常见 **支配格/介词**。
4. **双语释义与例句**：每个词性/义项至少 1 条 **中文 + 英文释义**，以及 1 条 **DE + EN + ZH 例句**。
5. **同形异义**：如 *Bank/See/Joghurt/Leiter* 必须拆分为不同 **sense** 并可切换。

---

## 2) 数据库迁移（保持向后兼容，不破坏式）
> 在现有基础上新增下列结构，旧接口可通过视图维持：

```sql
-- 2.1 义项层（支持一词多义/多词性）
CREATE TABLE IF NOT EXISTS lemma_senses (
  id INTEGER PRIMARY KEY,
  lemma_id INTEGER NOT NULL REFERENCES word_lemmas(id) ON DELETE CASCADE,
  upos TEXT,
  xpos TEXT,
  gender TEXT,
  sense_label TEXT,
  gloss_en TEXT,
  gloss_zh TEXT,
  notes TEXT,
  confidence REAL,
  source TEXT DEFAULT 'backfill',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 名词/动词属性
CREATE TABLE IF NOT EXISTS noun_props (
  sense_id INTEGER PRIMARY KEY REFERENCES lemma_senses(id) ON DELETE CASCADE,
  gen_sg TEXT,
  plural TEXT,
  declension_class TEXT,
  dative_plural_ends_n INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS verb_props (
  sense_id INTEGER PRIMARY KEY REFERENCES lemma_senses(id) ON DELETE CASCADE,
  separable INTEGER DEFAULT 0,
  prefix TEXT,
  aux TEXT,
  regularity TEXT,
  partizip_ii TEXT,
  reflexive INTEGER DEFAULT 0,
  valency_json TEXT
);

-- 2.3 统一形态存储（保留旧 word_forms；新增标准化 forms_unimorph）
CREATE TABLE IF NOT EXISTS forms_unimorph (
  id INTEGER PRIMARY KEY,
  sense_id INTEGER NOT NULL REFERENCES lemma_senses(id) ON DELETE CASCADE,
  form TEXT NOT NULL,
  features_json TEXT NOT NULL,
  UNIQUE (sense_id, form, features_json)
);

-- 2.4 释义/例句增加 sense 维度
ALTER TABLE translations ADD COLUMN sense_id INTEGER REFERENCES lemma_senses(id);
ALTER TABLE examples ADD COLUMN sense_id INTEGER REFERENCES lemma_senses(id);

-- 2.5 兼容视图（可选）
CREATE VIEW IF NOT EXISTS v_lemma_primary AS
SELECT wl.id AS lemma_id, wl.lemma, wl.pos, wl.cefr, wl.ipa, wl.frequency,
       ls.id AS sense_id, ls.upos, ls.xpos, ls.gender, ls.gloss_en, ls.gloss_zh
FROM word_lemmas wl
LEFT JOIN lemma_senses ls ON ls.lemma_id = wl.id
GROUP BY wl.id;
```

---

## 3) 两条线并行：**离线回填** + **在线查词时补洞**
### 3.1 离线回填（Batch Backfill）
1. 备份数据库 → 执行 §2 迁移。
2. 按 `word_lemmas` 逐条创建/关联 `lemma_senses`（若已有则跳过），**同形异义**用多条 sense。
3. 根据 `pos`：
   - **名词**：补 `gender / plural / gen_sg / declension_class / dative_plural_ends_n`；生成 **Sg/Pl × Nom/Acc/Dat/Gen** 到 `forms_unimorph`。
   - **动词**：补 `separable/prefix / aux / regularity / partizip_ii / reflexive / valency_json`；生成 **Präsens & Präteritum 全人称**到 `forms_unimorph`；`Perfekt` 保存为 `aux + partizip_ii`（在 `verb_props`）。
4. 每个 sense 至少写入 1 条 **gloss_en/gloss_zh** 与 **DE+EN+ZH 例句**；记录 `source='openai'` 与 `confidence`。
5. 幂等：以唯一键 `(sense_id, form, features_json)`、文本去重确保多次运行不重复插入。

### 3.2 在线补洞（Runtime Enrichment）
当查到 **已有词条**但字段不完整时：
1. 后端 `lookup_service` 计算**字段完备度**（见 §6）。
2. 若存在缺口（例如名词缺 `plural`，动词缺 `präteritum`），**调用 OpenAI** 的对应 Prompt 获取**严格 JSON** 结果。
3. 校验/规范化后**落库更新**（仅补空字段，不覆盖人工字段），返回给前端。
4. 对低置信度（如 `<0.8`）的写入加入**复核队列**（`review_tasks` 可选表）。

---

## 4) OpenAI 提示词（严格 JSON 输出）
> 统一要求：**只输出 JSON**。字段不确定填 `null`；同时返回 `rationale`（简短英文）便于日志审计。

### 4.1 名词补全 Prompt（enrich_noun）
**System**: You are a precise German morphology and lexicon engine. Output strict JSON per schema.
**User (example)**:
```json
{
  "task":"enrich_noun",
  "lemma":"Tisch",
  "context":{"notes":"existing: der"},
  "want_examples":true
}
```
**Return JSON**:
```json
{
  "upos":"NOUN",
  "xpos":"NN",
  "gender":"masc",
  "noun_props":{"gen_sg":"Tisches","plural":"Tische","declension_class":"strong","dative_plural_ends_n":false},
  "gloss_en":"table; desk",
  "gloss_zh":"桌子；台子",
  "example":{"de":"Der Tisch ist neu.","en":"The table is new.","zh":"这张桌子是新的。"},
  "forms":[
    {"form":"Tisch","features":{"POS":"NOUN","Number":"Sing","Case":"Nom"}},
    {"form":"Tisches","features":{"POS":"NOUN","Number":"Sing","Case":"Gen"}},
    {"form":"Tische","features":{"POS":"NOUN","Number":"Plur","Case":"Nom"}},
    {"form":"Tischen","features":{"POS":"NOUN","Number":"Plur","Case":"Dat"}}
  ],
  "rationale":"Monosyllabic masculine nouns tend to take -es in genitive singular."
}
```

### 4.2 动词补全 Prompt（enrich_verb）
**System**: You are a precise German verb morphology engine. Output strict JSON per schema.
**User (example)**:
```json
{"task":"enrich_verb","lemma":"aufstehen"}
```
**Return JSON**:
```json
{
  "upos":"VERB",
  "xpos":"VVINF",
  "separable":true,
  "prefix":"auf",
  "aux":"sein",
  "regularity":"strong",
  "partizip_ii":"aufgestanden",
  "tables":{
    "praesens":{"ich":"stehe auf","du":"stehst auf","er_sie_es":"steht auf","wir":"stehen auf","ihr":"steht auf","sie_Sie":"stehen auf"},
    "praeteritum":{"ich":"stand auf","du":"standest auf","er_sie_es":"stand auf","wir":"standen auf","ihr":"standet auf","sie_Sie":"standen auf"}
  },
  "gloss_en":"to get up; to stand up",
  "gloss_zh":"起床；站起",
  "example":{"de":"Ich stehe um sieben auf.","en":"I get up at seven.","zh":"我七点起床。"},
  "valency":{"cases":[],"preps":[]},
  "rationale":"Change-of-state verbs typically select 'sein' as auxiliary."
}
```

### 4.3 同形词性判定 Prompt（disambiguate）
**User**:
```json
{"task":"disambiguate","lemma":"Leiter"}
```
**Return JSON**:
```json
{
  "senses":[
    {"upos":"NOUN","xpos":"NN","gender":"masc","gloss_en":"leader","gloss_zh":"负责人"},
    {"upos":"NOUN","xpos":"NN","gender":"fem","gloss_en":"ladder","gloss_zh":"梯子"}
  ]
}
```

---

## 5) 服务改造与代码骨架（Python/FastAPI/SQLAlchemy）
### 5.1 LLM 适配器接口（你已在用 OpenAI，以下为占位接口）
```python
class LLMClient:
    async def json(self, task: str, payload: dict) -> dict:
        """Call OpenAI model and return strict JSON. Must validate & retry on JSON errors."""
        ...
```

### 5.2 查词服务（含在线补洞）
```python
async def lookup(lemma: str) -> dict:
    entry = await repo.get_lemma_full(lemma)
    if not entry:
        # 你已有：直接用 OpenAI 回退生成新条目 → 落库 → 返回
        return await create_via_llm(lemma)
    # 有条目但不完整 → 逐词性检测缺口
    gaps = completeness(entry)  # 见 §6
    if gaps.need_noun_enrich:
        data = await llm.json("enrich_noun", {"lemma": lemma})
        await repo.merge_noun(entry.sense_id, data)
    if gaps.need_verb_enrich:
        data = await llm.json("enrich_verb", {"lemma": lemma})
        await repo.merge_verb(entry.sense_id, data)
    return await repo.get_lemma_full(lemma)
```

### 5.3 回填脚本（Batch）
```python
# scripts/backfill.py
for lem in repo.iter_lemmas(limit=args.limit, offset=args.offset):
    senses = repo.ensure_senses(lem)
    for s in senses:
        if s.upos == "NOUN" and missing_noun_fields(s):
            data = llm.json("enrich_noun", {"lemma": lem.lemma})
            repo.merge_noun(s.id, data)
        if s.upos == "VERB" and missing_verb_fields(s):
            data = llm.json("enrich_verb", {"lemma": lem.lemma})
            repo.merge_verb(s.id, data)
```

---

## 6) 字段完备度与落库策略
**名词**：需要 `gender / plural / gen_sg`；形态表至少含 Sg/Pl × Nom/Acc/Dat/Gen。

**动词**：需要 `aux / partizip_ii / praesens(6人称) / praeteritum(6人称)`；若可分，需 `separable=true` 与 `prefix`。

**落库策略**：
- 仅补空字段；不覆盖人工确认的数据（可通过 `source`/`confidence` 判断）。
- `forms_unimorph` 去重键：`(sense_id, form, features_json)`。
- 低置信度（<0.8）进入 `review_tasks`（可选）与后台复核界面。

---

## 7) 前端最小改动
1. 词性 chips + 性别 badge（der/die/das）。
2. 动词时态切换（Präsens/Präteritum/Perfekt）；名词变格表（Sg/Pl × 4 格）。
3. 同形异义 sense tab 切换；例句与释义随 sense 变更。

---

## 8) 测试与验收
- 样例 **Tisch**：der；Plural=Tische；Gen.Sg.=Tisches/Tischs；例句齐全（DE/EN/ZH）。
- **aufstehen**：separable；aux=sein；Partizip II=aufgestanden；Präsens/Präteritum 六人称齐全。
- **Leiter**：两个 sense（阳性“负责人” vs 阴性“梯子”），复数不同（Leiter vs Leitern）。

---

## 9) 一次性指令（粘贴给 Claude Code 执行）
```
You are Claude Code working on a Python FastAPI + SQLite project that uses OpenAI models at runtime.
Goal: Backfill missing fields for existing German lexicon entries and enhance runtime lookup to auto-enrich incomplete entries using OpenAI.

Tasks:
1) Apply non-destructive migrations in §2.
2) Implement a batch backfill script per §3.1, using the strict JSON prompts in §4.
3) Modify lookup service per §5.2 to detect gaps (§6) and call OpenAI to fill, then persist.
4) Add minimal frontend changes in §7.
5) Provide unit tests & a README for running backfill and reviewing low-confidence items.

Constraints:
- Always backup DB before migrations.
- Idempotent writes; do not overwrite human-reviewed data.
- Strict JSON only; validate and retry on parse errors.
- Log counts, failures, and token usage.
```

---

*说明：运行时调用的确使用 OpenAI 模型；Claude 仅用于写代码与脚本。*
