"""
Main Application Entry Point
"""

import asyncio
import argparse
import sys
from typing import Optional

from .container import Container
from .application import AnalysisRequest, DifferenceAnalysisRequest
from .adapters import CLIAdapter, JSONPresenter, MarkdownPresenter, ImageLoader


def parse_args():
    """コマンドラインオプションをパース"""
    parser = argparse.ArgumentParser(
        description="Plant Image Analysis using LVM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Analyze command
    analyze = subparsers.add_parser("analyze", help="Analyze plant image")
    analyze.add_argument("--plant-id", required=True, help="Plant identifier")
    analyze.add_argument("--species", required=True, help="Plant species")
    analyze.add_argument("--image", required=True, help="Image path")
    analyze.add_argument("--diary", action="store_true", help="Generate diary")
    analyze.add_argument(
        "--format", choices=["table", "json", "markdown"], default="table"
    )
    
    # Difference Analysis command (差分解析)
    diff = subparsers.add_parser(
        "diff", help="Analyze difference between two plant images (old image, new image)"
    )
    diff.add_argument("--plant-id", required=True, help="Plant identifier")
    diff.add_argument("--species", required=True, help="Plant species")
    diff.add_argument(
        "--old-image", required=True, help="Old/furui image path (reference image)"
    )
    diff.add_argument("--new-image", required=True, help="New image path")
    diff.add_argument("--diary", action="store_true", help="Generate diary")
    diff.add_argument(
        "--format", choices=["table", "json", "markdown"], default="table"
    )
    
    # List command
    list_cmd = subparsers.add_parser("list", help="List analyzed plants")
    list_cmd.add_argument("--format", choices=["table", "json"], default="table")
    
    return parser.parse_args()


async def analyze_plant(args):
    """植物を解析"""
    # 画像の妥当性確認
    if not ImageLoader.validate(args.image):
        print(f"❌ Invalid image: {args.image}")
        sys.exit(1)
    
    # DI コンテナからサービスを取得
    container = Container()
    
    # リクエストを作成
    request = AnalysisRequest(
        plant_id=args.plant_id,
        species=args.species,
        image_path=args.image,
    )
    
    # アプリケーションサービスを実行
    print(f"🔄 Analyzing {args.species}...")
    response = await container.plant_analysis_app.analyze_plant(
        request=request,
        generate_diary=args.diary,
    )
    
    # レスポンスをディクショナリに変換
    response_dict = {
        "plant_id": response.plant_id,
        "overall_health": response.overall_health,
        "leaf_condition": response.leaf_condition,
        "growth_stage": response.growth_stage,
        "confidence_score": response.confidence_score,
        "details": response.details,
    }
    
    if response.diary:
        response_dict["diary"] = {
            "date": response.diary.date,
            "content": response.diary.content,
            "recommendations": response.diary.recommendations,
        }
    
    # 形式に応じて出力
    if args.format == "table":
        CLIAdapter.print_result(response_dict)
    elif args.format == "json":
        print(JSONPresenter.format(response_dict))
    elif args.format == "markdown":
        print(MarkdownPresenter.format(response_dict))


async def difference_analyze_plants(args):
    """2つの画像の差分を解析（ふるい画像と新規画像の比較）"""
    # 画像の妥当性確認
    if not ImageLoader.validate(args.old_image):
        print(f"❌ Invalid old image: {args.old_image}")
        sys.exit(1)
    
    if not ImageLoader.validate(args.new_image):
        print(f"❌ Invalid new image: {args.new_image}")
        sys.exit(1)
    
    # DI コンテナからサービスを取得
    container = Container()
    
    # リクエストを作成
    request = DifferenceAnalysisRequest(
        plant_id=args.plant_id,
        species=args.species,
        old_image_path=args.old_image,
        new_image_path=args.new_image,
    )
    
    # アプリケーションサービスを実行
    print(f"🔄 Analyzing difference for {args.species}...")
    response = await container.plant_analysis_app.analyze_difference(
        request=request,
        difference_adapter=container.difference_analysis_adapter,
        generate_diary=args.diary,
    )
    
    # レスポンスをディクショナリに変換
    response_dict = {
        "plant_id": response.plant_id,
        "old_image": response.old_image_path,
        "new_image": response.new_image_path,
        "health_change": response.health_change,
        "leaf_condition_change": response.leaf_condition_change,
        "growth_progress": response.growth_progress,
        "confidence_score": response.confidence_score,
        "details": response.details,
        "difference_report": response.difference_report,
    }
    
    if response.diary:
        response_dict["diary"] = {
            "date": response.diary.date,
            "content": response.diary.content,
            "recommendations": response.diary.recommendations,
        }
    
    # 形式に応じて出力
    if args.format == "table":
        print_difference_result(response_dict)
    elif args.format == "json":
        print(JSONPresenter.format(response_dict))
    elif args.format == "markdown":
        print(MarkdownPresenter.format(response_dict))


def print_difference_result(response: dict) -> None:
    """差分解析結果を表示"""
    print("\n" + "=" * 70)
    print(f"🌱 Plant Difference Analysis Result")
    print("=" * 70)
    print(f"Plant ID: {response.get('plant_id')}")
    print(f"\n📊 Comparison:")
    print(f"  Old Image (Reference): {response.get('old_image')}")
    print(f"  New Image: {response.get('new_image')}")
    print(f"\n📈 Changes:")
    print(f"  Health Status: {response.get('health_change').upper()}")
    print(f"  Leaf Condition: {response.get('leaf_condition_change').upper()}")
    print(f"  Growth Progress: {response.get('growth_progress')}")
    print(f"  Confidence Score: {response.get('confidence_score'):.1%}")
    
    if response.get("difference_report"):
        print(f"\n{response.get('difference_report')}")
    
    if response.get("diary"):
        print(f"\n📝 Observation Diary:")
        print("-" * 70)
        print(response["diary"]["content"])
        print("-" * 70)
    
    print("=" * 70 + "\n")


async def list_plants(args):
    """解析済み植物の一覧"""
    from pathlib import Path
    
    data_dir = Path("data/plants")
    
    if not data_dir.exists():
        print("📭 No plants recorded yet")
        return
    
    plants = list(data_dir.glob("*.json"))
    
    if not plants:
        print("📭 No plants recorded yet")
        return
    
    if args.format == "table":
        print(f"\n{'Plant ID':<20} {'Species':<20}")
        print("-" * 40)
        for plant_file in plants:
            import json
            with open(plant_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"{data.get('id', 'N/A'):<20} {data.get('species', 'N/A'):<20}")
    else:
        import json
        plants_data = []
        for plant_file in plants:
            with open(plant_file, "r", encoding="utf-8") as f:
                plants_data.append(json.load(f))
        print(json.dumps(plants_data, indent=2, ensure_ascii=False))


async def main():
    """メイン処理"""
    args = parse_args()
    
    if args.command == "analyze":
        await analyze_plant(args)
    elif args.command == "diff":
        await difference_analyze_plants(args)
    elif args.command == "list":
        await list_plants(args)
    else:
        parse_args().print_help()


if __name__ == "__main__":
    asyncio.run(main())
