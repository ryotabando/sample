"""
Dependency Injection Container
依存関係を注入して各オブジェクトを構成
"""

import os
from .domain import AnalyzePlantUseCase
from .application import PlantAnalysisApplicationService
from .adapters import (
    MockLVMAdapter,
    MockDiaryAdapter,
    FilePlantRepositoryAdapter,
    FileAnalysisRepositoryAdapter,
    LMStudioAdapter,
    YOLOAdapter,
    LLMTextGeneratorAdapter,
    HybridAnalysisAdapter,
    YOLODifferenceAnalysisAdapter,
)


class Container:
    """依存関係注入コンテナ"""
    
    def __init__(self):
        # LVM Service
        lvm_service_type = os.getenv("LVM_SERVICE", "mock")
        
        if lvm_service_type == "mock":
            self.lvm_service = MockLVMAdapter()
        elif lvm_service_type == "openai":
            from .adapters import OpenAIVisionAdapter
            self.lvm_service = OpenAIVisionAdapter()
        elif lvm_service_type == "lm_studio":
            api_base = os.getenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
            model = os.getenv("LM_STUDIO_MODEL", "llava-llama-3-8b-v1_1")
            self.lvm_service = LMStudioAdapter(api_base=api_base, model=model)
        elif lvm_service_type == "yolo_hybrid":
            # YOLO + LLM ハイブリッド（推奨・精度重視）
            yolo_model = os.getenv("YOLO_MODEL", "yolov8s-seg.pt")
            llm_api_base = os.getenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
            llm_model = os.getenv("LLM_MODEL", "mistral-7b-instruct")
            self.lvm_service = HybridAnalysisAdapter(
                yolo_model=yolo_model,
                llm_api_base=llm_api_base,
                llm_model=llm_model,
            )
        else:
            self.lvm_service = MockLVMAdapter()
        
        # Diary Service
        if lvm_service_type == "yolo_hybrid":
            # YOLOの場合、LLMテキスト生成を使用
            llm_api_base = os.getenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
            llm_model = os.getenv("LLM_MODEL", "mistral-7b-instruct")
            self.diary_service = LLMTextGeneratorAdapter(
                api_base=llm_api_base,
                model=llm_model,
            )
        else:
            self.diary_service = MockDiaryAdapter()
        
        # Repositories
        self.plant_repo = FilePlantRepositoryAdapter()
        self.analysis_repo = FileAnalysisRepositoryAdapter()
        
        # Difference Analysis Adapter (差分解析用)
        yolo_model = os.getenv("YOLO_MODEL", "yolov8s-seg.pt")
        llm_api_base = os.getenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
        llm_model = os.getenv("LLM_MODEL", "mistral-7b-instruct")
        self.difference_analysis_adapter = YOLODifferenceAnalysisAdapter(
            yolo_model=yolo_model,
            llm_api_base=llm_api_base,
            llm_model=llm_model,
        )
        
        # Domain Use Case
        self.analyze_plant_use_case = AnalyzePlantUseCase(
            image_analyzer=self.lvm_service,
            diary_generator=self.diary_service,
            plant_repo=self.plant_repo,
            analysis_repo=self.analysis_repo,
        )
        
        # Application Service
        self.plant_analysis_app = PlantAnalysisApplicationService(
            use_case=self.analyze_plant_use_case,
        )
