# Vocab System Backend

本專案為一個輕量化的後端服務，用於英語文章解析與字彙管理。
後端以 Flask 撰寫，所有資料皆以 JSON 檔形式保存，不需要資料庫。

##功能概要

- 解析文章並抽取單字
- 管理使用者字彙庫（words.json）
- 記錄單字出現頻率（seen_words.json）
- 儲存與讀取文章（articles/*.json）
- 可選：整合 n8n workflow，自動獲取文章與翻譯
- 完全無狀態（除了 JSON 檔）

## 主要 API
### 文章解析
```
POST /api/parse
```

### 字彙 CRUD
```
GET    /api/words
POST   /api/words
GET    /api/words/<word>
DELETE /api/words/<word>
```
### 文章儲存
```
POST /api/articles/save
GET  /api/articles/list
GET  /api/articles/load/<filename>
```
### n8n 整合（可選）
```
POST /api/trigger
GET  /api/job/<job_id>
POST /api/n8n_callback
```
### 資料格式
#### 字彙資料
```
{
  "word": "example",
  "definition": "示例",
  "count": 1,
  "reviewed": 0,
  "added_by": "manual"
}
```
#### 單字解析結果
```
{
  "word": "example",
  "definition": "示例"
}
```
本地執行方式
`python app.py`


服務啟動於：

`http://127.0.0.1:5000`


無需額外資料庫或外部服務即可運作。

## 備註

- 系統以 JSON 檔為核心資料存放方式
- 無登入／權限系統，適用於個人使用或小型工具
- n8n 為可選模組，後端本身可獨立運作
- 適合作為輕量化語言學習工具的後端服務
- 這個人很懶，不用資料庫就算了，連文件都要用LLM寫

## 授權
MIT License.