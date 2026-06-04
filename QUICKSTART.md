# LM Studioでの実行方法 - クイックスタート

## 5分で開始

### 前提条件
- Python 3.8 以上がインストール済み
- LM Studio がダウンロード・インストール済み

### 準備（初回のみ）

```bash
# 1. このリポジトリを開く
cd plant-test

# 2. 依存パッケージをインストール
pip install -r requirements.txt

# 3. .env ファイルを作成/編集
echo LVM_SERVICE=lm_studio > .env
echo LM_STUDIO_API_BASE=http://localhost:1234/v1 >> .env
echo LM_STUDIO_MODEL=llava-llama-3-8b-v1_1 >> .env
```

### LM Studio の起動（毎回必要）

```bash
# 1. LM Studio を起動
# Windows/Mac: LM Studio アプリをダブルクリック
# Linux: ./LM-Studio-*.appimage

# 2. 左側「Local Server」を選択
# 3. モデルドロップダウンから「llava-1.6-7b-q4」を選択
# 4. 「Start Server」をクリック

# ターミナルに以下が表示される:
# LM Studio Local Server
# Server is running at: http://localhost:1234/v1
```

### 実行

```bash
# ターミナルで実行
python -m src analyze --plant-id myplant --species ガジュマル --diary

# 結果が表示される:
# ======================================================================
# 🌱 Plant Analysis Result
# ======================================================================
# Plant ID: myplant
# Overall Health: GOOD
# Leaf Condition: healthy
# Growth Stage: mature
# Confidence Score: 87.0%
#
# 📝 Observation Diary:
# ...
```

## よく使うコマンド

```bash
# 基本解析（日記なし）
python -m src analyze --plant-id plant1 --species ガジュマル --image photo.png

# JSON出力
python -m src analyze --plant-id plant1 --species ガジュマル --image photo.png --format json

# Markdown出力
python -m src analyze --plant-id plant1 --species ガジュマル --image photo.png --format markdown

# 解析済み植物一覧
python -m src list

# テスト実行
pytest tests/ -v
```

## トラブルシューティング

### エラー: "LM Studio connection failed"
→ LM Studio を起動して「Start Server」をクリック

### エラー: "Model not found"
→ モデル名を確認: `LM_STUDIO_MODEL=llava-1.6-7b-q4`

### エラー: "CUDA out of memory"
→ より小さいモデルを使用: `LM_STUDIO_MODEL=llava-1.6-7b-q4`

## 詳細ガイド
詳細は [LM_STUDIO_SETUP.md](./LM_STUDIO_SETUP.md) を参照してください。

---

🌱 Happy analyzing!
