# Plant Image Analysis

ガジュマル画像を **YOLO** で解析し、**LLM** で観察日記を生成します。

## セットアップ

`ash
pip install -r requirements.txt
cp .env.example .env
`

## 環境変数（.env）

| 変数 | 説明 | デフォルト |
|------|------|--------|
| LVM_SERVICE | mock / yolo_hybrid / lm_studio | mock |
| LM_STUDIO_API_BASE | LM Studio エンドポイント | http://localhost:1234/v1 |
| LM_STUDIO_MODEL | ビジョンモデル名 | llava-llama-3-8b-v1_1 |
| LLM_MODEL | テキスト生成モデル名（日記用） | mistral-7b-instruct |
| YOLO_MODEL | YOLO モデルファイル | yolov8s-seg.pt |

## LM Studio 起動

1. LM Studio を起動
2. 左メニュー「Local Server」を選択
3. ビジョンモデル（例: llava-llama-3-8b-v1_1）を選択
4. 「Start Server」をクリック → http://localhost:1234 で起動

## 実行方法

### 推奨: image/ ディレクトリのペア画像を自動解析

image/ に xxxx_1.jpg と xxxx_2.jpg のような連番ペアを置きます。  
番号が小さいほうを古い画像として差分解析します。

`
image/
  plant_1.jpg   ← 古い画像
  plant_2.jpg   ← 新しい画像
`

`ash
# .env で LVM_SERVICE=yolo_hybrid を設定してから実行
python -m src scan --plant-id myplant --species ガジュマル --diary
`

### 1枚の画像を解析

`ash
python -m src analyze --plant-id myplant --species ガジュマル --image image/plant.jpg --diary
`

### 2枚を直接指定して差分解析

`ash
python -m src diff \
  --plant-id myplant --species ガジュマル \
  --old-image image/plant_1.jpg --new-image image/plant_2.jpg \
  --diary
`

### 解析済み植物の一覧

`ash
python -m src list
`

### 出力形式（--format）

| オプション | 説明 |
|-----------|------|
| 	able | 見やすい表形式（デフォルト） |
| json | JSON 出力 |
| markdown | Markdown 出力 |

## テスト

`ash
python -m pytest tests/
`
