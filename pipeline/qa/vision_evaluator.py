import json
from pathlib import Path
from typing import Any


class VisionEvaluator:
    """
    Multimodal Vision QA Judge & Evaluation Harness.
    Audits the 5 calibrated diagnostic passes rendered by TurntableStudio:
    1. beauty_045.png (PBR shaded realism & lighting)
    2. wireframe_clay_045.png (Topology, edge flow, triangle/quad density)
    3. normal_orientation.png (Surface normals & inverted face detection)
    4. uv_checker_045.png (Texel uniformity & UV distortion/pinching)
    5. ao_cavity_045.png (Contact shadows, depth & cavity shading)
    """

    RUBRIC_WEIGHTS = {
        "silhouette_and_anatomy": 0.30,
        "topology_and_edge_flow": 0.25,
        "normal_and_shading_fidelity": 0.20,
        "uv_and_texel_uniformity": 0.15,
        "contact_and_ao_depth": 0.10,
    }

    REQUIRED_PASSES = [
        "beauty_045.png",
        "wireframe_clay_045.png",
        "normal_orientation.png",
        "uv_checker_045.png",
        "ao_cavity_045.png",
    ]

    def __init__(self, renders_dir: str = "output/renders"):
        self.renders_dir = Path(renders_dir)

    def prepare_audit(self, asset_name: str) -> dict[str, Any]:
        """Prepares an asset audit record with all diagnostic passes verified on disk."""
        asset_render_dir = self.renders_dir / asset_name
        available_passes = {}
        for p in self.REQUIRED_PASSES:
            file_path = asset_render_dir / p
            available_passes[p] = {
                "exists": file_path.is_file(),
                "path": str(file_path.resolve()) if file_path.is_file() else None,
            }

        audit_record = {
            "asset_name": asset_name,
            "render_dir": str(asset_render_dir.resolve()),
            "passes": available_passes,
            "all_passes_present": all(v["exists"] for v in available_passes.values()),
            "rubric_weights": self.RUBRIC_WEIGHTS,
            "scores": {k: None for k in self.RUBRIC_WEIGHTS.keys()},
            "overall_score": None,
            "verdict": "pending_multimodal_review",
            "findings": [],
            "remediation_actions": [],
        }
        return audit_record

    def record_evaluation(
        self,
        asset_name: str,
        scores: dict[str, float],
        findings: list[str],
        remediation_actions: list[str] | None = None,
        min_passing_score: float = 0.70,
    ) -> dict[str, Any]:
        """Calculates weighted score, determines pass/fail verdict, and writes vision_qa_report.json."""
        audit_record = self.prepare_audit(asset_name)

        weighted_sum = 0.0
        for metric, weight in self.RUBRIC_WEIGHTS.items():
            score = max(0.0, min(1.0, scores.get(metric, 0.0)))
            audit_record["scores"][metric] = round(score, 3)
            weighted_sum += score * weight

        overall_score = round(weighted_sum, 3)
        audit_record["overall_score"] = overall_score
        audit_record["verdict"] = (
            "PASS"
            if overall_score >= min_passing_score
            and not any("FAIL" in f.upper() or "BLOCKER" in f.upper() for f in findings)
            else "FAIL"
        )
        audit_record["findings"] = findings
        audit_record["remediation_actions"] = remediation_actions or []

        report_path = self.renders_dir / asset_name / "vision_qa_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(audit_record, f, indent=2)

        return audit_record
