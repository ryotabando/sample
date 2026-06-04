"""
Application Layer - Use Case Orchestration
アプリケーション層は外部ポート（アダプター）を調整
"""

from dataclasses import dataclass
from typing import Optional
from .domain import AnalyzePlantUseCase, PlantAnalysisResult


@dataclass
class AnalysisRequest:
    """解析リクエストDTO"""
    plant_id: str
    species: str
    image_path: str
    metadata: Optional[dict] = None


@dataclass
class DifferenceAnalysisRequest:
    """差分解析リクエストDTO - 複数画像比較"""
    plant_id: str
    species: str
    old_image_path: str
    new_image_path: str
    metadata: Optional[dict] = None


@dataclass
class DiaryEntry:
    """日記エントリDTO"""
    date: str
    content: str
    recommendations: list[str]


@dataclass
class AnalysisResponse:
    """解析レスポンスDTO"""
    plant_id: str
    overall_health: str
    leaf_condition: str
    growth_stage: str
    confidence_score: float
    details: dict
    diary: Optional[DiaryEntry] = None


@dataclass
class DifferenceAnalysisResponse:
    """差分解析レスポンスDTO"""
    plant_id: str
    old_image_path: str
    new_image_path: str
    health_change: str  # "improved", "stable", "declined", "critical"
    leaf_condition_change: str  # "improved", "stable", "declined"
    growth_progress: str  # 成長の進捗
    confidence_score: float
    details: dict
    difference_report: Optional[str] = None
    diary: Optional[DiaryEntry] = None


class PlantAnalysisApplicationService:
    """植物解析アプリケーションサービス"""
    
    def __init__(self, use_case: AnalyzePlantUseCase):
        self.use_case = use_case
    
    async def analyze_plant(
        self,
        request: AnalysisRequest,
        generate_diary: bool = False,
    ) -> AnalysisResponse:
        """
        植物を解析するアプリケーションサービス
        """
        # ユースケース実行
        domain_result: PlantAnalysisResult = await self.use_case.execute(
            plant_id=request.plant_id,
            species=request.species,
            image_path=request.image_path,
            generate_diary=generate_diary,
        )
        
        # DTOに変換して返す
        diary_dto = None
        if domain_result.observation_diary:
            diary_dto = DiaryEntry(
                date=domain_result.details.get("timestamp", ""),
                content=domain_result.observation_diary,
                recommendations=domain_result.details.get("recommendations", []),
            )
        
        return AnalysisResponse(
            plant_id=domain_result.plant_id,
            overall_health=domain_result.overall_health.value,
            leaf_condition=domain_result.leaf_condition.value,
            growth_stage=domain_result.growth_stage,
            confidence_score=domain_result.confidence_score,
            details=domain_result.details,
            diary=diary_dto,
        )
    
    async def analyze_difference(
        self,
        request: DifferenceAnalysisRequest,
        difference_adapter,
        generate_diary: bool = False,
    ) -> DifferenceAnalysisResponse:
        """
        2つの画像の差分を解析
        """
        # 差分解析アダプターを実行
        diff_result = await difference_adapter.analyze_difference(
            old_image_path=request.old_image_path,
            new_image_path=request.new_image_path,
        )
        
        # DTOに変換して返す
        diary_dto = None
        if generate_diary and diff_result.get("observation_diary"):
            diary_dto = DiaryEntry(
                date=diff_result.get("timestamp", ""),
                content=diff_result.get("observation_diary", ""),
                recommendations=diff_result.get("recommendations", []),
            )
        
        return DifferenceAnalysisResponse(
            plant_id=request.plant_id,
            old_image_path=request.old_image_path,
            new_image_path=request.new_image_path,
            health_change=diff_result.get("health_change", "stable"),
            leaf_condition_change=diff_result.get("leaf_condition_change", "stable"),
            growth_progress=diff_result.get("growth_progress", "normal"),
            confidence_score=diff_result.get("confidence_score", 0.7),
            details=diff_result,
            difference_report=diff_result.get("difference_report"),
            diary=diary_dto,
        )
