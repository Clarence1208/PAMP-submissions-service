from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.domains.detection.similarity_detection_service import SimilarityDetectionService
from app.domains.detection.visualization import VisualizationService
from app.domains.tokenization.tokenization_service import TokenizationService

router = APIRouter(prefix="/detection", tags=["detection"])


def get_tokenization_service() -> TokenizationService:
    """Dependency to get tokenization service"""
    return TokenizationService()


@router.get("/similarity-test", response_model=Dict[str, Any])
async def test_project_similarity(tokenization_service: TokenizationService = Depends(get_tokenization_service)):
    """
    Test endpoint that exposes similarity results for the test projects.
    Compares the calculator and game projects and returns detailed similarity analysis.
    """
    try:
        # Initialize services
        similarity_service = SimilarityDetectionService()

        # Define project paths
        calculator_project = Path("resources/test/project_calculator")
        game_project = Path("resources/test/project_game")

        # Check if projects exist
        if not calculator_project.exists():
            raise HTTPException(status_code=404, detail="Calculator project not found")
        if not game_project.exists():
            raise HTTPException(status_code=404, detail="Game project not found")

        # Get all Python files from both projects
        calc_files = list(calculator_project.glob("*.py"))
        game_files = list(game_project.glob("*.py"))

        if not calc_files:
            raise HTTPException(status_code=404, detail="No Python files found in calculator project")
        if not game_files:
            raise HTTPException(status_code=404, detail="No Python files found in game project")

        # Tokenize all files in both projects
        calc_all_tokens = []
        game_all_tokens = []
        calc_all_source = ""
        game_all_source = ""
        calc_file_details = []
        game_file_details = []

        for file_path in calc_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = tokenization_service.tokenize(content, file_path)
            calc_all_tokens.extend(tokens)
            calc_all_source += f"\n# === {file_path.name} ===\n" + content + "\n"
            calc_file_details.append(
                {"filename": file_path.name, "tokens": len(tokens), "lines": len(content.splitlines())}
            )

        for file_path in game_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = tokenization_service.tokenize(content, file_path)
            game_all_tokens.extend(tokens)
            game_all_source += f"\n# === {file_path.name} ===\n" + content + "\n"
            game_file_details.append(
                {"filename": file_path.name, "tokens": len(tokens), "lines": len(content.splitlines())}
            )

        # Project-level similarity analysis
        overall_similarity = similarity_service.compare_similarity(calc_all_tokens, game_all_tokens)
        shared_blocks_result = similarity_service.detect_shared_code_blocks(
            calc_all_tokens, game_all_tokens, calc_all_source, game_all_source, "calculator_project", "game_project"
        )

        # File-by-file analysis
        file_comparisons = []
        for calc_file in calc_files:
            with open(calc_file, "r", encoding="utf-8") as f:
                calc_content = f.read()
            calc_tokens = tokenization_service.tokenize(calc_content, calc_file)

            for game_file in game_files:
                with open(game_file, "r", encoding="utf-8") as f:
                    game_content = f.read()
                game_tokens = tokenization_service.tokenize(game_content, game_file)

                file_similarity = similarity_service.compare_similarity(calc_tokens, game_tokens)
                file_shared = similarity_service.detect_shared_code_blocks(
                    calc_tokens, game_tokens, calc_content, game_content, calc_file.name, game_file.name
                )

                file_comparisons.append(
                    {
                        "calculator_file": calc_file.name,
                        "game_file": game_file.name,
                        "jaccard_similarity": file_similarity["jaccard_similarity"],
                        "type_similarity": file_similarity["type_similarity"],
                        "shared_blocks": file_shared["total_shared_blocks"],
                        "average_shared_similarity": file_shared["average_similarity"]
                        if file_shared["total_shared_blocks"] > 0
                        else 0.0,
                    }
                )

        # Find the best matching file pair
        best_pair = max(file_comparisons, key=lambda x: x["jaccard_similarity"])

        # Build comprehensive response
        response = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "projects": {
                "calculator": {
                    "files": calc_file_details,
                    "total_tokens": len(calc_all_tokens),
                    "total_functions": shared_blocks_result["functions_file1"],
                },
                "game": {
                    "files": game_file_details,
                    "total_tokens": len(game_all_tokens),
                    "total_functions": shared_blocks_result["functions_file2"],
                },
            },
            "overall_similarity": {
                "jaccard_similarity": overall_similarity["jaccard_similarity"],
                "type_similarity": overall_similarity["type_similarity"],
                "common_elements": overall_similarity["common_elements"],
                "total_unique_elements": overall_similarity["total_unique_elements"],
            },
            "shared_code_analysis": {
                "total_shared_blocks": shared_blocks_result["total_shared_blocks"],
                "average_similarity": shared_blocks_result["average_similarity"],
                "shared_blocks": shared_blocks_result["shared_blocks"],
            },
            "file_by_file_analysis": file_comparisons,
            "best_matching_pair": {
                "files": f"{best_pair['calculator_file']} ↔ {best_pair['game_file']}",
                "jaccard_similarity": best_pair["jaccard_similarity"],
                "type_similarity": best_pair["type_similarity"],
                "shared_blocks": best_pair["shared_blocks"],
            },
            "summary": {
                "projects_are_different": overall_similarity["jaccard_similarity"] < 0.5,
                "shared_code_detected": shared_blocks_result["total_shared_blocks"] > 0,
                "high_quality_shared_code": shared_blocks_result["average_similarity"] > 0.8
                if shared_blocks_result["total_shared_blocks"] > 0
                else False,
                "total_file_pairs_analyzed": len(file_comparisons),
            },
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity analysis failed: {str(e)}")


@router.get("/similarity-test/simple", response_model=Dict[str, Any])
async def test_project_similarity_simple(tokenization_service: TokenizationService = Depends(get_tokenization_service)):
    """
    Simplified test endpoint that returns basic similarity metrics for the test projects.
    """
    try:
        # Initialize services
        similarity_service = SimilarityDetectionService()

        # Define project paths
        calculator_project = Path("resources/test/project_calculator")
        game_project = Path("resources/test/project_game")

        # Check if projects exist
        if not calculator_project.exists() or not game_project.exists():
            raise HTTPException(status_code=404, detail="Test projects not found")

        # Get all Python files
        calc_files = list(calculator_project.glob("*.py"))
        game_files = list(game_project.glob("*.py"))

        if not calc_files or not game_files:
            raise HTTPException(status_code=404, detail="No Python files found in projects")

        # Tokenize all files
        calc_all_tokens = []
        game_all_tokens = []
        calc_all_source = ""
        game_all_source = ""

        for file_path in calc_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = tokenization_service.tokenize(content, file_path)
            calc_all_tokens.extend(tokens)
            calc_all_source += content + "\n"

        for file_path in game_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tokens = tokenization_service.tokenize(content, file_path)
            game_all_tokens.extend(tokens)
            game_all_source += content + "\n"

        # Analyze similarity
        overall_similarity = similarity_service.compare_similarity(calc_all_tokens, game_all_tokens)
        shared_blocks_result = similarity_service.detect_shared_code_blocks(
            calc_all_tokens, game_all_tokens, calc_all_source, game_all_source, "calculator_project", "game_project"
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "calculator_tokens": len(calc_all_tokens),
            "game_tokens": len(game_all_tokens),
            "jaccard_similarity": overall_similarity["jaccard_similarity"],
            "type_similarity": overall_similarity["type_similarity"],
            "shared_blocks": shared_blocks_result["total_shared_blocks"],
            "average_shared_similarity": shared_blocks_result["average_similarity"],
            "are_projects_similar": overall_similarity["jaccard_similarity"] > 0.3,
            "has_shared_code": shared_blocks_result["total_shared_blocks"] > 0,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/similarity-test/files/{file1}/{file2}")
async def compare_specific_files(file1: str, file2: str):
    """
    Compare two specific files from the test projects.

    Args:
        file1: Filename from calculator project (e.g., "main.py")
        file2: Filename from game project (e.g., "game_engine.py")
    """
    try:
        # Initialize services
        tokenization_service = TokenizationService()
        similarity_service = SimilarityDetectionService()

        # Define file paths
        calc_file_path = Path("resources/test/project_calculator") / file1
        game_file_path = Path("resources/test/project_game") / file2

        # Check if files exist
        if not calc_file_path.exists():
            raise HTTPException(status_code=404, detail=f"Calculator file '{file1}' not found")
        if not game_file_path.exists():
            raise HTTPException(status_code=404, detail=f"Game file '{file2}' not found")

        # Load and tokenize files
        with open(calc_file_path, "r", encoding="utf-8") as f:
            calc_content = f.read()
        with open(game_file_path, "r", encoding="utf-8") as f:
            game_content = f.read()

        calc_tokens = tokenization_service.tokenize(calc_content, calc_file_path)
        game_tokens = tokenization_service.tokenize(game_content, game_file_path)

        # Analyze similarity
        similarity = similarity_service.compare_similarity(calc_tokens, game_tokens)
        shared_blocks = similarity_service.detect_shared_code_blocks(
            calc_tokens, game_tokens, calc_content, game_content, file1, file2
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "files": {"calculator": file1, "game": file2},
            "tokens": {"calculator": len(calc_tokens), "game": len(game_tokens)},
            "similarity": {
                "jaccard": similarity["jaccard_similarity"],
                "type": similarity["type_similarity"],
                "common_elements": similarity["common_elements"],
                "total_unique_elements": similarity["total_unique_elements"],
            },
            "shared_code": {
                "blocks_detected": shared_blocks["total_shared_blocks"],
                "average_similarity": shared_blocks["average_similarity"],
                "functions_calc": shared_blocks["functions_file1"],
                "functions_game": shared_blocks["functions_file2"],
                "shared_blocks": shared_blocks["shared_blocks"],
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File comparison failed: {str(e)}")


@router.get("/react-flow-ast/files/{file1}/{file2}")
async def get_react_flow_ast_for_files(file1: str, file2: str):
    """
    Get optimized React Flow AST representation for two specific files.
    Returns streamlined structure with complete source code content for comparison.

    Args:
        file1: Filename from calculator project (e.g., "main.py")
        file2: Filename from game project (e.g., "game_engine.py")
    """
    try:
        # Initialize services
        tokenization_service = TokenizationService()
        visualization_service = VisualizationService()

        # Define file paths
        calc_file_path = Path("resources/test/project_calculator") / file1
        game_file_path = Path("resources/test/project_game") / file2

        # Check if files exist
        if not calc_file_path.exists():
            raise HTTPException(status_code=404, detail=f"Calculator file '{file1}' not found")
        if not game_file_path.exists():
            raise HTTPException(status_code=404, detail=f"Game file '{file2}' not found")

        # Load and tokenize files
        with open(calc_file_path, "r", encoding="utf-8") as f:
            calc_content = f.read()
        with open(game_file_path, "r", encoding="utf-8") as f:
            game_content = f.read()

        calc_tokens = tokenization_service.tokenize(calc_content, calc_file_path)
        game_tokens = tokenization_service.tokenize(game_content, game_file_path)

        # Generate optimized React Flow AST
        react_flow_data = visualization_service.generate_react_flow_ast(
            calc_tokens, game_tokens, calc_content, game_content, file1, file2, "elk"
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "files_compared": {"file1": file1, "file2": file2},
            "layout_used": "elk_layered",
            "react_flow": react_flow_data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"React Flow AST generation failed: {str(e)}")


@router.get("/react-flow-ast/projects")
async def get_react_flow_ast_for_projects():
    """
    Get optimized React Flow AST representation for the test projects.
    Returns streamlined data structure with essential visualization data and complete source code content.
    Uses ELK layout algorithm for consistent rendering.
    """
    try:
        # Initialize services
        tokenization_service = TokenizationService()
        visualization_service = VisualizationService()

        # Define project paths
        calculator_project = Path("resources/test/project_calculator")
        game_project = Path("resources/test/project_game")

        # Check if projects exist
        if not calculator_project.exists() or not game_project.exists():
            raise HTTPException(status_code=404, detail="Test projects not found")

        # Get all Python files
        calc_files = list(calculator_project.glob("*.py"))
        game_files = list(game_project.glob("*.py"))

        if not calc_files or not game_files:
            raise HTTPException(status_code=404, detail="No Python files found in projects")

        # Analyze all file pairs and collect those with similarities
        files_with_similarities = []

        for calc_file in calc_files:
            with open(calc_file, "r", encoding="utf-8") as f:
                calc_content = f.read()
            calc_tokens = tokenization_service.tokenize(calc_content, calc_file)

            for game_file in game_files:
                with open(game_file, "r", encoding="utf-8") as f:
                    game_content = f.read()
                game_tokens = tokenization_service.tokenize(game_content, game_file)

                # Generate optimized React Flow AST for this pair
                react_flow_data = visualization_service.generate_react_flow_ast(
                    calc_tokens,
                    game_tokens,
                    calc_content,
                    game_content,
                    calc_file.name,
                    game_file.name,
                    "elk",  # Always use ELK
                )

                # Only include if similarities were detected
                if react_flow_data.get("has_similarity", False):
                    files_with_similarities.append(
                        {
                            "file_pair": {"calculator_file": calc_file.name, "game_file": game_file.name},
                            "react_flow": react_flow_data,
                        }
                    )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_file_pairs_with_similarity": len(files_with_similarities),
            "layout_used": "elk_layered",
            "file_pairs": files_with_similarities,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project React Flow AST generation failed: {str(e)}")


@router.get("/react-flow-ast/projects/combined")
async def get_combined_react_flow_ast_for_projects(layout: str = "elk"):
    """
    Get a combined React Flow AST representation showing all files with similarities in one view.

    Args:
        layout: Layout type - "elk", "dagre", "hierarchical", "force", "circular", or "manual" (default: "elk")
    """
    try:
        # Initialize services
        tokenization_service = TokenizationService()
        visualization_service = VisualizationService()

        # Define project paths
        calculator_project = Path("resources/test/project_calculator")
        game_project = Path("resources/test/project_game")

        # Check if projects exist
        if not calculator_project.exists() or not game_project.exists():
            raise HTTPException(status_code=404, detail="Test projects not found")

        # Get all Python files
        calc_files = list(calculator_project.glob("*.py"))
        game_files = list(game_project.glob("*.py"))

        if not calc_files or not game_files:
            raise HTTPException(status_code=404, detail="No Python files found in projects")

        # Combine all nodes and edges from files with similarities
        all_nodes = []
        all_edges = []
        x_offset = 0
        y_offset = 0

        files_with_similarities = []

        for calc_file in calc_files:
            with open(calc_file, "r", encoding="utf-8") as f:
                calc_content = f.read()
            calc_tokens = tokenization_service.tokenize(calc_content, calc_file)

            for game_file in game_files:
                with open(game_file, "r", encoding="utf-8") as f:
                    game_content = f.read()
                game_tokens = tokenization_service.tokenize(game_content, game_file)

                # Generate React Flow AST for this pair with layout
                react_flow_data = visualization_service.generate_react_flow_ast(
                    calc_tokens, game_tokens, calc_content, game_content, calc_file.name, game_file.name, layout
                )

                # Only include if similarities were detected
                if react_flow_data.get("has_similarity", False):
                    # Adjust positions to avoid overlap
                    for node in react_flow_data["nodes"]:
                        node["position"]["x"] += x_offset
                        node["position"]["y"] += y_offset
                        # Update node IDs to be unique
                        node["id"] = f"pair_{len(files_with_similarities)}_{node['id']}"

                    # Update edge IDs and references
                    for edge in react_flow_data["edges"]:
                        edge["id"] = f"pair_{len(files_with_similarities)}_{edge['id']}"
                        edge["source"] = f"pair_{len(files_with_similarities)}_{edge['source']}"
                        edge["target"] = f"pair_{len(files_with_similarities)}_{edge['target']}"

                    all_nodes.extend(react_flow_data["nodes"])
                    all_edges.extend(react_flow_data["edges"])

                    files_with_similarities.append(
                        {
                            "calculator_file": calc_file.name,
                            "game_file": game_file.name,
                            "shared_blocks": react_flow_data.get("shared_blocks_count", 0),
                            "average_similarity": react_flow_data.get("average_similarity", 0),
                        }
                    )

                    # Move to next position based on layout
                    if layout == "hierarchical":
                        y_offset += 800  # Space between file pairs vertically
                    elif layout == "force":
                        y_offset += 600
                    elif layout == "circular":
                        x_offset += 800  # Space between pairs horizontally
                    else:
                        y_offset += 700

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_file_pairs_with_similarity": len(files_with_similarities),
            "files_analyzed": files_with_similarities,
            "layout_used": layout,
            "react_flow": {
                "nodes": all_nodes,
                "edges": all_edges,
                "has_similarity": len(all_nodes) > 0,
                "total_nodes": len(all_nodes),
                "total_edges": len(all_edges),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Combined React Flow AST generation failed: {str(e)}")


@router.get("/react-flow-ast/files/{file1}/{file2}/animated")
async def get_animated_react_flow_ast_for_files(file1: str, file2: str, layout: str = "elk"):
    """
    Get React Flow AST with enhanced animation settings and layout configuration.

    Args:
        file1: Filename from calculator project (e.g., "main.py")
        file2: Filename from game project (e.g., "game_engine.py")
        layout: Layout type - "elk", "dagre", "hierarchical", "force", "circular", or "manual" (default: "elk")
    """
    try:
        # Get the regular React Flow data with layout
        regular_response = await get_react_flow_ast_for_files(file1, file2, layout)
        react_flow_data = regular_response["react_flow"]

        # Enhanced animation configuration based on layout
        layout_configs = {
            "hierarchical": {
                "viewport": {"x": 0, "y": 0, "zoom": 0.7},
                "fitView": True,
                "defaultEdgeOptions": {"animated": True},
                "snapToGrid": True,
                "snapGrid": [20, 20],
            },
            "force": {
                "viewport": {"x": 0, "y": 0, "zoom": 0.8},
                "fitView": True,
                "defaultEdgeOptions": {"animated": True},
                "connectionMode": "loose",
            },
            "circular": {
                "viewport": {"x": 0, "y": 0, "zoom": 0.9},
                "fitView": True,
                "defaultEdgeOptions": {"animated": True},
                "snapToGrid": True,
                "snapGrid": [15, 15],
            },
            "manual": {
                "viewport": {"x": 0, "y": 0, "zoom": 0.6},
                "fitView": True,
                "defaultEdgeOptions": {"animated": True},
                "connectionMode": "strict",
            },
        }

        enhanced_config = layout_configs.get(layout, layout_configs["hierarchical"])

        # Add animation metadata to edges
        for edge in react_flow_data.get("edges", []):
            if edge.get("animated"):
                edge["markerEnd"] = {"type": "arrowclosed", "color": edge.get("style", {}).get("stroke", "#666")}

                # Add pulse animation for similarity edges
                if edge.get("data", {}).get("type") == "similarity":
                    edge["className"] = "similarity-edge-animated"
                    edge["style"]["animation"] = "pulse 2s infinite"

                # Add flow animation for function calls
                elif edge.get("data", {}).get("type") == "function_call":
                    edge["className"] = "function-call-edge-animated"
                    edge["style"]["animation"] = "dash 3s linear infinite"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "files_compared": {"file1": file1, "file2": file2},
            "layout_used": layout,
            "react_flow": react_flow_data,
            "animation_config": enhanced_config,
            "css_animations": {
                f".{layout}-layout": {"transition": "all 0.3s ease-in-out"},
                ".similarity-edge-animated": {"animation": "pulse 2s infinite"},
                ".function-call-edge-animated": {"animation": "dash 3s linear infinite"},
                "@keyframes pulse": {"0%": {"opacity": "1"}, "50%": {"opacity": "0.6"}, "100%": {"opacity": "1"}},
                "@keyframes dash": {"0%": {"stroke-dashoffset": "0"}, "100%": {"stroke-dashoffset": "20"}},
            },
            "layout_specific_tips": {
                "hierarchical": "Best viewed with zoom 0.7, shows clear code hierarchy",
                "force": "Natural clustering, may need adjustment after initial render",
                "circular": "Compact view, good for small codebases",
                "manual": "Fixed positions, reliable for presentations",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Animated React Flow AST generation failed: {str(e)}")
