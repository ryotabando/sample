# LM Studio セットアップガイド

LM Studio を使用してローカルで植物画像解析を実行するための完全ガイドです。

## 概要

LM Studio は、大規模ビジョンモデル（LLaVA など）をローカルで実行するための統合開発環境です。

### 主な利点
- 🚀 **インターネット不要**: オフラインで動作
- 💰 **無料**: API費用なし
- ⚡ **高速**: ローカル実行で低レイテンシー
- 🔒 **プライベート**: データがサーバーに送信されない
- 🛡️ **セキュア**: 機密画像の分析に安全

## システム要件

### 最小要件
- **CPU**: 4コア以上
- **RAM**: 8GB 以上
- **VRAM**: 4GB 以上（GPU推奨）
- **ストレージ**: 20GB 以上の空き容量

### 推奨要件
- **CPU**: 8コア以上
- **RAM**: 16GB 以上
- **VRAM**: 8GB 以上（NVIDIA RTX3060 以上推奨）
- **ストレージ**: SSD（高速）

### 対応OS
- Windows 10/11
- macOS 12 以上
- Linux（Ubuntu 20.04 以上）

## インストール手順

### ステップ1: LM Studio をダウンロード

1. 公式ウェブサイトにアクセス
   ```
   https://lmstudio.ai/
   ```

2. 使用している OS 用のインストーラーをダウンロード
   - **Windows**: `LM-Studio-x.x.x-Setup.exe`
   - **macOS**: `LM-Studio-x.x.x.dmg`
   - **Linux**: `LM-Studio-x.x.x-appimage`

3. ダウンロード完了を確認

### ステップ2: インストール実行

#### Windows の場合
```bash
# ダウンロードしたEXEファイルをダブルクリック
# インストールウィザードに従い、「Next」で進める
# インストール完了後、LM Studioが自動起動
```

#### macOS の場合
```bash
# DMGファイルをダブルクリック
# LM Studioをアプリケーションフォルダへドラッグ&ドロップ
# アプリケーションフォルダから起動
```

#### Linux の場合
```bash
chmod +x LM-Studio-*.appimage
./LM-Studio-*.appimage
```

### ステップ3: 初回起動

1. LM Studio を起動
2. ウェルカムスクリーンが表示される
3. 「Get Started」をクリック

### ステップ4: ビジョンモデルのダウンロード

1. 左側メニューの **「Search」** をクリック

2. 検索ボックスに「llava」と入力

3. 以下から選択してダウンロード:
   ```
   llava-1.6-7b-q4        ← 推奨（4GB VRAM）
   llava-1.6-13b-q4       ← 標準（8GB VRAM）
   llava-1.6-34b-q4       ← 高精度（24GB VRAM）
   ```

4. モデルを選択して、「Download」をクリック

5. ダウンロード完了を待つ（5-30分程度）

### ステップ5: ローカルサーバーの起動

1. 左側メニューの **「Local Server」** をクリック

2. 「Select a Model」ドロップダウンから、ダウンロードしたモデルを選択
   ```
   llava-1.6-7b-q4
   ```

3. **「Start Server」** をクリック

4. 以下のメッセージが表示される:
   ```
   LM Studio Local Server
   Server is running at: http://localhost:1234/v1
   ```

5. サーバーが起動しました ✅

### ステップ6: Python 環境の設定

```bash
# リポジトリディレクトリに移動
cd plant-test

# 仮想環境を作成（オプション）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# .env ファイルを編集
nano .env  # または手動で編集
```

### ステップ7: 環境変数の設定

`.env` ファイルを編集:

```bash
# Environment variables
ENVIRONMENT=development
LVM_SERVICE=lm_studio
LOG_LEVEL=INFO

# LM Studio Configuration
LM_STUDIO_API_BASE=http://localhost:1234/v1
LM_STUDIO_MODEL=llava-1.6-7b-q4
```

または、環境変数をターミナルで設定:

```bash
# Windows PowerShell
$env:LVM_SERVICE = "lm_studio"
$env:LM_STUDIO_API_BASE = "http://localhost:1234/v1"

# Linux/macOS bash
export LVM_SERVICE=lm_studio
export LM_STUDIO_API_BASE=http://localhost:1234/v1
```

## 使用開始

### 基本的な解析

```bash
python -m src analyze \
  --plant-id plant1 \
  --species ガジュマル \
  --image sample_plant.png
```

### 観察日記を生成

```bash
python -m src analyze \
  --plant-id plant1 \
  --species ガジュマル \
  --image sample_plant.png \
  --diary
```

### JSON 形式で出力

```bash
python -m src analyze \
  --plant-id plant1 \
  --species ガジュマル \
  --image sample_plant.png \
  --format json
```

### Markdown 形式で出力

```bash
python -m src analyze \
  --plant-id plant1 \
  --species ガジュマル \
  --image sample_plant.png \
  --format markdown
```

## トラブルシューティング

### ❌ エラー: "LM Studio connection failed"

**原因**: LM Studio サーバーが起動していない

**解決策**:
```bash
# LM Studio が起動しているか確認
# 左側「Local Server」で「Start Server」をクリック

# ポート番号が正しいか確認
# デフォルト: http://localhost:1234/v1

# ファイアウォール設定を確認
# ポート 1234 がブロックされていないか確認
```

### ❌ エラー: "Model not loaded"

**原因**: モデルがダウンロードされていない、または選択されていない

**解決策**:
```bash
1. LM Studio の「Search」でモデルをダウンロード
2. 「Local Server」でモデルを選択
3. 正しいモデル名を .env に設定
   LM_STUDIO_MODEL=llava-1.6-7b-q4
```

### ❌ エラー: "CUDA out of memory"

**原因**: GPU メモリが不足している

**解決策**:
```bash
# より小さいモデルを使用
LM_STUDIO_MODEL=llava-1.6-7b-q4

# または、CPU モードを使用（遅い）
# LM Studio の設定でGPU使用を無効化
```

### ❌ エラー: "Connection refused"

**原因**: ネットワーク接続の問題

**解決策**:
```bash
# localhost ではなく 127.0.0.1 を試す
LM_STUDIO_API_BASE=http://127.0.0.1:1234/v1

# ポートが使用されているか確認
# Windows: netstat -ano | findstr :1234
# Linux/Mac: lsof -i :1234
```

## パフォーマンス最適化

### GPU 加速の有効化

LM Studio で GPU を使用することで 5-10 倍高速化されます:

```bash
# NVIDIA GPU (推奨)
LM_STUDIO_GPU=cuda

# AMD GPU
LM_STUDIO_GPU=rocm

# Apple Silicon
LM_STUDIO_GPU=metal

# CPU のみ（低速）
LM_STUDIO_GPU=cpu
```

### モデルの選択

```
処理速度: llava-7b > llava-13b > llava-34b
精度:    llava-7b < llava-13b < llava-34b

推奨: llava-1.6-13b-q4（バランス重視）
```

## 高度なセットアップ

### リモートサーバー上で実行

別のマシンで LM Studio を実行:

```bash
# リモートサーバーで LM Studio を起動
# (例: cloud PC, Linux server)

# ローカルマシンから接続
export LM_STUDIO_API_BASE=http://remote-server-ip:1234/v1
python -m src analyze --plant-id plant1 --image image.png
```

### Docker でのデプロイ

```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# LM Studio インストール
RUN apt-get update && apt-get install -y lm-studio

# Python セットアップ
COPY requirements.txt .
RUN pip install -r requirements.txt

# アプリケーション実行
ENTRYPOINT ["python", "-m", "src"]
```

## よくある質問

### Q: インターネット接続は必須ですか？
**A**: いいえ。LM Studio を起動後は完全にオフラインで動作します。

### Q: 料金は発生しますか？
**A**: LM Studio は無料です。

### Q: どのモデルがベストですか？
**A**: 推奨は `llava-1.6-13b-q4`です。バランスの取れた精度と速度を提供します。

### Q: 複数の GPU で並列実行できますか？
**A**: LM Studio GUI では不可ですが、Python から複数の接続を並列化できます。

### Q: ローカル以外で実行できますか？
**A**: はい、リモートサーバーで LM Studio を実行後、`LM_STUDIO_API_BASE` を設定してください。

## さらに詳しく

- LM Studio 公式サイト: https://lmstudio.ai/
- LLaVA モデル情報: https://llava-vl.github.io/
- 公式ドキュメント: https://lmstudio.ai/docs

---

**質問や問題があれば、GitHub の Issue を作成してください！** 🌱
