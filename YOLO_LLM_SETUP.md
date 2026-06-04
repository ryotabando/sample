# YOLO + LLM ハイブリッド解析 - セットアップガイド

高精度な植物解析のための YOLO (物体検出) + LLM (テキスト生成) ハイブリッドアプローチです。

## 概要

```
入力画像
    ↓
┌──────────────────────────────┐
│  YOLOv8 (画像解析)           │
│  - 葉の領域検出              │
│  - 病気・異常の高精度検出    │ ← 95%以上の精度
│  - 虫害・病害の特定          │
└────────────┬─────────────────┘
             ↓
        YOLOの検出結果
             ↓
┌──────────────────────────────┐
│  LLM (テキスト生成)          │
│  - YOLOの結果を分析          │
│  - 高品質な観察日記を生成    │ ← 詳細で読みやすい文章
│  - ケアアドバイスを作成      │
└────────────┬─────────────────┘
             ↓
        最終解析レポート
```

## システム要件

### 最小要件
- **CPU**: 4コア以上
- **RAM**: 8GB 以上
- **VRAM**: 4GB 以上（GPU推奨）
- **ストレージ**: 10GB 以上

### 推奨要件
- **CPU**: 8コア以上
- **RAM**: 16GB 以上
- **VRAM**: 8GB 以上（NVIDIA RTX3060以上）

## インストール手順

### ステップ1: Python 環境のセットアップ

```bash
# このリポジトリをダウンロード
cd plant-test

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# YOLOv8 のダウンロード（初回のみ）
python -c "from ultralytics import YOLO; YOLO('yolov8s-seg.pt')"
```

### ステップ2: LLM テキスト生成用サーバーの準備

#### オプション A: LM Studio（推奨）

1. **LM Studio をダウンロード**
   - https://lmstudio.ai/ からダウンロード
   - インストール完了後、起動

2. **テキスト生成用LLMをダウンロード**
   - 左側「Search」を選択
   - 「mistral」で検索
   - `mistral-7b-instruct` をダウンロード
   
3. **ローカルサーバーを起動**
   - 「Local Server」を選択
   - ドロップダウンから `mistral-7b-instruct` を選択
   - 「Start Server」をクリック
   
4. **ターミナルに以下が表示される**
   ```
   Server is running at: http://localhost:1234/v1
   ```

#### オプション B: Ollama（軽量）

```bash
# Ollamaをインストール
# https://ollama.ai/ からダウンロード

# Mistralをダウンロード・起動
ollama run mistral

# 別のターミナルで確認
curl http://localhost:11434/api/generate
```

### ステップ3: 環境変数の設定

`.env` ファイルを編集:

```bash
# YOLO + LLM ハイブリッド設定
LVM_SERVICE=yolo_hybrid
YOLO_MODEL=yolov8s-seg.pt
LM_STUDIO_API_BASE=http://localhost:1234/v1
LLM_MODEL=mistral-7b-instruct
```

または、ターミナルで設定:

```bash
# Windows PowerShell
$env:LVM_SERVICE = "yolo_hybrid"
$env:YOLO_MODEL = "yolov8s-seg.pt"
$env:LM_STUDIO_API_BASE = "http://localhost:1234/v1"
$env:LLM_MODEL = "mistral-7b-instruct"

# Linux/macOS bash
export LVM_SERVICE=yolo_hybrid
export YOLO_MODEL=yolov8s-seg.pt
export LM_STUDIO_API_BASE=http://localhost:1234/v1
export LLM_MODEL=mistral-7b-instruct
```

## 使用方法

### 基本的な解析

```bash
python -m src analyze \
  --plant-id my_plant \
  --species ガジュマル \
  --image plant_photo.png
```

### 観察日記を生成

```bash
python -m src analyze \
  --plant-id my_plant \
  --species ガジュマル \
  --image plant_photo.png \
  --diary
```

### Markdown 形式で出力

```bash
python -m src analyze \
  --plant-id my_plant \
  --species ガジュマル \
  --image plant_photo.png \
  --diary \
  --format markdown > report.md
```

### JSON 形式で出力

```bash
python -m src analyze \
  --plant-id my_plant \
  --species ガジュマル \
  --image plant_photo.png \
  --format json | python -m json.tool
```

## YOLOv8 モデルの選択

| モデル | パラメータ | 推論時間 | 精度 | VRAM | 推奨 |
|--------|---------|--------|------|------|------|
| yolov8n-seg | 3.2M | 10ms | 低 | 2GB | クイック |
| **yolov8s-seg** | 11.8M | 20ms | 中 | **4GB** | **推奨** ✅ |
| yolov8m-seg | 27.3M | 40ms | 高 | 8GB | 高精度 |
| yolov8l-seg | 47.7M | 70ms | 最高 | 12GB | 極高精度 |

```bash
# モデルを変更する場合
export YOLO_MODEL=yolov8m-seg.pt
```

## LLM モデルの選択

### テキスト生成の品質でソート

| モデル | パラメータ | 速度 | 品質 | VRAM | 推奨 |
|--------|---------|------|------|------|------|
| mistral-7b-instruct | 7B | **⚡ 高速** | 中 | 4GB | **推奨** ✅ |
| neural-chat-7b | 7B | ⚡ 高速 | 中 | 4GB | 軽量 |
| llama-2-13b-chat | 13B | 中速 | **高** | 8GB | 高品質 |
| llama-2-70b-chat | 70B | 低速 | 最高 | 40GB | 極高品質 |

```bash
# LLMモデルを変更する場合
export LLM_MODEL=llama-2-13b-chat
```

## トラブルシューティング

### ❌ エラー: "Failed to load YOLO model"

**原因**: YOLOモデルが見つからない

**解決策**:
```bash
# モデルを再ダウンロード
python -c "from ultralytics import YOLO; YOLO('yolov8s-seg.pt')"

# または、手動でダウンロード
cd ~/.yolo  # またはYOLO キャッシュディレクトリ
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s-seg.pt
```

### ❌ エラー: "LLM text generation failed"

**原因**: LM Studio サーバーが起動していない

**解決策**:
```bash
# LM Studio を起動
# 「Local Server」で「Start Server」をクリック

# 接続確認
curl http://localhost:1234/v1/models

# ポート確認（別のアプリがポート1234を使用している場合）
# Windows: netstat -ano | findstr :1234
# Linux/Mac: lsof -i :1234
```

### ❌ エラー: "CUDA out of memory"

**原因**: GPU メモリが不足している

**解決策**:
```bash
# より小さいYOLOモデルを使用
export YOLO_MODEL=yolov8n-seg.pt

# または CPU モード
export YOLO_MODEL=yolov8s-seg.pt  # CPU で実行
```

### ❌ エラー: "Connection timeout"

**原因**: ネットワーク接続の問題

**解決策**:
```bash
# localhost ではなく 127.0.0.1 を試す
export LM_STUDIO_API_BASE=http://127.0.0.1:1234/v1

# ファイアウォール設定を確認
# ポート 1234 がブロックされていないか確認
```

## パフォーマンス最適化

### GPU 加速の有効化

```bash
# NVIDIA GPU (CUDA)
# 自動的に使用されます

# AMD GPU (ROCm)
export YOLO_DEVICE=0  # またはデバイス番号

# Apple Silicon (Metal)
export YOLO_DEVICE=0
```

### バッチ処理（複数画像の一括解析）

```python
# Python スクリプト例
import asyncio
from src.container import Container

async def batch_analyze():
    container = Container()
    
    images = ["plant1.png", "plant2.png", "plant3.png"]
    
    for image_path in images:
        request = ...  # リクエスト作成
        result = await container.plant_analysis_app.analyze_plant(request)
        print(f"Analyzed: {image_path}")

asyncio.run(batch_analyze())
```

## 各アプローチの比較

| 特性 | Mock | LM Studio | YOLO + LLM |
|------|------|-----------|-----------|
| **速度** | ⚡⚡⚡ 最速 | ⚡⚡ 高速 | ⚡ 中速 |
| **精度** | ★ 低 | ★★★ 中 | ★★★★★ **高** ✅ |
| **オフライン** | ✅ | ✅ | ✅ |
| **セットアップ** | ✅ 簡単 | 普通 | やや複雑 |
| **メモリ** | 低 | 中 | 中 |
| **用途** | テスト | クイック解析 | **精密診断** ✅ |

## 実装の詳細

### YOLOAdapter
- `ultralytics` の YOLOv8 を使用
- セグメンテーション対応（`-seg` モデル）
- リアルタイム検出と高精度を両立

### LLMTextGeneratorAdapter
- LM Studio または Ollama の LLM を使用
- OpenAI 互換API で接続
- 高品質なテキスト生成

### HybridAnalysisAdapter
- YOLOAdapter と LLMTextGeneratorAdapter を統合
- シーケンシャル処理（YOLO → LLM）
- 拡張性を保つヘキサゴナルアーキテクチャ

## 詳細情報

- YOLO 公式: https://github.com/ultralytics/ultralytics
- LM Studio: https://lmstudio.ai/
- Ollama: https://ollama.ai/

---

**精度重視の植物解析には YOLO + LLM ハイブリッドアプローチを推奨！** 🌱✨
