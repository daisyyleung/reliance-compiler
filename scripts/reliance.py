#!/usr/bin/env python3
"""Command line interface for the Reliance Compiler deterministic control plane."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from reliance_core import compare_packets, compute_plan, evaluate_directory, render_receipt, validate_packet


def _read_json(path: str) -> object:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _dump(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile evidence-bound AI reliance packets")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a reliance packet")
    validate.add_argument("packet")
    validate.add_argument("--policy")

    plan = sub.add_parser("plan", help="recompute a bounded minimum verification set")
    plan.add_argument("packet")

    compare = sub.add_parser("compare", help="compare baseline and candidate packets")
    compare.add_argument("baseline")
    compare.add_argument("candidate")

    evaluate = sub.add_parser("evaluate", help="evaluate fixture records")
    evaluate.add_argument("directory")

    render = sub.add_parser("render", help="render a human-readable reliance receipt")
    render.add_argument("packet")

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            packet = _read_json(args.packet)
            policy = _read_json(args.policy) if args.policy else None
            result = validate_packet(packet, policy if isinstance(policy, dict) else None)
            _dump(result.as_dict())
            return 0 if result.valid else 2
        if args.command == "plan":
            packet = _read_json(args.packet)
            if not isinstance(packet, dict):
                _dump({"error": "packet must be an object"})
                return 2
            validation = validate_packet(packet, packet.get("policy") if isinstance(packet.get("policy"), dict) else None)
            if not validation.valid:
                _dump({"valid": False, "errors": validation.errors, "warnings": validation.warnings})
                return 2
            _dump(compute_plan(packet))
            return 0
        if args.command == "compare":
            baseline = _read_json(args.baseline)
            candidate = _read_json(args.candidate)
            baseline_validation = validate_packet(baseline, baseline.get("policy") if isinstance(baseline, dict) and isinstance(baseline.get("policy"), dict) else None)
            candidate_validation = validate_packet(candidate, candidate.get("policy") if isinstance(candidate, dict) and isinstance(candidate.get("policy"), dict) else None)
            if not baseline_validation.valid or not candidate_validation.valid:
                _dump({"status": "invalid", "errors": baseline_validation.errors + candidate_validation.errors, "scope": "packet_comparison"})
                return 2
            result = compare_packets(baseline, candidate)
            _dump(result)
            return 0 if result.get("status") != "invalid" else 2
        if args.command == "evaluate":
            _dump(evaluate_directory(args.directory))
            return 0
        if args.command == "render":
            packet = _read_json(args.packet)
            if not isinstance(packet, dict):
                print("packet must be an object", file=sys.stderr)
                return 2
            validation = validate_packet(packet, packet.get("policy") if isinstance(packet.get("policy"), dict) else None)
            if not validation.valid:
                _dump({"valid": False, "errors": validation.errors, "warnings": validation.warnings})
                return 2
            print(render_receipt(packet))
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _dump({"error": str(exc)})
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
