import csv
import json

input_file = "ecdict.csv"      # 原始詞庫檔
output_file = "ecdict.json"    # 轉換後輸出檔

mapping = {}

with open(input_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # ECDICT 有時會在欄位值前後帶引號
        word = row["word"].strip().lower().strip("'").strip('"')
        translation = row.get("translation", "").strip()

        # 若 translation 欄位空，則跳過
        if not word or not translation:
            continue

        # 清理換行符與多餘空白
        translation = translation.replace("\n", "；").replace("\r", "").strip()
        if translation.endswith("；"):
            translation = translation[:-1]

        mapping[word] = translation

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"轉換完成，共 {len(mapping)} 條詞彙，輸出至 {output_file}")
