"""
Adapter Layer - External Interfaces
アダプター層は外部システムとの接続を担当
"""

import asyncio
import json
import os
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from .domain import (
    AnalysisRepositoryPort,
    DiaryGenerationPort,
    DifferenceAnalysisPort,
    ImageAnalysisPort,
    Plant,
    PlantAnalysisResult,
    PlantRepositoryPort,
)

# ========== Input Adapters (入力アダプター) ==========

class CLIAdapter:
    """コマンドラインインターフェース"""
    
    @staticmethod
    def print_result(response: dict) -> None:
        """解析結果を表示"""
        print("\n" + "=" * 70)
        print(f"🌱 Plant Analysis Result")
        print("=" * 70)
        print(f"Plant ID: {response.get('plant_id')}")
        print(f"Overall Health: {response.get('overall_health').upper()}")
        print(f"Leaf Condition: {response.get('leaf_condition')}")
        print(f"Growth Stage: {response.get('growth_stage')}")
        print(f"Confidence Score: {response.get('confidence_score'):.1%}")
        
        if response.get("diary"):
            print(f"\n📝 Observation Diary:")
            print("-" * 70)
            print(response["diary"]["content"])
            print("-" * 70)
        
        print("=" * 70 + "\n")


class ImageLoader:
    """画像ローダー"""
    
    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
    
    @staticmethod
    def load(image_path: str) -> bytes:
        """画像をバイナリで読み込む"""
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if path.suffix.lower() not in ImageLoader.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {path.suffix}")
        
        with open(path, "rb") as f:
            return f.read()
    
    @staticmethod
    def validate(image_path: str) -> bool:
        """画像パスの妥当性確認"""
        path = Path(image_path)
        return path.exists() and path.suffix.lower() in ImageLoader.SUPPORTED_FORMATS


# ========== Output Adapters (出力アダプター) ==========

class JSONPresenter:
    """JSON形式でのプレゼンテーション"""
    
    @staticmethod
    def format(response: dict) -> str:
        """レスポンスをJSON形式に変換"""
        return json.dumps(response, indent=2, ensure_ascii=False)


class MarkdownPresenter:
    """Markdown形式でのプレゼンテーション"""
    
    @staticmethod
    def format(response: dict) -> str:
        """レスポンスをMarkdown形式に変換"""
        lines = [
            "# 🌱 植物解析レポート",
            f"\n## 基本情報",
            f"- **Plant ID**: {response.get('plant_id')}",
            f"- **Overall Health**: {response.get('overall_health')}",
            f"- **Confidence**: {response.get('confidence_score'):.1%}",
            f"\n## 詳細",
            f"- **Leaf Condition**: {response.get('leaf_condition')}",
            f"- **Growth Stage**: {response.get('growth_stage')}",
        ]
        
        if response.get("diary"):
            lines.append(f"\n## 📝 観察日記")
            lines.append(response["diary"]["content"])
        
        return "\n".join(lines)


# ========== External Service Adapters (外部サービスアダプター) ==========

class LVMAdapter(ImageAnalysisPort):
    """LVM画像解析アダプター - 抽象基底"""
    pass


class MockLVMAdapter(LVMAdapter):
    """モック LVM（テスト用）"""
    
    async def analyze(self, image_path: str) -> dict:
        """モック解析を実行"""
        await asyncio.sleep(0.1)  # 処理をシミュレート
        
        return {
            "overall_health": "good",
            "leaf_condition": "healthy",
            "growth_stage": "mature",
            "confidence_score": 0.87,
            "leaf_color": "vibrant green",
            "leaf_texture": "glossy",
            "visible_diseases": [],
            "health_notes": "Plant appears healthy",
            "recommendations": [
                "Maintain regular watering",
                "Provide 4-6 hours of sunlight",
            ],
            "timestamp": datetime.now().isoformat(),
        }


class OpenAIVisionAdapter(LVMAdapter):
    """OpenAI Vision API アダプター"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
    
    async def analyze(self, image_path: str) -> dict:
        """OpenAI Visionで解析"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required")
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        import base64
        image_base64 = base64.b64encode(image_data).decode()
        
        prompt = """
Analyze this Ficus retusa (ガジュマル) plant image and respond with JSON:
{
    "overall_health": "excellent/good/fair/poor/critical",
    "leaf_condition": "vibrant/healthy/stressed/diseased/wilted",
    "growth_stage": "seedling/juvenile/mature/flowering/fruiting",
    "confidence_score": 0.0-1.0,
    "leaf_color": "description",
    "visible_diseases": ["list"],
    "recommendations": ["care tips"]
}
"""
        
        response = await client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                        },
                    ],
                }
            ],
            max_tokens=1024,
        )

        response_text = response.choices[0].message.content or ""
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        try:
            return json.loads(json_match.group() if json_match else response_text)
        except (json.JSONDecodeError, ValueError):
            return {
                "overall_health": "fair",
                "leaf_condition": "stressed",
                "growth_stage": "unknown",
                "confidence_score": 0.0,
                "health_notes": "LLM response could not be parsed",
                "recommendations": [],
                "timestamp": datetime.now().isoformat(),
            }


class LMStudioAdapter(LVMAdapter):
    """LM Studio ローカルAI アダプター
    
    LM Studioで実行されているビジョンモデルを使用
    デフォルトエンドポイント: http://localhost:1234/v1
    """
    
    def __init__(
        self,
        api_base: str = "http://localhost:1234/v1",
        model: str = "llava-7b",
    ):
        self.api_base = api_base
        self.model = model
    
    async def analyze(self, image_path: str) -> dict:
        """LM Studioでローカル解析を実行"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package required")
        
        # LM StudioのOpenAI互換APIクライアントを作成
        client = AsyncOpenAI(
            api_key="lm-studio",  # ダミーキー
            base_url=self.api_base,
        )
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        import base64
        image_base64 = base64.b64encode(image_data).decode()
        
        prompt = """
Analyze this Ficus retusa (ガジュマル) plant image and respond with JSON:
{
    "overall_health": "excellent/good/fair/poor/critical",
    "leaf_condition": "vibrant/healthy/stressed/diseased/wilted",
    "growth_stage": "seedling/juvenile/mature/flowering/fruiting",
    "confidence_score": 0.0-1.0,
    "leaf_color": "description",
    "visible_diseases": ["list of issues or empty"],
    "health_notes": "summary of plant health",
    "recommendations": ["care recommendations"]
}
"""
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1024,
                temperature=0.7,
            )
            
            response_text = response.choices[0].message.content or ""

            # JSON部分を抽出（マークダウンコード等でラップされている場合）
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            try:
                return json.loads(json_match.group() if json_match else response_text)
            except (json.JSONDecodeError, ValueError):
                return {
                    "overall_health": "fair",
                    "leaf_condition": "stressed",
                    "growth_stage": "unknown",
                    "confidence_score": 0.0,
                    "health_notes": "LLM response could not be parsed",
                    "recommendations": [],
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            raise RuntimeError(
                f"LM Studio connection failed. "
                f"Make sure LM Studio is running on {self.api_base}\n"
                f"Error: {str(e)}"
            )


class DiaryAdapter(DiaryGenerationPort):
    """日記生成アダプター - 抽象基底"""
    pass


class MockDiaryAdapter(DiaryAdapter):
    """モック日記生成（テスト用）"""
    
    async def generate(self, analysis_data: dict) -> str:
        """モック日記を生成"""
        await asyncio.sleep(0.1)
        
        health = analysis_data.get("overall_health", "不明")
        return f"""
【ガジュマル観察日記】

本日のガジュマルは{health}な状態を保っています。

葉の様子も良好で、光合成が活発に行われているようです。
光沢感もあり、元気そうです。

【本日のケアアドバイス】
- 朝日をしっかり当てる
- 土が乾いたら水やりする
- 定期的に液肥を与える

次のチェックは1週間後の予定です。
"""


# ========== Repository Adapters (リポジトリアダプター) ==========

class FilePlantRepositoryAdapter(PlantRepositoryPort):
    """ファイルベースの植物リポジトリ"""
    
    def __init__(self, data_dir: str = "data/plants"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def save(self, plant: Plant) -> None:
        """植物を保存"""
        file_path = self.data_dir / f"{plant.id}.json"
        
        data = {
            "id": plant.id,
            "species": plant.species,
            "image_path": plant.image_path,
            "captured_at": plant.captured_at.isoformat(),
            "metadata": plant.metadata or {},
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def get_by_id(self, plant_id: str) -> Optional[Plant]:
        """植物を取得"""
        file_path = self.data_dir / f"{plant_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return Plant(
            id=data["id"],
            species=data["species"],
            image_path=data["image_path"],
            captured_at=datetime.fromisoformat(data["captured_at"]),
            metadata=data.get("metadata"),
        )


class FileAnalysisRepositoryAdapter(AnalysisRepositoryPort):
    """ファイルベースの解析結果リポジトリ"""
    
    def __init__(self, data_dir: str = "data/analyses"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def save(self, result: PlantAnalysisResult) -> None:
        """解析結果を保存"""
        plant_dir = self.data_dir / result.plant_id
        plant_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().isoformat().replace(":", "-")
        file_path = plant_dir / f"analysis_{timestamp}.json"
        
        data = {
            "plant_id": result.plant_id,
            "overall_health": result.overall_health.value,
            "leaf_condition": result.leaf_condition.value,
            "growth_stage": result.growth_stage,
            "confidence_score": result.confidence_score,
            "details": result.details,
            "observation_diary": result.observation_diary,
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def get_latest(self, plant_id: str) -> Optional[PlantAnalysisResult]:
        """最新の解析結果を取得"""
        plant_dir = self.data_dir / plant_id
        
        if not plant_dir.exists():
            return None
        
        files = sorted(plant_dir.glob("analysis_*.json"))
        
        if not files:
            return None
        
        with open(files[-1], "r", encoding="utf-8") as f:
            data = json.load(f)
        
        from .domain import HealthStatus, LeafCondition
        
        return PlantAnalysisResult(
            plant_id=data["plant_id"],
            overall_health=HealthStatus(data["overall_health"]),
            leaf_condition=LeafCondition(data["leaf_condition"]),
            growth_stage=data["growth_stage"],
            confidence_score=data["confidence_score"],
            details=data["details"],
            observation_diary=data.get("observation_diary"),
        )


# ========== YOLO + LLM Hybrid Adapters (精度重視版) ==========

class YOLOAdapter(ImageAnalysisPort):
    """YOLOv8 画像解析アダプター - 高精度な葉の異常検出"""
    
    def __init__(self, model_name: str = "yolov8n-seg.pt"):
        """
        初期化
        
        Args:
            model_name: YOLOモデル
                - yolov8n-seg.pt (nano, 高速)
                - yolov8s-seg.pt (small)
                - yolov8m-seg.pt (medium, 推奨)
                - yolov8l-seg.pt (large)
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics required: pip install ultralytics"
            )
        
        self.model_name = model_name
        try:
            self.model = YOLO(model_name)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load YOLO model {model_name}\n"
                f"Download: yolo detect download {model_name}\n"
                f"Error: {e}"
            )
    
    async def analyze(self, image_path: str) -> dict:
        """YOLOで高精度解析"""
        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            raise ImportError("pillow required: pip install pillow")
        
        # 画像を読み込み
        image = Image.open(image_path)
        
        # YOLO推論実行
        results = self.model.predict(image_path, conf=0.5)
        result = results[0]
        
        # 検出結果を分析
        detected_classes = []
        confidence_scores = []
        
        if result.boxes is not None:
            for box, conf, cls in zip(
                result.boxes.xyxy,
                result.boxes.conf,
                result.boxes.cls
            ):
                class_name = result.names[int(cls)]
                detected_classes.append(class_name)
                confidence_scores.append(float(conf))
        
        # 健康状態を判定
        overall_confidence = (
            np.mean(confidence_scores) if confidence_scores else 0.7
        )
        
        health_status = "good"
        leaf_condition = "healthy"
        
        # 検出結果に基づいて判定
        class_lower = [c.lower() for c in detected_classes]
        
        if any("disease" in c or "病気" in c for c in class_lower):
            health_status = "poor"
            leaf_condition = "diseased"
        elif any("stress" in c or "ストレス" in c for c in class_lower):
            health_status = "fair"
            leaf_condition = "stressed"
        elif any("pest" in c or "虫害" in c for c in class_lower):
            health_status = "fair"
            leaf_condition = "stressed"
        elif any("wilted" in c or "枯れ" in c for c in class_lower):
            health_status = "poor"
            leaf_condition = "wilted"
        else:
            health_status = "good"
            leaf_condition = "healthy"
        
        return {
            "overall_health": health_status,
            "leaf_condition": leaf_condition,
            "growth_stage": "mature",
            "confidence_score": float(overall_confidence),
            "detected_objects": detected_classes,
            "detection_confidence": confidence_scores,
            "analysis_method": "YOLO v8",
            "health_notes": f"Detected: {', '.join(set(detected_classes))}" if detected_classes else "No abnormalities detected",
            "recommendations": [
                "Monitor plant regularly",
                "Ensure proper watering",
                "Provide adequate sunlight",
            ],
            "timestamp": datetime.now().isoformat(),
        }


class LLMTextGeneratorAdapter(DiaryGenerationPort):
    """LLM テキスト生成アダプター - 高品質観察日記生成"""
    
    def __init__(
        self,
        api_base: str = "http://localhost:1234/v1",
        model: str = "mistral-7b-instruct",
    ):
        """
        初期化
        
        Args:
            api_base: LLM APIベースURL（LM Studio等）
            model: LLMモデル
                - mistral-7b-instruct
                - llama-2-13b-chat
                - neural-chat-7b
        """
        self.api_base = api_base
        self.model = model
    
    async def generate(self, analysis_data: dict) -> str:
        """LLMで高品質な観察日記を生成"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai required: pip install openai")

        client = AsyncOpenAI(
            api_key="lm-studio",
            base_url=self.api_base,
            timeout=60.0,
        )

        # 差分解析結果か単体解析結果かでプロンプトを分岐
        if analysis_data.get("is_difference_analysis"):
            old_health = analysis_data.get("old_health_status", "unknown")
            new_health = analysis_data.get("new_health_status", "unknown")
            health_change = analysis_data.get("health_change", "stable")
            leaf_change = analysis_data.get("leaf_condition_change", "stable")
            new_issues = analysis_data.get("new_issues_detected", [])
            resolved = analysis_data.get("resolved_issues", [])
            persistent = analysis_data.get("persistent_issues", [])

            prompt = f"""
以下の植物差分解析結果をもとに、日本語で詳しい観察日記を書いてください。

差分解析データ:
- 前回の健康状態: {old_health} → 今回: {new_health}
- 健康状態の変化: {health_change}
- 葉の状態変化: {leaf_change}
- 新たに検出された問題: {', '.join(new_issues) if new_issues else 'なし'}
- 解決した問題: {', '.join(resolved) if resolved else 'なし'}
- 継続中の問題: {', '.join(persistent) if persistent else 'なし'}

前回からの変化に注目しながら、植物を世話する人の目線で記辺ってください。
現在の観察、変化の評価、ケアの推奨、下回のケア予定を含めて3～5段落で簡潔にまとめてください。
"""
        else:
            health = analysis_data.get("overall_health", "不明")
            detected = analysis_data.get("detected_objects", [])
            leaf_condition = analysis_data.get("leaf_condition", "不明")

            prompt = f"""
以下の植物解析データをもとに、日本語で詳しい観察日記を書いてください。

解析データ:
- 健康状態: {health}
- 葉の状態: {leaf_condition}
- 検出された問題: {', '.join(detected) if detected else 'なし'}

植物を世話する人の目線で記辺ってください。
現在の観察、健康状態の評価、ケアの推奨、次回のケア予定を含めて3～5段落で簡潔にまとめてください。
"""

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful plant care expert writing observation notes in Japanese.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            raise RuntimeError(
                f"LLM text generation failed. "
                f"Make sure LM Studio is running on {self.api_base}\n"
                f"Error: {str(e)}"
            )


class HybridAnalysisAdapter(ImageAnalysisPort):
    """YOLO + LLMハイブリッド解析アダプター（推奨・精度重視）"""
    
    def __init__(
        self,
        yolo_model: str = "yolov8s-seg.pt",
        llm_api_base: str = "http://localhost:1234/v1",
        llm_model: str = "mistral-7b-instruct",
    ):
        self.yolo = YOLOAdapter(model_name=yolo_model)
        self.llm = LLMTextGeneratorAdapter(
            api_base=llm_api_base,
            model=llm_model,
        )
    
    async def analyze(self, image_path: str) -> dict:
        """YOLOで解析後、詳細情報を取得"""
        # YOLOで画像解析
        result = await self.yolo.analyze(image_path)
        return result


class YOLODifferenceAnalysisAdapter(DifferenceAnalysisPort):
    """YOLO + LLM差分解析アダプター - ふるい画像と新規画像の比較"""
    
    def __init__(
        self,
        yolo_model: str = "yolov8s-seg.pt",
        llm_api_base: str = "http://localhost:1234/v1",
        llm_model: str = "mistral-7b-instruct",
    ):
        """
        初期化
        
        Args:
            yolo_model: YOLOモデル
            llm_api_base: LLM APIベース
            llm_model: LLMモデル
        """
        self.yolo = YOLOAdapter(model_name=yolo_model)
        self.llm = LLMTextGeneratorAdapter(
            api_base=llm_api_base,
            model=llm_model,
        )
    
    async def analyze_difference(
        self,
        old_image_path: str,
        new_image_path: str,
        generate_diary: bool = False,
    ) -> dict:
        """
        ふるい画像（old_image_path）と新規画像（new_image_path）の差分を解析

        画像番号が若い順序（古い画像がふるい画像）
        """
        import numpy as np
        from PIL import Image

        # 両画像をYOLOで解析
        old_result = await self.yolo.analyze(old_image_path)
        new_result = await self.yolo.analyze(new_image_path)
        
        # 画像を読み込み、差分を計算
        old_image = Image.open(old_image_path).convert("RGB")
        new_image = Image.open(new_image_path).convert("RGB")
        
        # 画像サイズが異なる場合は新画像に合わせてリサイズ
        if old_image.size != new_image.size:
            old_image = old_image.resize(new_image.size, Image.Resampling.LANCZOS)
        
        # 画像配列に変換
        old_array = np.array(old_image, dtype=np.float32)
        new_array = np.array(new_image, dtype=np.float32)
        
        # 差分を計算（絶対値）
        diff_array = np.abs(old_array - new_array)
        diff_ratio = np.mean(diff_array) / 255.0  # 0-1に正規化
        
        # 健康状態の変化を判定
        old_health = old_result.get("overall_health", "good")
        new_health = new_result.get("overall_health", "good")
        
        health_change = self._compare_health(old_health, new_health)
        
        # 葉の状態変化を判定
        old_leaf = old_result.get("leaf_condition", "healthy")
        new_leaf = new_result.get("leaf_condition", "healthy")
        
        leaf_change = self._compare_condition(old_leaf, new_leaf)
        
        # 成長の進捗を判定
        old_detected = set(old_result.get("detected_objects", []))
        new_detected = set(new_result.get("detected_objects", []))
        
        new_issues = new_detected - old_detected
        resolved_issues = old_detected - new_detected
        persistent_issues = old_detected & new_detected
        
        growth_progress = self._calculate_growth_progress(
            new_issues, resolved_issues, persistent_issues, diff_ratio
        )
        
        # 信頼度を計算
        old_confidence = old_result.get("confidence_score", 0.7)
        new_confidence = new_result.get("confidence_score", 0.7)
        avg_confidence = (old_confidence + new_confidence) / 2
        
        # 差分レポートを生成
        difference_report = self._generate_difference_report(
            old_result, new_result, new_issues, resolved_issues, persistent_issues
        )

        result = {
            "health_change": health_change,
            "leaf_condition_change": leaf_change,
            "growth_progress": growth_progress,
            "confidence_score": avg_confidence,
            "pixel_difference_ratio": float(diff_ratio),
            "old_health_status": old_health,
            "new_health_status": new_health,
            "old_leaf_condition": old_leaf,
            "new_leaf_condition": new_leaf,
            "new_issues_detected": list(new_issues),
            "resolved_issues": list(resolved_issues),
            "persistent_issues": list(persistent_issues),
            "difference_report": difference_report,
            "old_analysis": old_result,
            "new_analysis": new_result,
            "timestamp": datetime.now().isoformat(),
            "analysis_method": "YOLO v8 Difference Analysis",
            "recommendations": self._generate_recommendations(
                health_change, leaf_change, new_issues
            ),
            "observation_diary": None,
        }

        if generate_diary:
            try:
                result["observation_diary"] = await self.llm.generate(
                    {**result, "is_difference_analysis": True}
                )
            except Exception as e:
                result["observation_diary"] = f"日記生成に失敗しました: {str(e)}"

        return result
    
    def _compare_health(self, old: str, new: str) -> str:
        """健康状態の変化を判定"""
        health_levels = {"excellent": 5, "good": 4, "fair": 3, "poor": 2, "critical": 1}
        
        old_level = health_levels.get(old, 3)
        new_level = health_levels.get(new, 3)
        
        if new_level > old_level:
            return "improved"
        elif new_level < old_level:
            return "declined"
        else:
            return "stable"
    
    def _compare_condition(self, old: str, new: str) -> str:
        """葉の状態変化を判定"""
        condition_levels = {
            "vibrant": 5,
            "healthy": 4,
            "stressed": 3,
            "diseased": 2,
            "wilted": 1,
        }
        
        old_level = condition_levels.get(old, 3)
        new_level = condition_levels.get(new, 3)
        
        if new_level > old_level:
            return "improved"
        elif new_level < old_level:
            return "declined"
        else:
            return "stable"
    
    def _calculate_growth_progress(
        self, new_issues, resolved_issues, persistent_issues, diff_ratio
    ) -> str:
        """成長の進捗を計算"""
        # 新しい問題が出現した場合は「停滞」
        if new_issues:
            return "declined"
        
        # 問題が解決した場合は「向上」
        if resolved_issues and not persistent_issues:
            return "improved"
        
        # 問題が継続する場合は「停滞」
        if persistent_issues:
            return "stable"
        
        # 画像差分が大きい場合は成長の兆候
        if diff_ratio > 0.15:
            return "growing"
        
        # 小さな変化のみ
        return "normal"
    
    def _generate_difference_report(
        self, old_result, new_result, new_issues, resolved_issues, persistent_issues
    ) -> str:
        """差分レポートを生成"""
        report_lines = []
        
        report_lines.append("📊 差分解析レポート")
        report_lines.append("-" * 50)
        
        # ふるい状態
        report_lines.append(f"\n📸 ふるい画像:")
        report_lines.append(f"  健康状態: {old_result.get('overall_health', 'N/A')}")
        report_lines.append(f"  葉の状態: {old_result.get('leaf_condition', 'N/A')}")
        old_detected = old_result.get("detected_objects", [])
        if old_detected:
            report_lines.append(f"  検出項目: {', '.join(old_detected)}")
        
        # 新規状態
        report_lines.append(f"\n🌱 新規画像:")
        report_lines.append(f"  健康状態: {new_result.get('overall_health', 'N/A')}")
        report_lines.append(f"  葉の状態: {new_result.get('leaf_condition', 'N/A')}")
        new_detected = new_result.get("detected_objects", [])
        if new_detected:
            report_lines.append(f"  検出項目: {', '.join(new_detected)}")
        
        # 変化
        report_lines.append(f"\n📈 変化:")
        if new_issues:
            report_lines.append(f"  🆕 新たに検出: {', '.join(new_issues)}")
        if resolved_issues:
            report_lines.append(f"  ✅ 解決した項目: {', '.join(resolved_issues)}")
        if persistent_issues:
            report_lines.append(f"  ⚠️  継続中の項目: {', '.join(persistent_issues)}")
        
        if not new_issues and not resolved_issues and not persistent_issues:
            report_lines.append(f"  特に変化なし（安定状態）")
        
        return "\n".join(report_lines)
    
    def _generate_recommendations(
        self, health_change: str, leaf_change: str, new_issues: set
    ) -> list[str]:
        """推奨事項を生成"""
        recommendations = []
        
        if health_change == "declined":
            recommendations.append("⚠️ 植物の健康状態が低下しています。ケアを強化してください")
            recommendations.append("💧 水やりの頻度と量を見直してください")
            recommendations.append("☀️ 日当たりの条件を確認してください")
        
        if leaf_change == "declined":
            recommendations.append("🍃 葉の状態が悪化しています。病気の可能性を確認してください")
            recommendations.append("🧼 葉を軽く拭いて清潔に保ってください")
        
        if new_issues:
            recommendations.append(f"🔍 新たに以下が検出されました: {', '.join(new_issues)}")
            recommendations.append("早急な対処をお勧めします")
        
        if health_change == "improved":
            recommendations.append("✨ 植物の健康状態が改善しています！")
            recommendations.append("現在のケア方法を継続してください")
        
        if not recommendations:
            recommendations.append("🌱 植物は安定した状態です。定期的な監視を継続してください")
        
        return recommendations
