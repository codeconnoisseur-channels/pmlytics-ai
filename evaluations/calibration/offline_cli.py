"""Offline commands for validating and inspecting the product-owned case library."""

import argparse
import json
import re
from pathlib import Path
from typing import Literal

from evaluations.calibration.agreement import compare_audit_sets
from evaluations.calibration.human_review import (
    DEFAULT_REVIEW_PACKETS_PATH,
    compare_human_review_to_catalog,
    create_human_review_working_copy,
    export_human_review_bundle,
    export_human_review_subset,
    save_human_review_submission,
    validate_human_review_form,
)
from evaluations.calibration.loader import load_case_library
from evaluations.calibration.packets import build_evaluation_packet
from evaluations.calibration.schema import AuditRecord


def main() -> None:
    parser = argparse.ArgumentParser(description="PMLytics AI offline evaluation case tools")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="Validate catalog rubric and reference sets")
    packet_parser = subparsers.add_parser(
        "show-packet", help="Print the reviewer-identical packet for one case"
    )
    packet_parser.add_argument("case_id")
    export_parser = subparsers.add_parser(
        "export-human-review",
        help="Create blind packets and a blank human-review worksheet",
    )
    export_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("evaluations/reviews/human_review"),
    )
    subset_parser = subparsers.add_parser(
        "export-review-subset",
        help="Export selected blind packets and a matching blank review worksheet",
    )
    subset_parser.add_argument("--review-case-id", action="append", required=True)
    subset_parser.add_argument("--output-dir", type=Path, required=True)
    start_parser = subparsers.add_parser(
        "start-human-review",
        help="Create a personalized ignored working copy of the review worksheet",
    )
    start_parser.add_argument("--reviewer-id", required=True)
    start_parser.add_argument(
        "--reviewer-type",
        choices=["author", "independent"],
        required=True,
    )
    start_parser.add_argument("--output", type=Path)
    validate_review_parser = subparsers.add_parser(
        "validate-human-review",
        help="Validate a completed human-review worksheet without provider calls",
    )
    validate_review_parser.add_argument("form_path", type=Path)
    validate_review_parser.add_argument("--packet-bundle", type=Path)
    save_review_parser = subparsers.add_parser(
        "save-human-review",
        help="Validate a submitted review and save it into the ignored workspace",
    )
    save_review_parser.add_argument("submission_path", type=Path)
    save_review_parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluations/reviews/workspace/human_review_project_author.csv"),
    )
    save_review_parser.add_argument("--packet-bundle", type=Path)
    compare_review_parser = subparsers.add_parser(
        "compare-human-review",
        help="Compare a validated human review with current product expectations",
    )
    compare_review_parser.add_argument("form_path", type=Path)
    compare_review_parser.add_argument("--output", type=Path)
    compare_review_parser.add_argument("--packet-bundle", type=Path)
    judge_compare_parser = subparsers.add_parser(
        "compare-human-review-to-judge",
        help="Compare an independent human review with cached judge records offline",
    )
    judge_compare_parser.add_argument("form_path", type=Path)
    judge_compare_parser.add_argument("--packet-bundle", type=Path, required=True)
    judge_compare_parser.add_argument("--judge-results", type=Path, required=True)
    judge_compare_parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    library = load_case_library()
    if args.command == "validate":
        print(
            json.dumps(
                {
                    "cases": len(library.cases),
                    "development_cases": len(library.development.case_ids),
                    "held_out_cases": len(library.held_out.case_ids),
                    "held_out_status": library.held_out.status,
                    "rubric_version": library.rubric.rubric_version,
                    "provider_calls": 0,
                },
                indent=2,
            )
        )
        return

    if args.command == "export-human-review":
        packets_path, form_path = export_human_review_bundle(args.output_dir)
        print(
            json.dumps(
                {
                    "review_packets": str(packets_path),
                    "human_review_form": str(form_path),
                    "provider_calls": 0,
                },
                indent=2,
            )
        )
        return

    if args.command == "export-review-subset":
        packets_path, form_path = export_human_review_subset(
            output_dir=args.output_dir,
            review_case_ids=args.review_case_id,
        )
        print(
            json.dumps(
                {
                    "review_packets": str(packets_path),
                    "human_review_form": str(form_path),
                    "review_case_count": len(args.review_case_id),
                    "provider_calls": 0,
                },
                indent=2,
            )
        )
        return

    if args.command == "start-human-review":
        safe_reviewer_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.reviewer_id).strip("_")
        if not safe_reviewer_id:
            raise ValueError("Reviewer ID must contain at least one letter or number")
        output_path = args.output or Path(
            f"evaluations/reviews/workspace/human_review_{safe_reviewer_id}.csv"
        )
        attestation: Literal["author_human_review", "independent_human_review"] = (
            "author_human_review" if args.reviewer_type == "author" else "independent_human_review"
        )
        review_path = create_human_review_working_copy(
            template_path=Path("evaluations/reviews/human_review/human_review_form.csv"),
            output_path=output_path,
            reviewer_id=args.reviewer_id,
            reviewer_attestation=attestation,
        )
        print(
            json.dumps(
                {
                    "working_review_form": str(review_path),
                    "git_ignored": True,
                    "provider_calls": 0,
                },
                indent=2,
            )
        )
        return

    if args.command == "validate-human-review":
        records = validate_human_review_form(
            args.form_path,
            packet_bundle_path=args.packet_bundle or DEFAULT_REVIEW_PACKETS_PATH,
        )
        print(
            json.dumps(
                {
                    "validated_human_reviews": len(records),
                    "provider_calls": 0,
                },
                indent=2,
            )
        )
        return

    if args.command == "save-human-review":
        saved_path = save_human_review_submission(
            submission_path=args.submission_path,
            output_path=args.output,
            packet_bundle_path=args.packet_bundle or DEFAULT_REVIEW_PACKETS_PATH,
        )
        print(
            json.dumps(
                {
                    "saved_human_review": str(saved_path),
                    "validated_human_reviews": len(
                        validate_human_review_form(
                            saved_path,
                            packet_bundle_path=args.packet_bundle or DEFAULT_REVIEW_PACKETS_PATH,
                        )
                    ),
                    "git_ignored": True,
                    "provider_calls": 0,
                },
                indent=2,
            )
        )
        return

    if args.command == "compare-human-review":
        comparison = compare_human_review_to_catalog(
            args.form_path,
            packet_bundle_path=args.packet_bundle or DEFAULT_REVIEW_PACKETS_PATH,
        )
        serialized = json.dumps(comparison, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized + "\n", encoding="utf-8")
        print(serialized)
        return

    if args.command == "compare-human-review-to-judge":
        references = validate_human_review_form(
            args.form_path,
            packet_bundle_path=args.packet_bundle,
        )
        judge_payload = json.loads(args.judge_results.read_text(encoding="utf-8"))
        if not isinstance(judge_payload, dict) or not isinstance(
            judge_payload.get("records"), list
        ):
            raise ValueError("Judge result file must contain a records list")
        judges = [AuditRecord.model_validate(record) for record in judge_payload["records"]]
        report = compare_audit_sets(
            references=references,
            judges=judges,
            library=library,
        )
        serialized = report.model_dump_json(indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized + "\n", encoding="utf-8")
        print(serialized)
        return

    packet = build_evaluation_packet(library, args.case_id)
    print(packet.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
