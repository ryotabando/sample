"""
Tests - Unit and Integration Tests
テストコード
"""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters import (
    FileAnalysisRepositoryAdapter,
    FilePlantRepositoryAdapter,
    MockDiaryAdapter,
    MockLVMAdapter,
)
from src.application import (
    AnalysisRequest,
    AnalysisResponse,
    DifferenceAnalysisRequest,
    DifferenceAnalysisResponse,
    PlantAnalysisApplicationService,
)
from src.domain import (
    AnalyzePlantUseCase,
    HealthStatus,
    LeafCondition,
    Plant,
    PlantAnalysisResult,
    PlantDifferenceAnalysisResult,
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
        """YOLODifferenceAnalysisAdapterテスト - YOLO/LLM/numpy/PILをモック化"""
        import sys

        from src.adapters import YOLODifferenceAnalysisAdapter

        mock_analysis = {
            "overall_health": "good",
            "leaf_condition": "healthy",
            "detected_objects": [],
            "confidence_score": 0.8,
        }

        # numpy モック
        numpy_mock = MagicMock()
        numpy_mock.array.return_value = MagicMock()
        numpy_mock.abs.return_value = MagicMock()
        numpy_mock.mean.return_value = 10.0

        # PIL モック
        img_instance = MagicMock()
        img_instance.size = (100, 100)
        img_instance.convert.return_value = img_instance
        pil_image_mock = MagicMock()
        pil_image_mock.open.return_value = img_instance
        pil_mock = MagicMock()
        pil_mock.Image = pil_image_mock

        with patch("src.adapters.YOLOAdapter.__init__", return_value=None), \
             patch("src.adapters.LLMTextGeneratorAdapter.__init__", return_value=None):
            adapter = YOLODifferenceAnalysisAdapter()
            adapter.yolo = MagicMock()
            adapter.yolo.analyze = AsyncMock(return_value=mock_analysis)
            adapter.llm = MagicMock()

        with patch.dict(sys.modules, {"numpy": numpy_mock, "PIL": pil_mock, "PIL.Image": pil_image_mock}):
            result = await adapter.analyze_difference(
                old_image_path="old.png",
                new_image_path="new.png",
            )

        assert "health_change" in result
        assert "leaf_condition_change" in result
        assert "growth_progress" in result
        assert "confidence_score" in result
    
    def test_health_comparison(self):
        """健康状態比較テスト - __init__ をバイパスして純粋ロジックのみ検証"""
        from src.adapters import YOLODifferenceAnalysisAdapter

        adapter = object.__new__(YOLODifferenceAnalysisAdapter)

        assert adapter._compare_health("fair", "good") == "improved"
        assert adapter._compare_health("good", "fair") == "declined"
        assert adapter._compare_health("good", "good") == "stable"
    
    def test_leaf_condition_comparison(self):
        """葉の状態比較テスト - __init__ をバイパスして純粋ロジックのみ検証"""
        from src.adapters import YOLODifferenceAnalysisAdapter

        adapter = object.__new__(YOLODifferenceAnalysisAdapter)

        assert adapter._compare_condition("stressed", "healthy") == "improved"
        assert adapter._compare_condition("healthy", "diseased") == "declined"
        
        # Test stable
        change = adapter._compare_condition("healthy", "healthy")
        assert change == "stable"
    
    def test_growth_progress_calculation(self):
        """成長進捗計算テスト - __init__ をバイパスして純粋ロジックのみ検証"""
        from src.adapters import YOLODifferenceAnalysisAdapter

        adapter = object.__new__(YOLODifferenceAnalysisAdapter)
        
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
