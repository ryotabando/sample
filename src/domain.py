"""
Domain Layer - Core Business Logic
ドメイン層は外部フレームワークに依存しない純粋なビジネスロジック
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

# === Value Objects ===

class HealthStatus(Enum):
    """植物の健康状態"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class LeafCondition(Enum):
    """葉の状態"""
    VIBRANT = "vibrant"
    HEALTHY = "healthy"
    STRESSED = "stressed"
    DISEASED = "diseased"
    WILTED = "wilted"


@dataclass
class PlantAnalysisResult:
    """植物解析結果 - Value Object"""
    plant_id: str
    overall_health: HealthStatus
    leaf_condition: LeafCondition
    growth_stage: str
    confidence_score: float
    details: dict
    observation_diary: Optional[str] = None
    
    def __post_init__(self):
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("confidence_score must be between 0 and 1")


@dataclass
class PlantDifferenceAnalysisResult:
    """植物差分解析結果 - ふるい画像と新規画像の比較"""
    plant_id: str
    old_image_path: str
    new_image_path: str
    health_change: str  # "improved", "stable", "declined", "critical"
    leaf_condition_change: str  # "improved", "stable", "declined"
    growth_progress: str  # 成長の進捗度合い
    confidence_score: float  # 差分検出の信頼度
    details: dict  # 差分の詳細情報
    difference_report: Optional[str] = None  # 差分レポート
    observation_diary: Optional[str] = None  # 観察日記
    
    def __post_init__(self):
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("confidence_score must be between 0 and 1")


# === Entities ===

@dataclass
class Plant:
    """植物エンティティ"""
    id: str
    species: str
    image_path: str
    captured_at: datetime
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("Plant id cannot be empty")
        if not self.species:
            raise ValueError("species cannot be empty")


# === Port Interfaces ===

class ImageAnalysisPort:
    """LVMを使用した画像解析ポート（アウトバウンド）"""
    
    async def analyze(self, image_path: str) -> dict:
        raise NotImplementedError


class DiaryGenerationPort:
    """観察日記生成ポート（アウトバウンド）"""
    
    async def generate(self, analysis_data: dict) -> str:
        raise NotImplementedError


class PlantRepositoryPort:
    """植物リポジトリポート（アウトバウンド）"""
    
    async def save(self, plant: Plant) -> None:
        raise NotImplementedError
    
    async def get_by_id(self, plant_id: str) -> Optional[Plant]:
        raise NotImplementedError


class AnalysisRepositoryPort:
    """解析結果リポジトリポート（アウトバウンド）"""
    
    async def save(self, result: PlantAnalysisResult) -> None:
        raise NotImplementedError
    
    async def get_latest(self, plant_id: str) -> Optional[PlantAnalysisResult]:
        raise NotImplementedError


class DifferenceAnalysisPort:
    """差分解析ポート（アウトバウンド）"""

    async def analyze_difference(
        self,
        old_image_path: str,
        new_image_path: str,
        generate_diary: bool = False,
    ) -> dict:
        """2つの画像の差分を解析"""
        raise NotImplementedError


# === Use Cases (Domain Services) ===

class AnalyzePlantUseCase:
    """植物解析ユースケース - ドメイン層のビジネスロジック"""
    
    def __init__(
        self,
        image_analyzer: ImageAnalysisPort,
        diary_generator: Optional[DiaryGenerationPort] = None,
        plant_repo: Optional[PlantRepositoryPort] = None,
        analysis_repo: Optional[AnalysisRepositoryPort] = None,
    ):
        self.image_analyzer = image_analyzer
        self.diary_generator = diary_generator
        self.plant_repo = plant_repo
        self.analysis_repo = analysis_repo
    
    async def execute(
        self,
        plant_id: str,
        species: str,
        image_path: str,
        generate_diary: bool = False,
    ) -> PlantAnalysisResult:
        """
        植物解析を実行
        """
        # 1. エンティティ作成
        plant = Plant(
            id=plant_id,
            species=species,
            image_path=image_path,
            captured_at=datetime.now(),
        )
        
        # 2. 植物を保存
        if self.plant_repo:
            await self.plant_repo.save(plant)
        
        # 3. 画像解析
        analysis_data = await self.image_analyzer.analyze(image_path)
        
        # 4. 結果をValue Objectに変換
        try:
            health_status = HealthStatus(analysis_data.get("overall_health", "fair"))
        except ValueError:
            health_status = HealthStatus.FAIR

        try:
            leaf_condition = LeafCondition(analysis_data.get("leaf_condition", "stressed"))
        except ValueError:
            leaf_condition = LeafCondition.STRESSED

        result = PlantAnalysisResult(
            plant_id=plant_id,
            overall_health=health_status,
            leaf_condition=leaf_condition,
            growth_stage=analysis_data.get("growth_stage", "unknown"),
            confidence_score=analysis_data.get("confidence_score", 0.0),
            details=analysis_data,
        )
        
        # 5. 日記生成
        if generate_diary and self.diary_generator:
            diary = await self.diary_generator.generate(analysis_data)
            result.observation_diary = diary
        
        # 6. 結果を保存
        if self.analysis_repo:
            await self.analysis_repo.save(result)
        
        return result
