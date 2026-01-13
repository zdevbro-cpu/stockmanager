# tools/reportgen/generate_report.py

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List

from docxtpl import DocxTemplate

from report_data_adapter import build_report_data


DEFAULT_TEMPLATE = "docs/templates/project-report-template.TEMPLATE.docx"
DEFAULT_OUTPUT = "out/project-report.docx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Word report from a template and report data."
    )
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, help="Path to .docx template.")
    parser.add_argument("--out", default=DEFAULT_OUTPUT, help="Output .docx path.")

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--data", help="Path to report-data.json (file mode).")
    input_group.add_argument(
        "--source",
        choices=["system"],
        help="Data source (system mode).",
    )

    parser.add_argument("--project_id", help="Project identifier for system mode.")
    parser.add_argument("--asof", help="As-of date for system mode (YYYY-MM-DD).")
    parser.add_argument("--scan-only", action="store_true", help="List template tokens and exit.")
    parser.add_argument(
        "--init-json",
        action="store_true",
        help="Emit a JSON skeleton based on template tokens and exit.",
    )
    return parser.parse_args()


def scan_template_tokens(template_path: Path) -> List[str]:
    doc = DocxTemplate(str(template_path))
    tokens = []
    if hasattr(doc, "get_undeclared_template_variables"):
        try:
            tokens = sorted(doc.get_undeclared_template_variables())
        except Exception as exc:  # pragma: no cover - depends on docxtpl internals
            print(f"[warn] Failed to scan template tokens: {exc}", file=sys.stderr)
    else:  # pragma: no cover - older docxtpl fallback
        print("[warn] Template token scan not supported by this docxtpl version.", file=sys.stderr)
    return tokens


def build_init_json(tokens: Iterable[str]) -> Dict[str, str]:
    return {token: "" for token in sorted(tokens)}


def ensure_missing_tokens(context: Dict[str, object], tokens: Iterable[str]) -> Dict[str, object]:
    updated = dict(context)
    for token in tokens:
        if token in updated:
            continue
        if "." in token:
            parts = token.split(".")
            cursor: Dict[str, object] = updated
            for part in parts[:-1]:
                if part not in cursor or not isinstance(cursor[part], dict):
                    cursor[part] = {}
                cursor = cursor[part]  # type: ignore[assignment]
            if parts[-1] not in cursor:
                print(f"[warn] Missing token '{token}'. Replacing with empty string.", file=sys.stderr)
                cursor[parts[-1]] = ""
            continue
        print(f"[warn] Missing token '{token}'. Replacing with empty string.", file=sys.stderr)
        updated[token] = ""
    return updated


def load_context(args: argparse.Namespace, tokens: Iterable[str]) -> Dict[str, object]:
    if args.data:
        data_path = Path(args.data)
        data = json.loads(data_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Report data JSON must be an object at the top level.")
        return ensure_missing_tokens(data, tokens)

    if args.source == "system":
        if not args.project_id or not args.asof:
            raise ValueError("--project_id and --asof are required for system mode.")
        data = build_report_data(
            source=args.source,
            project_id=args.project_id,
            asof=args.asof,
            template_tokens=list(tokens),
        )
        return ensure_missing_tokens(data, tokens)

    raise ValueError("Either --data or --source system must be provided.")


def main() -> int:
    args = parse_args()
    template_path = Path(args.template)
    out_path = Path(args.out)

    if args.scan_only and args.init_json:
        print("[error] --scan-only and --init-json cannot be used together.", file=sys.stderr)
        return 2

    tokens = scan_template_tokens(template_path)

    if args.scan_only:
        for token in tokens:
            print(token)
        return 0

    if args.init_json:
        skeleton = build_init_json(tokens)
        print(json.dumps(skeleton, indent=2, sort_keys=True))
        return 0

    try:
        context = load_context(args, tokens)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    doc = DocxTemplate(str(template_path))
    doc.render(context)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    print(f"Saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
