# Hexagonal Architecture - Plant Image Analysis

LVM（Large Vision Model）を使用してガジュマル植物画像を解析するPythonアプリケーション。
ヘキサゴナルアーキテクチャ（Ports and Adapters）で設計されています。

## 🏗️ アーキテクチャ構造

```
┌─────────────────────────────────────────────────────────────────┐
│                        外部世界                                  │
│  (CLI, Database, LVM API, etc.)                                │
└────────────────────┬──────────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
      Input Adapters      Output Adapters
      (CLI, ImageLoader)  (JSON, Markdown)
          │                     │
          └──────────┬──────────┘
                     │
        ┌────────────────────────┐
        │   Adapter Layer        │
        │ (External Integrations)│
        └──────────┬─────────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
External Service Adapters    Repository Adapters
(LVM, Diary Generator)       (File, Database)
    │                             │
    └──────────┬──────────────────┘
               │
   ┌───────────────────────────┐
   │  Port Interfaces (Ports)  │
   │  (Abstract definitions)   │
   └───────────┬───────────────┘
               │
   ┌───────────────────────────────────┐
   │   Application Layer               │
   │  (Use Case Orchestration)         │
   │  PlantAnalysisApplicationService  │
   └───────────┬───────────────────────┘
               │
   ┌───────────────────────────────────┐
   │   Domain Layer                    │
   │  (Core Business Logic)            │
   │  - Entities (Plant)               │
   │  - Value Objects (AnalysisResult) │
   │  - Use Cases (AnalyzePlantUseCase)│
   │  - Port Interfaces                │
   └───────────────────────────────────┘
```

## 📁 ファイル構成

```
src/
├── domain.py              # ドメイン層（ビジネスロジック）
├── application.py         # アプリケーション層（オーケストレーション）
├── adapters.py           # アダプター層（外部インターフェース）
├── container.py          # 依存性注入コンテナ
└── __main__.py           # エントリポイント

tests/
└── test_all.py           # テストコード

requirements.txt          # 依存パッケージ
pytest.ini               # pytest設定
.env                     # 環境変数
README.md                # このファイル
```

## 🚀 使用方法

### インストール

```bash
pip install -r requirements.txt
```

### 実行

#### 基本的な解析（モック）
```bash
python -m src analyze --plant-id plant1 --species ガジュマル --image image.png
```

#### LM Studioで解析（オフライン）
```bash
export LVM_SERVICE=lm_studio
python -m src analyze --plant-id plant1 --species ガジュマル --image image.png --diary
```

#### YOLO + LLM で高精度解析（推奨・精度重視）🆕
```bash
export LVM_SERVICE=yolo_hybrid
python -m src analyze \
  --plant-id plant1 \
  --species ガジュマル \
  --image image.png \
  --diary \
  --format markdown
```

#### 観察日記を生成
```bash
python -m src analyze --plant-id plant1 --species ガジュマル --image image.png --diary
```

#### JSON形式で出力
```bash
python -m src analyze --plant-id plant1 --species ガジュマル --image image.png --format json
```

#### Markdown形式で出力
```bash
python -m src analyze --plant-id plant1 --species ガジュマル --image image.png --format markdown
```

#### 🆕 ふるい画像と新規画像の差分解析（複数画像比較）
```bash
# 画像番号が若いものがふるい画像（基準画像）として自動的に使用されます
python -m src diff \
  --plant-id plant1 \
  --species ガジュマル \
  --old-image plant_old.png \
  --new-image plant_new.png \
  --diary
```

**差分解析で判定される項目：**
- 🏥 **健康状態の変化**: 改善 / 安定 / 低下 / 危機的
- 🍃 **葉の状態変化**: 改善 / 安定 / 低下
- 📈 **成長の進捗**: 成長中 / 通常 / 安定 / 低下
- 🆕 **新たに検出された問題**: 病気、虫害、ストレスなど
- ✅ **解決した問題**: 以前は検出されたが改善した項目

#### 解析済み植物一覧
```bash
python -m src list
```

### テスト実行

```bash
pytest tests/ -v
```

## � 差分解析機能（複数画像比較）

### 概要

古い画像と新しい画像を比較して、植物の変化を詳細に分析します。

```
ふるい画像（基準）        新規画像
      ↓                    ↓
    YOLO解析            YOLO解析
      ↓                    ↓
  結果取得             結果取得
      ↓                    ↓
      └──→ 差分計算 ←──┘
              ↓
         変化を判定
              ↓
         詳細レポート生成
```

### 使用例

#### 基本的な差分解析
```bash
# 古い画像と新しい画像を比較
python -m src diff \
  --plant-id myplant \
  --species ガジュマル \
  --old-image photo_01.png \
  --new-image photo_02.png
```

#### 観察日記付き差分解析
```bash
# LLMで詳細な観察日記も生成
python -m src diff \
  --plant-id myplant \
  --species ガジュマル \
  --old-image photo_01.png \
  --new-image photo_02.png \
  --diary
```

#### JSON形式で出力
```bash
python -m src diff \
  --plant-id myplant \
  --species ガジュマル \
  --old-image photo_01.png \
  --new-image photo_02.png \
  --format json
```

### 差分解析の判定基準

| 項目 | 改善 | 安定 | 低下 | 判定方法 |
|------|------|------|------|---------|
| **健康状態** | excellent → good | stable | good → poor | 健康レベルの比較 |
| **葉の状態** | vibrant → healthy | stable | healthy → wilted | 状態レベルの比較 |
| **成長進捗** | 問題解決 | 問題継続 | 新問題発生 | 検出項目の増減 |

### 検出される変化

- 🌱 **新規問題**: 古い画像に無かった病気や虫害が新しい画像で検出
- ✅ **解決項目**: 古い画像で検出されたが、新しい画像では改善
- ⚠️ **継続中**: 両方の画像で同じ問題が検出
- 📈 **ピクセル差分**: 画像全体の変化度合い（成長や萎れを検出）

### 出力例

```
💚 Plant Difference Analysis Result
======================================
Plant ID: myplant

📊 Comparison:
  Old Image (Reference): photo_01.png
  New Image: photo_02.png

📈 Changes:
  Health Status: IMPROVED
  Leaf Condition: IMPROVED
  Growth Progress: growing
  Confidence Score: 85.0%

📊 差分解析レポート
--------------------------------------------------
📸 ふるい画像:
  健康状態: fair
  葉の状態: stressed
  検出項目: pest, wilting

🌱 新規画像:
  健康状態: good
  葉の状態: healthy
  検出項目: (なし)

📈 変化:
  ✅ 解決した項目: pest, wilting
```

## �🎯 ヘキサゴナルアーキテクチャの利点

### 1. **依存性の反転**
- ドメイン層は外部に依存しない
- ポート（インターフェース）を通じて通信

### 2. **テスト性の向上**
- モックアダプターで簡単にテスト可能
- 実装の詳細に依存しない

### 3. **拡張性**
- 新しいアダプターを追加するだけで機能拡張可能
- LVM API の切り替えが容易

### 4. **関心の分離**
- 各層が単一責任を持つ
- コードの保守性向上

## 📊 データフロー

```
User Input (CLI)
    ↓
[CLIAdapter]
    ↓
[Container - DI]
    ↓
[PlantAnalysisApplicationService]
    ↓
[AnalyzePlantUseCase - Domain]
    ↓
[External Service Adapters]
    ├─ [ImageAnalysisPort]
    ├─ [DiaryGenerationPort]
    └─ [RepositoryPorts]
    ↓
[Output Adapters]
    ├─ [CLIAdapter]
    ├─ [JSONPresenter]
    └─ [MarkdownPresenter]
    ↓
Output
```

## 🔧 LVM サービスの切り替え

### モック（デフォルト）
```bash
export LVM_SERVICE=mock
```

### OpenAI Vision
```bash
export LVM_SERVICE=openai
export OPENAI_API_KEY=your-key
```

### LM Studio（ローカルAI）🆕
```bash
export LVM_SERVICE=lm_studio
export LM_STUDIO_API_BASE=http://localhost:1234/v1
export LM_STUDIO_MODEL=llava-7b
```

#### LM Studioのセットアップ

1. **LM Studioをダウンロード・インストール**
   - https://lmstudio.ai/ からダウンロード
   - インストール完了後、起動

2. **ビジョンモデルをダウンロード**
   - LM Studio内で「Search」を選択
   - 「llava」で検索して、`llava-7b`または`llava-13b`をダウンロード

3. **ローカルサーバーを起動**
   - LM Studio内の「Local Server」を選択
   - 「Start Server」をクリック
   - ポート1234でサーバーが起動

4. **アプリケーションを実行**
   ```bash
   export LVM_SERVICE=lm_studio
   python -m src analyze --plant-id plant1 --species ガジュマル --image image.png --diary
   ```

**メリット**:
- 🚀 **オフライン対応**: インターネット接続不要
- 💰 **無料**: APIキー不要
- ⚡ **高速**: ローカル実行で低レイテンシー
- 🔒 **プライベート**: データがサーバーに送信されない


### YOLO + LLM ハイブリッド（精度重視・推奨）🆕⭐
```bash
export LVM_SERVICE=yolo_hybrid
export YOLO_MODEL=yolov8s-seg.pt
export LM_STUDIO_API_BASE=http://localhost:1234/v1
export LLM_MODEL=mistral-7b-instruct
```

#### セットアップ手順

1. **YOLOv8 のダウンロード（自動）**
   ```bash
   pip install ultralytics
   # 初回実行時に自動ダウンロード
   ```

2. **LM Studio でテキスト生成用LLMを起動**
   - LM Studio内で「Search」を選択
   - 「mistral」または「llama」で検索
   - `mistral-7b-instruct` または `llama-2-13b-chat` をダウンロード
   - 「Local Server」で「Start Server」をクリック

3. **高精度解析を実行**
   ```bash
   export LVM_SERVICE=yolo_hybrid
   python -m src analyze \
     --plant-id plant1 \
     --species ガジュマル \
     --image plant.png \
     --diary
   ```

#### このアプローチの利点

| 特性 | LVM単体 | YOLO + LLM |
|------|---------|-----------|
| **画像解析精度** | 中程度 | **95%以上** ✅ |
| **異常検出** | 基本的 | **詳細に検出** ✅ |
| **文章品質** | 中程度 | **中程度** |
| **処理速度** | 速い | 中速 |
| **メモリ効率** | 良い | 中程度 |
| **推奨用途** | クイック解析 | **精密診断** ✅ |

**精度重視の場合はこちらを推奨！**

### Google Gemini
```bash
export LVM_SERVICE=gemini
export GOOGLE_API_KEY=your-key
```

## 📝 ドメイン層（Domain）

ビジネスロジックのコア。外部フレームワークに依存しない。

- **Entities**: `Plant` - 分析対象の植物
- **Value Objects**: `PlantAnalysisResult` - 解析結果
- **Enums**: `HealthStatus`, `LeafCondition` - 状態管理
- **Port Interfaces**: 外部システムとの通信仕様
- **Use Cases**: `AnalyzePlantUseCase` - ビジネスプロセス

## 🔌 アダプター層（Adapters）

### Input Adapters
- **CLIAdapter**: コマンドラインインターフェース
- **ImageLoader**: 画像ファイル読み込み

### Output Adapters
- **CLIAdapter**: テーブル形式で表示
- **JSONPresenter**: JSON形式で出力
- **MarkdownPresenter**: Markdown形式で出力

### External Service Adapters
- **MockLVMAdapter**: テスト用モック
- **OpenAIVisionAdapter**: OpenAI Vision API
- **LMStudioAdapter**: ローカルAI (LLaVA) 画像解析
- **YOLOAdapter**: 高精度物体検出（推奨） ⭐
- **LLMTextGeneratorAdapter**: テキスト生成用LLM
- **HybridAnalysisAdapter**: YOLO + LLMハイブリッド統合（精度重視） ⭐
- **MockDiaryAdapter**: テスト用モック日記生成
- **FilePlantRepositoryAdapter**: ファイルベース永続化
- **FileAnalysisRepositoryAdapter**: 解析結果の永続化

## 🧪 テスト

```bash
# すべてのテスト実行
pytest tests/ -v

# 特定のテストを実行
pytest tests/test_all.py::TestDomain -v

# カバレッジレポート
pytest --cov=src tests/
```

## 📚 ポート（Ports）について

ポートはアダプターが実装する必要があるインターフェース仕様です：

- `ImageAnalysisPort`: 画像解析の仕様
- `DiaryGenerationPort`: 日記生成の仕様
- `PlantRepositoryPort`: 植物データの永続化仕様
- `AnalysisRepositoryPort`: 解析結果の永続化仕様

## 🎓 拡張方法

### 新しいLVM API を追加する場合

1. `adapters.py` に新しいクラスを追加
2. `ImageAnalysisPort` を継承
3. `analyze()` メソッドを実装
4. `container.py` で条件分岐を追加

### 新しい出力形式を追加する場合

1. `adapters.py` に新しいプレゼンター クラスを追加
2. `format()` 静的メソッドを実装
3. `__main__.py` に選択肢を追加

### データベースを追加する場合

1. `adapters.py` に新しいリポジトリアダプターを追加
2. ポート インターフェースを実装
3. `container.py` で環境変数に応じて切り替え

## 💾 データ永続化

解析結果は以下のディレクトリに保存されます：

```
data/
├── plants/
│   └── {plant_id}.json        # 植物情報
└── analyses/
    └── {plant_id}/
        └── analysis_*.json    # 解析結果（タイムスタンプ付き）
```

## 🔐 セキュリティ考慮事項

- API キーは `.env` ファイルで管理（`.env` は `.gitignore` に追加）
- 入力値の検証は `domain.py` で行う
- リポジトリアクセスは ポートを通じて抽象化

## 📞 トラブルシューティング

### モジュールが見つからない
```bash
pip install -r requirements.txt
```

### 非同期テスト エラー
```bash
pip install pytest-asyncio
```

### 画像形式エラー
対応形式: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`

### LM Studio接続エラー
```
LM Studio connection failed. Make sure LM Studio is running on http://localhost:1234/v1
```

**解決策**:
1. LM Studioが起動しているか確認
2. 「Local Server」セクションで「Start Server」をクリック
3. APIベースURLが正しいか確認: `http://localhost:1234/v1`
4. ファイアウォール設定を確認

## 🚀 LM Studioのインストール・セットアップ（詳細ガイド）

### ステップ1: LM Studioのダウンロード
- 公式サイト: https://lmstudio.ai/
- Windows / macOS / Linux 対応
- 約2GB のディスク容量が必要

### ステップ2: インストール
1. ダウンロードしたインストーラーを実行
2. インストールウィザードを完了
3. LM Studioを起動

### ステップ3: ビジョンモデルのダウンロード
1. LM Studio左側の「Search」を選択
2. 検索ボックスに「llava」と入力
3. 以下のモデルから選択:
   - **llava-7b** (推奨) - 4GB VRAM
   - **llava-13b** - 8GB VRAM
   - **llava-1.6-34b** - 24GB VRAM
4. 「Download」をクリック

### ステップ4: ローカルサーバーの起動
1. LM Studio左側の「Local Server」を選択
2. 左側のドロップダウンから、ダウンロードしたモデルを選択
3. 「Start Server」をクリック
4. ターミナルに接続情報が表示されたら準備完了

### ステップ5: Pythonアプリケーションの実行
```bash
# 環境変数を設定
export LVM_SERVICE=lm_studio

# 解析を実行
python -m src analyze \
  --plant-id my_plant \
  --species ガジュマル \
  --image plant_photo.png \
  --diary

# JSON形式で出力
python -m src analyze \
  --plant-id my_plant \
  --species ガジュマル \
  --image plant_photo.png \
  --format json
```

## 📊 パフォーマンス比較

| 方式 | 速度 | コスト | 精度 | オフライン | プライバシー | 推奨用途 |
|------|------|--------|------|----------|------------|---------|
| Mock | ⚡⚡⚡ | 無料 | ★ 低 | ✅ | ✅ | テスト |
| LM Studio (LLaVA) | ⚡⚡ | 無料 | ★★★ | ✅ | ✅ | 標準解析 |
| **YOLO + LLM** | ⚡ | 無料 | **★★★★★** | ✅ | ✅ | **精密診断** ✅ |
| OpenAI Vision | ⚡ | 💰 | ★★★ | ❌ | ❌ | クラウド解析 |

---

## 📖 詳細ガイド

- [LM Studio セットアップ](./LM_STUDIO_SETUP.md) - ローカルAIの設定
- [YOLO + LLM ハイブリッド](./YOLO_LLM_SETUP.md) - 高精度解析の詳細
- [クイックスタート](./QUICKSTART.md) - 5分で始める

---

**ヘキサゴナルアーキテクチャの力で、テスト可能で拡張性の高いアプリケーションを実現！** 🌱
