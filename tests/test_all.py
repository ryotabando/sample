"""
Tests - Unit and Integration Tests
テストコード
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.domain import (
    Plant,
    PlantAnalysisResult,
    PlantDifferenceAnalysisResult,
    HealthStatus,
    LeafCondition,
    AnalyzePlantUseCase,
)
from src.application import (
    AnalysisRequest,
    DifferenceAnalysisRequest,
    AnalysisResponse,
    DifferenceAnalysisResponse,
    PlantAnalysisApplicationService,
)
from src.adapters import (
    MockLVMAdapter,
    MockDiaryAdapter,
    FilePlantRepositoryAdapter,
    FileAnalysisRepositoryAdapter,
)


# ========== Unit Tests ==========

class TestDomain:
    """ドメイン層のテスト"""
    
    def test_plant_creation(self):
        """植物エンティティの作成"""
        plant = Plant(
            id="plant1",
            species="ガジュマル",
            image_path="image.png",
            captured_at=datetime.now(),
        )
        
        assert plant.id == "plant1"
        assert plant.species == "ガジュマル"
    
    def test_plant_validation(self):
        """植物の妥当性確認"""
        with pytest.raises(ValueError):
            Plant(
                id="",
                species="ガジュマル",
                image_path="image.png",
                captured_at=datetime.now(),
            )
    
    def test_analysis_result_creation(self):
        """解析結果の作成"""
        result = PlantAnalysisResult(
            plant_id="plant1",
            overall_health=HealthStatus.GOOD,
            leaf_condition=LeafCondition.HEALTHY,
            growth_stage="mature",
            confidence_score=0.85,
            details={},
        )
        
        assert result.plant_id == "plant1"
        assert result.confidence_score == 0.85
    
    def test_analysis_result_validation(self):
        """解析結果の妥当性確認"""
        with pytest.raises(ValueError):
            PlantAnalysisResult(
                plant_id="plant1",
                overall_health=HealthStatus.GOOD,
                leaf_condition=LeafCondition.HEALTHY,
                growth_stage="mature",
                confidence_score=1.5,  # Invalid
                details={},
            )


class TestAdapters:
    """アダプター層のテスト"""
    
    @pytest.mark.asyncio
    async def test_mock_lvm_adapter(self):
        """モック LVM アダプター"""
        adapter = MockLVMAdapter()
        result = await adapter.analyze("dummy.png")
        
        assert result["overall_health"] == "good"
        assert result["leaf_condition"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_mock_diary_adapter(self):
        """モック日記アダプター"""
        adapter = MockDiaryAdapter()
        diary = await adapter.generate({})
        
        assert "ガジュマル" in diary
    
    @pytest.mark.asyncio
    async def test_file_repository_adapter(self, tmp_path):
        """ファイルリポジトリアダプター"""
        repo = FilePlantRepositoryAdapter(str(tmp_path))
        
        plant = Plant(
            id="test",
            species="ガジュマル",
            image_path="image.png",
            captured_at=datetime.now(),
        )
        
        await repo.save(plant)
        retrieved = await repo.get_by_id("test")
        
        assert retrieved is not None
        assert retrieved.id == "test"


class TestApplicationService:
    """アプリケーションサービスのテスト"""
    
    @pytest.mark.asyncio
    async def test_analyze_plant(self, tmp_path):
        """植物解析"""
        # モックアダプターを使用
        lvm = MockLVMAdapter()
        diary = MockDiaryAdapter()
        plant_repo = FilePlantRepositoryAdapter(str(tmp_path / "plants"))
        analysis_repo = FileAnalysisRepositoryAdapter(str(tmp_path / "analyses"))
        
        # ユースケースとアプリケーションサービスを構成
        use_case = AnalyzePlantUseCase(
            image_analyzer=lvm,
            diary_generator=diary,
            plant_repo=plant_repo,
            analysis_repo=analysis_repo,
        )
        
        app = PlantAnalysisApplicationService(use_case=use_case)
        
        # テスト実行
        request = AnalysisRequest(
            plant_id="test_plant",
            species="ガジュマル",
            image_path="dummy.png",
        )
        
        # Create a dummy image file
        image_file = tmp_path / "dummy.png"
        image_file.write_bytes(b"fake_image_data")
        request.image_path = str(image_file)
        
        response = await app.analyze_plant(request, generate_diary=True)
        
        assert response.plant_id == "test_plant"
        assert response.overall_health == "good"
        assert response.diary is not None


# ========== Integration Tests ==========

class TestIntegration:
    """統合テスト"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """フル ワークフロー テスト"""
        import os
        os.environ["LVM_SERVICE"] = "mock"
        
        from src.container import Container
        
        container = Container()
        
        # Create a dummy image
        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"fake_image")
        
        request = AnalysisRequest(
            plant_id="integration_test",
            species="ガジュマル",
            image_path=str(image_file),
        )
        
        response = await container.plant_analysis_app.analyze_plant(
            request=request,
            generate_diary=True,
        )
        
        assert response.plant_id == "integration_test"
        assert response.confidence_score >= 0
        assert response.diary is not None


class TestDifferenceAnalysis:
    """差分解析テスト"""
    
    def test_difference_analysis_result_creation(self):
        """差分解析結果の作成"""
        from src.domain import PlantDifferenceAnalysisResult
        
        result = PlantDifferenceAnalysisResult(
            plant_id="plant1",
            old_image_path="old.png",
            new_image_path="new.png",
            health_change="improved",
            leaf_condition_change="improved",
            growth_progress="growing",
            confidence_score=0.85,
            details={"pixel_diff": 0.1},
        )
        
        assert result.plant_id == "plant1"
        assert result.health_change == "improved"
        assert result.confidence_score == 0.85
    
    def test_difference_analysis_result_validation(self):
        """差分解析結果の妥当性確認"""
        from src.domain import PlantDifferenceAnalysisResult
        
        # 信頼度が範囲外
        with pytest.raises(ValueError):
            PlantDifferenceAnalysisResult(
                plant_id="plant1",
                old_image_path="old.png",
                new_image_path="new.png",
                health_change="improved",
                leaf_condition_change="improved",
                growth_progress="growing",
                confidence_score=1.5,  # Invalid: > 1
                details={},
            )
    
    @pytest.mark.asyncio
    async def test_yolo_difference_adapter(self):
        """YOLODifferenceAnalysisAdapterテスト"""
        from src.adapters import YOLODifferenceAnalysisAdapter
        
        # Note: This test requires YOLO to be installed
        # and images to exist, so we mock it
        adapter = YOLODifferenceAnalysisAdapter()
        
        # Mock the analyze methods
        adapter.yolo.analyze = AsyncMock(return_value={
            "overall_health": "good",
            "leaf_condition": "healthy",
            "detected_objects": [],
            "confidence_score": 0.8,
        })
        
        result = await adapter.analyze_difference(
            old_image_path="old.png",
            new_image_path="new.png",
        )
        
        assert "health_change" in result
        assert "leaf_condition_change" in result
        assert "growth_progress" in result
        assert "confidence_score" in result
    
    def test_health_comparison(self):
        """健康状態比較テスト"""
        from src.adapters import YOLODifferenceAnalysisAdapter
        
        adapter = YOLODifferenceAnalysisAdapter()
        
        # Test improvement
        change = adapter._compare_health("fair", "good")
        assert change == "improved"
        
        # Test decline
        change = adapter._compare_health("good", "fair")
        assert change == "declined"
        
        # Test stable
        change = adapter._compare_health("good", "good")
        assert change == "stable"
    
    def test_leaf_condition_comparison(self):
        """葉の状態比較テスト"""
        from src.adapters import YOLODifferenceAnalysisAdapter
        
        adapter = YOLODifferenceAnalysisAdapter()
        
        # Test improvement
        change = adapter._compare_condition("stressed", "healthy")
        assert change == "improved"
        
        # Test decline
        change = adapter._compare_condition("healthy", "diseased")
        assert change == "declined"
        
        # Test stable
        change = adapter._compare_condition("healthy", "healthy")
        assert change == "stable"
    
    def test_growth_progress_calculation(self):
        """成長進捗計算テスト"""
        from src.adapters import YOLODifferenceAnalysisAdapter
        
        adapter = YOLODifferenceAnalysisAdapter()
        
        # Test: new issues detected → declined
        progress = adapter._calculate_growth_progress(
            new_issues={"disease"},
            resolved_issues=set(),
            persistent_issues=set(),
            diff_ratio=0.05,
        )
        assert progress == "declined"
        
        # Test: issues resolved → improved
        progress = adapter._calculate_growth_progress(
            new_issues=set(),
            resolved_issues={"pest"},
            persistent_issues=set(),
            diff_ratio=0.05,
        )
        assert progress == "improved"
        
        # Test: high pixel difference → growing
        progress = adapter._calculate_growth_progress(
            new_issues=set(),
            resolved_issues=set(),
            persistent_issues=set(),
            diff_ratio=0.20,
        )
        assert progress == "growing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
