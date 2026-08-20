#!/usr/bin/env python3
"""Run the 3080 Brief workflow as a resumable, fail-closed state machine."""

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
STATE_FILE = "run_state.json"
STAGES = [
    "grounded",
    "preflight",
    "review_draft",
    "visual_replay",
    "reader_replay",
    "audit_review",
    "finalized",
]


class ContractError(RuntimeError):
    pass


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path):
    candidate = Path(path)
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_ref(value):
    value = str(value).strip()
    parts = urlsplit(value)
    if parts.scheme and parts.netloc:
        return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), parts.path.rstrip("/"), parts.query, ""))
    try:
        return str(Path(value).expanduser().resolve())
    except OSError:
        return value


def require_file(path, label, minimum_bytes=1):
    candidate = Path(path).expanduser().resolve()
    if not candidate.is_file():
        raise ContractError(f"{label} is missing: {candidate}")
    if candidate.stat().st_size < minimum_bytes:
        raise ContractError(f"{label} is empty or too small: {candidate}")
    return candidate


def artifact(path, label, minimum_bytes=1):
    candidate = require_file(path, label, minimum_bytes)
    return {"path": str(candidate), "sha256": sha256_file(candidate), "bytes": candidate.stat().st_size}


def state_path(run_dir):
    return Path(run_dir).expanduser().resolve() / STATE_FILE


def load_state(run_dir):
    path = state_path(run_dir)
    if not path.is_file():
        raise ContractError(f"run state is missing; initialize first: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8")), path
    except json.JSONDecodeError as exc:
        raise ContractError(f"run state is invalid JSON: {exc}") from exc


def save_state(state, path):
    state["updated_at"] = now_utc()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def clear_from(state, stage):
    index = STAGES.index(stage)
    for name in STAGES[index:]:
        state.get("completed", {}).pop(name, None)
    if index <= STAGES.index("visual_replay"):
        state.pop("review_preparation", None)
    state["status"] = "IN_PROGRESS"
    state["delivery_allowed"] = False


def require_stage(state, stage):
    if stage not in state.get("completed", {}):
        raise ContractError(f"required stage is incomplete: {stage}")


def verify_artifact_record(record, label):
    if not isinstance(record, dict) or not record.get("path") or not record.get("sha256"):
        raise ContractError(f"missing frozen artifact record: {label}")
    candidate = require_file(record["path"], label)
    current = sha256_file(candidate)
    if current != record["sha256"]:
        raise ContractError(f"frozen artifact changed after checkpoint: {label}")
    return candidate


def verify_group(records, labels):
    return {label: verify_artifact_record(records.get(label), label) for label in labels}


def run_script(script, *arguments):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *(str(value) for value in arguments)],
        text=True,
        capture_output=True,
    )
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    if result.returncode != 0:
        raise ContractError(f"{script} failed:\n{output}")
    return output


def current_stage(state):
    completed = state.get("completed", {})
    for stage in reversed(STAGES):
        if stage in completed:
            return stage
    return "initialized"


def next_action(state):
    stage = current_stage(state)
    actions = {
        "initialized": "Fetch the source, create source_before/source_non_appendix/source_inventory/claim_ledger, then run `run_3080.py ground`.",
        "grounded": "Create the draft and visual spec, then run `run_3080.py preflight`.",
        "preflight": "Create the complete review draft in the target format, capture live evidence, then run `run_3080.py record-output`.",
        "review_draft": "Run `run_3080.py record-visual-replay` before review readiness.",
        "visual_replay": "Run `run_3080.py prepare-review`, then run the Primary Blind Reader and `run_3080.py record-reader` before launching the audit.",
        "reader_replay": "Execute the three isolated audit packets, then run `run_3080.py record-review`.",
        "audit_review": "Re-fetch the source and generated output, then run `run_3080.py finalize`.",
        "finalized": "Delivery is allowed; return the generated output reference and delivery_receipt.json summary.",
    }
    return actions[stage]


def print_status(state):
    result = {
        "status": state.get("status"),
        "run_id": state.get("run_id"),
        "profile": state.get("profile"),
        "output_type": state.get("output_type"),
        "current_stage": current_stage(state),
        "delivery_allowed": state.get("delivery_allowed", False),
        "next_action": next_action(state),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def command_init(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / STATE_FILE
    if path.exists():
        raise ContractError(f"run already exists: {path}")
    state = {
        "schema_version": 1,
        "run_id": str(uuid.uuid4()),
        "created_at": now_utc(),
        "updated_at": now_utc(),
        "status": "IN_PROGRESS",
        "delivery_allowed": False,
        "source_ref": args.source_ref,
        "source_type": args.source_type,
        "output_type": args.output_type,
        "profile": args.profile,
        "completed": {},
    }
    save_state(state, path)
    print_status(state)


def command_ground(args):
    state, path = load_state(args.run_dir)
    clear_from(state, "grounded")
    records = {
        "source_before": artifact(args.source_before, "raw source snapshot before generation", 20),
        "source_snapshot": artifact(args.source_snapshot, "normalized non-appendix source snapshot", 20),
        "inventory": artifact(args.inventory, "source inventory", 20),
        "claim_ledger": artifact(args.claim_ledger, "claim ledger", 20),
    }
    run_script("validate_claim_ledger.py", records["claim_ledger"]["path"])
    inventory_text = Path(records["inventory"]["path"]).read_text(encoding="utf-8")
    for required in ("Source language", "Output language", "Output-language basis"):
        if required not in inventory_text:
            raise ContractError(f"source inventory is missing required field: {required}")
    state["completed"]["grounded"] = {"at": now_utc(), "artifacts": records}
    save_state(state, path)
    print_status(state)


def command_preflight(args):
    state, path = load_state(args.run_dir)
    require_stage(state, "grounded")
    grounding = state["completed"]["grounded"]["artifacts"]
    frozen = verify_group(grounding, ("source_before", "source_snapshot", "inventory", "claim_ledger"))
    clear_from(state, "preflight")
    draft = require_file(args.draft, "draft", 20)
    visual_spec = require_file(args.visual_spec, "visual spec", 20)
    run_script("validate_claim_ledger.py", frozen["claim_ledger"])
    if state["output_type"] == "html":
        run_script("validate_brief.py", draft, visual_spec)
    else:
        run_script(
            "preflight_check.py",
            draft,
            "--source-inventory", frozen["inventory"],
            "--claim-ledger", frozen["claim_ledger"],
        )
    run_script(
        "check_expression_quality.py",
        draft,
        "--claim-ledger", frozen["claim_ledger"],
        "--non-appendix-source", frozen["source_snapshot"],
    )
    run_script("check_coverage.py", frozen["claim_ledger"], "--visual-spec", visual_spec)
    run_script("validate_visual_spec.py", visual_spec, frozen["claim_ledger"])
    records = {
        "draft": artifact(draft, "draft", 20),
        "visual_spec": artifact(visual_spec, "visual spec", 20),
    }
    if state["output_type"] == "html":
        if not args.html_design:
            raise ContractError("HTML preflight requires --html-design")
        html_design = require_file(args.html_design, "HTML design plan", 20)
        try:
            from html_design_kit import validate_design_plan

            design_plan = json.loads(html_design.read_text(encoding="utf-8"))
            visual_payload = json.loads(visual_spec.read_text(encoding="utf-8"))
        except (ImportError, json.JSONDecodeError, OSError) as exc:
            raise ContractError(f"HTML design plan is unavailable or invalid: {exc}") from exc
        design_errors = validate_design_plan(design_plan, visual_payload)
        if design_errors:
            raise ContractError("HTML design plan failed:\n" + "\n".join(f"- {item}" for item in design_errors))
        records["html_design"] = artifact(html_design, "HTML design plan", 20)
    if state["output_type"] == "feishu":
        if not args.whiteboard_svg:
            raise ContractError("Feishu preflight requires --whiteboard-svg; a normal image is not a valid substitute")
        whiteboard = require_file(args.whiteboard_svg, "editable whiteboard SVG", 100)
        run_script("validate_whiteboard_svg.py", whiteboard)
        records["whiteboard_svg"] = artifact(whiteboard, "editable whiteboard SVG", 100)
    state["completed"]["preflight"] = {"at": now_utc(), "artifacts": records}
    save_state(state, path)
    print_status(state)


def require_distinct_output(state, output_ref):
    if normalize_ref(state["source_ref"]) == normalize_ref(output_ref):
        raise ContractError("generated output must be distinct from the source")


def validate_feishu_live_evidence(document_snapshot, whiteboard_query, whiteboard_preview, token, block_id):
    document = require_file(document_snapshot, "live generated-document snapshot", 20)
    query = require_file(whiteboard_query, "live whiteboard query response", 20)
    preview = require_file(whiteboard_preview, "live whiteboard preview", 100)
    document_text = document.read_text(encoding="utf-8", errors="ignore")
    query_text = query.read_text(encoding="utf-8", errors="ignore")
    if "whiteboard" not in document_text.casefold():
        raise ContractError("live generated document contains no native whiteboard marker; image/media fallback is not accepted")
    if block_id not in document_text:
        raise ContractError("live generated document does not contain the declared whiteboard block id")
    if token not in query_text:
        raise ContractError("live whiteboard query response does not contain the declared whiteboard token")
    return {
        "live_document": artifact(document, "live generated-document snapshot", 20),
        "whiteboard_query": artifact(query, "live whiteboard query response", 20),
        "whiteboard_preview": artifact(preview, "live whiteboard preview", 100),
    }


def command_record_output(args):
    state, path = load_state(args.run_dir)
    require_stage(state, "preflight")
    grounding = state["completed"]["grounded"]["artifacts"]
    preflight = state["completed"]["preflight"]["artifacts"]
    verify_group(grounding, ("source_before", "source_snapshot", "inventory", "claim_ledger"))
    verify_group(preflight, tuple(preflight))
    require_distinct_output(state, args.output_ref)
    clear_from(state, "review_draft")
    evidence = {}
    if state["output_type"] == "feishu":
        required = {
            "document_snapshot": args.document_snapshot,
            "whiteboard_query": args.whiteboard_query,
            "whiteboard_preview": args.whiteboard_preview,
            "whiteboard_token": args.whiteboard_token,
            "whiteboard_block_id": args.whiteboard_block_id,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ContractError(f"Feishu review draft is missing live evidence: {', '.join(missing)}")
        evidence = validate_feishu_live_evidence(
            args.document_snapshot,
            args.whiteboard_query,
            args.whiteboard_preview,
            args.whiteboard_token,
            args.whiteboard_block_id,
        )
    else:
        output = require_file(args.output_ref, "generated review draft", 20)
        if not args.one_picture_preview:
            raise ContractError("non-Feishu review draft requires --one-picture-preview")
        evidence["output_file"] = artifact(output, "generated review draft", 20)
        evidence["one_picture_preview"] = artifact(
            args.one_picture_preview,
            "cropped one-picture preview",
            100,
        )
        if state["output_type"] == "html":
            run_script(
                "preflight_check.py",
                output,
                "--format", "html",
                "--source-inventory", grounding["inventory"]["path"],
                "--claim-ledger", grounding["claim_ledger"]["path"],
            )
            run_script(
                "validate_html_output.py",
                output,
                "--visual-spec", preflight["visual_spec"]["path"],
                "--design-plan", preflight["html_design"]["path"],
            )
    state["completed"]["review_draft"] = {
        "at": now_utc(),
        "output_ref": args.output_ref,
        "whiteboard_token": args.whiteboard_token or None,
        "whiteboard_block_id": args.whiteboard_block_id or None,
        "artifacts": evidence,
    }
    save_state(state, path)
    print_status(state)


def command_record_visual_replay(args):
    state, path = load_state(args.run_dir)
    require_stage(state, "review_draft")
    grounding = state["completed"]["grounded"]["artifacts"]
    preflight = state["completed"]["preflight"]["artifacts"]
    review_draft = state["completed"]["review_draft"]
    verify_group(grounding, ("claim_ledger",))
    verify_group(preflight, tuple(preflight))
    verify_group(review_draft["artifacts"], tuple(review_draft["artifacts"]))
    preview_record = (
        review_draft["artifacts"].get("whiteboard_preview")
        or review_draft["artifacts"].get("one_picture_preview")
    )
    if not preview_record:
        raise ContractError("cropped one-picture preview is missing")
    clear_from(state, "visual_replay")
    records = {"visual_preview": preview_record}
    if state["profile"] == "fast":
        if not args.fast_self_check:
            raise ContractError("Fast profile requires --fast-self-check and disclosure")
        records["fast_self_check"] = artifact(args.fast_self_check, "Fast visual self-check", 20)
        mode = "self_check"
    else:
        if not args.visual_replay_result:
            raise ContractError("standard/strict profile requires --visual-replay-result")
        result = require_file(args.visual_replay_result, "visual blind replay result", 20)
        run_script(
            "validate_visual_replay.py",
            result,
            "--visual-preview", preview_record["path"],
            "--claim-ledger", grounding["claim_ledger"]["path"],
            "--visual-spec", preflight["visual_spec"]["path"],
        )
        records["visual_replay_result"] = artifact(result, "visual blind replay result", 20)
        mode = "independent"
    state["completed"]["visual_replay"] = {
        "at": now_utc(),
        "mode": mode,
        "artifacts": records,
    }
    save_state(state, path)
    print_status(state)


def prepared_artifact_set_id(state, preparation):
    grounding = state["completed"]["grounded"]["artifacts"]
    preflight = state["completed"]["preflight"]["artifacts"]
    hashes = {
        "source_snapshot": grounding["source_snapshot"]["sha256"],
        "inventory": grounding["inventory"]["sha256"],
        "claim_ledger": grounding["claim_ledger"]["sha256"],
        "tldr": preparation["tldr"]["sha256"],
        "body": preparation["body"]["sha256"],
        "draft": preflight["draft"]["sha256"],
        "visual_spec": preflight["visual_spec"]["sha256"],
        "html_design_plan": preparation.get("html_design_plan", {}).get("sha256"),
        "validation_notes": preparation["validation_notes"]["sha256"],
        "whiteboard_preview": preparation["visual_preview"]["sha256"],
        "document_preview": preparation["document_preview"]["sha256"],
        "source_outline": preparation["source_outline"]["sha256"],
        "source_excerpts": preparation["source_excerpts"]["sha256"],
        "readiness_receipt": preparation["readiness_receipt"]["sha256"],
    }
    hashes = {key: value for key, value in hashes.items() if value}
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode("utf-8")).hexdigest()


def build_prepared_review_packets(state, preparation):
    grounding = state["completed"]["grounded"]["artifacts"]
    preflight = state["completed"]["preflight"]["artifacts"]
    packet_dir = Path(preparation["packet_dir"])
    arguments = [
        "--role", "all",
        "--source-snapshot", grounding["source_snapshot"]["path"],
        "--inventory", grounding["inventory"]["path"],
        "--claim-ledger", grounding["claim_ledger"]["path"],
        "--tldr", preparation["tldr"]["path"],
        "--body", preparation["body"]["path"],
        "--draft", preflight["draft"]["path"],
        "--source-outline", preparation["source_outline"]["path"],
        "--source-excerpts", preparation["source_excerpts"]["path"],
        "--visual-spec", preflight["visual_spec"]["path"],
        "--validation-notes", preparation["validation_notes"]["path"],
        "--whiteboard-preview", preparation["visual_preview"]["path"],
        "--document-preview", preparation["document_preview"]["path"],
        "--readiness-receipt", preparation["readiness_receipt"]["path"],
        "--round", preparation["round"],
        "--output", packet_dir,
    ]
    if preparation.get("user_request"):
        arguments.extend(("--user-request", preparation["user_request"]))
    if preparation.get("whiteboard_summary"):
        arguments.extend(("--whiteboard-summary", preparation["whiteboard_summary"]))
    if preparation.get("html_design_plan"):
        arguments.extend(("--html-design-plan", preparation["html_design_plan"]["path"]))
    run_script("build_review_packet.py", *arguments)
    reader_packet = require_file(packet_dir / "review_packet_reader.md", "reader audit packet", 20)
    marker = "Artifact set ID: `"
    packet_text = reader_packet.read_text(encoding="utf-8")
    packet_id = packet_text.split(marker, 1)[1].split("`", 1)[0]
    if packet_id != preparation["artifact_set_id"]:
        raise ContractError("audit packet artifact set differs from review readiness")
    for role in ("source", "visual"):
        require_file(packet_dir / f"review_packet_{role}.md", f"{role} audit packet", 20)
    preparation["audit_packets_ready"] = True


def command_prepare_review(args):
    state, path = load_state(args.run_dir)
    require_stage(state, "visual_replay")
    grounding = state["completed"]["grounded"]["artifacts"]
    preflight = state["completed"]["preflight"]["artifacts"]
    review_draft = state["completed"]["review_draft"]
    frozen_grounding = verify_group(grounding, ("source_snapshot", "inventory", "claim_ledger"))
    frozen_preflight = verify_group(preflight, tuple(preflight))
    verify_group(review_draft["artifacts"], tuple(review_draft["artifacts"]))
    tldr = require_file(args.tldr or frozen_preflight["draft"], "TLDR review artifact", 20)
    body = require_file(args.body or frozen_preflight["draft"], "body review artifact", 20)
    document_preview = require_file(args.document_preview, "rendered document preview", 100)
    visual_preview_record = (
        review_draft["artifacts"].get("whiteboard_preview")
        or review_draft["artifacts"].get("one_picture_preview")
    )
    visual_preview = verify_artifact_record(visual_preview_record, "one-picture preview")
    validation_notes = require_file(args.validation_notes, "validation notes", 20)
    source_outline = require_file(
        args.source_outline or frozen_grounding["source_snapshot"],
        "non-appendix source outline",
        20,
    )
    source_excerpts = require_file(
        args.source_excerpts or frozen_grounding["source_snapshot"],
        "P0/P1 source excerpts",
        20,
    )
    readiness_receipt = Path(args.run_dir).expanduser().resolve() / f"review_readiness_round_{args.round}.json"
    readiness_arguments = [
        "--source-snapshot", frozen_grounding["source_snapshot"],
        "--inventory", frozen_grounding["inventory"],
        "--claim-ledger", frozen_grounding["claim_ledger"],
        "--tldr", tldr,
        "--body", body,
        "--draft", frozen_preflight["draft"],
        "--source-outline", source_outline,
        "--source-excerpts", source_excerpts,
        "--validation-notes", validation_notes,
        "--document-preview", document_preview,
        "--visual-spec", frozen_preflight["visual_spec"],
        "--visual-preview", visual_preview,
        "--output", readiness_receipt,
    ]
    if frozen_preflight.get("html_design"):
        readiness_arguments.extend(("--html-design-plan", frozen_preflight["html_design"]))
    run_script("validate_review_readiness.py", *readiness_arguments)
    packet_dir = Path(args.run_dir).expanduser().resolve() / f"review_round_{args.round}"
    clear_from(state, "reader_replay")
    state["review_preparation"] = {
        "round": args.round,
        "mode": "self_check" if state["profile"] == "fast" else "independent",
        "tldr": artifact(tldr, "TLDR review artifact", 20),
        "body": artifact(body, "body review artifact", 20),
        "document_preview": artifact(document_preview, "rendered document preview", 100),
        "visual_preview": artifact(visual_preview, "one-picture preview", 100),
        "source_outline": artifact(source_outline, "non-appendix source outline", 20),
        "source_excerpts": artifact(source_excerpts, "P0/P1 source excerpts", 20),
        "readiness_receipt": artifact(readiness_receipt, "review readiness receipt", 20),
        "validation_notes": artifact(validation_notes, "validation notes", 20),
        "packet_dir": str(packet_dir),
        "audit_packets_ready": False,
        "user_request": args.user_request,
        "whiteboard_summary": args.whiteboard_summary,
    }
    if frozen_preflight.get("html_design"):
        state["review_preparation"]["html_design_plan"] = artifact(
            frozen_preflight["html_design"],
            "HTML design plan",
            20,
        )
    artifact_set_id = prepared_artifact_set_id(state, state["review_preparation"])
    state["review_preparation"]["artifact_set_id"] = artifact_set_id
    if state["profile"] == "fast":
        state["completed"]["reader_replay"] = {
            "at": now_utc(),
            "mode": "skipped_fast",
            "artifact_set_id": artifact_set_id,
            "artifacts": {},
        }
        build_prepared_review_packets(state, state["review_preparation"])
    save_state(state, path)
    print(json.dumps(state["review_preparation"], ensure_ascii=False, indent=2))


def validate_blind_reader(path, artifact_set_id, expected_role):
    candidate = require_file(path, f"{expected_role} blind-reader replay", 20)
    try:
        replay = json.loads(candidate.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError(f"{expected_role} blind-reader replay is invalid JSON: {exc}") from exc
    if replay.get("reader_role") != expected_role:
        raise ContractError(f"blind-reader replay must use role: {expected_role}")
    if replay.get("artifact_set_id") != artifact_set_id:
        raise ContractError("blind-reader replay evaluated a different artifact set")
    questions = replay.get("questions")
    if not isinstance(questions, list) or len(questions) != 3:
        raise ContractError(f"{expected_role} blind-reader replay must contain exactly three questions")
    for index, item in enumerate(questions, 1):
        if not isinstance(item, dict) or not item.get("question") or not item.get("answer"):
            raise ContractError(f"blind-reader question {index} is incomplete")
        if not str(item.get("inference_or_uncertainty", "")).strip():
            raise ContractError(f"blind-reader question {index} must state inference or uncertainty")
    return artifact(candidate, f"{expected_role} blind-reader replay", 20)


def command_record_review(args):
    state, path = load_state(args.run_dir)
    require_stage(state, "reader_replay")
    preparation = state.get("review_preparation")
    if not preparation:
        raise ContractError("review packets are missing; run prepare-review first")
    for label in (
        "tldr",
        "body",
        "document_preview",
        "visual_preview",
        "source_outline",
        "source_excerpts",
        "readiness_receipt",
        "validation_notes",
    ):
        verify_artifact_record(preparation[label], label)
    for label in ("html_design_plan",):
        if preparation.get(label):
            verify_artifact_record(preparation[label], label)
    reader_replay = state["completed"]["reader_replay"]
    verify_group(reader_replay["artifacts"], tuple(reader_replay["artifacts"]))
    if reader_replay.get("artifact_set_id") != preparation.get("artifact_set_id"):
        raise ContractError("Blind Reader Replay does not match the prepared artifact set")
    if not preparation.get("audit_packets_ready"):
        raise ContractError("audit packets are not ready; complete Blind Reader Replay first")
    packet_dir = Path(preparation["packet_dir"])
    for role in ("reader", "source", "visual"):
        require_file(packet_dir / f"review_packet_{role}.md", f"{role} audit packet", 20)
    reviews = [
        require_file(args.reader_review, "reader review", 20),
        require_file(args.source_review, "source review", 20),
        require_file(args.visual_review, "visual review", 20),
    ]
    mode = preparation["mode"]
    review_result = Path(args.run_dir).expanduser().resolve() / "review_result.json"
    run_script(
        "aggregate_reviews.py",
        *(str(review) for review in reviews),
        "--output", review_result,
    )
    result = json.loads(review_result.read_text(encoding="utf-8"))
    if result.get("artifact_set_id") != preparation["artifact_set_id"]:
        raise ContractError("review result does not match the prepared artifact set")
    records = {
        "review_result": artifact(review_result, "aggregated review result", 20),
        "reader_review": artifact(reviews[0], "reader review", 20),
        "source_review": artifact(reviews[1], "source review", 20),
        "visual_review": artifact(reviews[2], "visual review", 20),
    }
    clear_from(state, "audit_review")
    state["review_preparation"] = preparation
    state["completed"]["audit_review"] = {
        "at": now_utc(),
        "mode": mode,
        "artifact_set_id": preparation["artifact_set_id"],
        "artifacts": records,
    }
    save_state(state, path)
    print_status(state)


def command_record_reader(args):
    state, path = load_state(args.run_dir)
    require_stage(state, "visual_replay")
    if state["profile"] == "fast":
        raise ContractError("Fast profile skips Blind Reader Replay and records that limitation automatically")
    preparation = state.get("review_preparation")
    if not preparation:
        raise ContractError("review readiness is missing; run prepare-review first")
    for label in (
        "tldr",
        "body",
        "document_preview",
        "visual_preview",
        "source_outline",
        "source_excerpts",
        "readiness_receipt",
        "validation_notes",
    ):
        verify_artifact_record(preparation[label], label)
    for label in ("html_design_plan",):
        if preparation.get(label):
            verify_artifact_record(preparation[label], label)
    if not args.blind_reader_result:
        raise ContractError("standard/strict profile requires --blind-reader-result before audit")
    records = {
        "blind_reader_result": validate_blind_reader(
            args.blind_reader_result,
            preparation["artifact_set_id"],
            "primary",
        )
    }
    if args.blind_reader_escalation == "required":
        if not args.technical_blind_reader_result or not args.decision_blind_reader_result:
            raise ContractError("reader escalation requires both Technical and Decision replay results")
        records["technical_blind_reader_result"] = validate_blind_reader(
            args.technical_blind_reader_result,
            preparation["artifact_set_id"],
            "technical",
        )
        records["decision_blind_reader_result"] = validate_blind_reader(
            args.decision_blind_reader_result,
            preparation["artifact_set_id"],
            "decision",
        )
    clear_from(state, "reader_replay")
    state["completed"]["reader_replay"] = {
        "at": now_utc(),
        "mode": "independent",
        "escalation": args.blind_reader_escalation,
        "artifact_set_id": preparation["artifact_set_id"],
        "artifacts": records,
    }
    build_prepared_review_packets(state, preparation)
    save_state(state, path)
    print_status(state)


def verify_reviewed_set(state):
    grounding = state["completed"]["grounded"]["artifacts"]
    preflight = state["completed"]["preflight"]["artifacts"]
    review_draft = state["completed"]["review_draft"]["artifacts"]
    preparation = state["review_preparation"]
    review = state["completed"]["audit_review"]["artifacts"]
    html_design = preparation.get("html_design_plan", {}).get("path", "")
    validation_notes = preparation.get("validation_notes", {}).get("path", "")
    run_script(
        "verify_reviewed_artifacts.py",
        "--review-result", review["review_result"]["path"],
        "--source-snapshot", grounding["source_snapshot"]["path"],
        "--inventory", grounding["inventory"]["path"],
        "--claim-ledger", grounding["claim_ledger"]["path"],
        "--tldr", preparation["tldr"]["path"],
        "--body", preparation["body"]["path"],
        "--draft", preflight["draft"]["path"],
        "--visual-spec", preflight["visual_spec"]["path"],
        "--html-design-plan", html_design,
        "--validation-notes", validation_notes,
        "--whiteboard-preview", preparation["visual_preview"]["path"],
        "--document-preview", preparation["document_preview"]["path"],
        "--source-outline", preparation["source_outline"]["path"],
        "--source-excerpts", preparation["source_excerpts"]["path"],
        "--readiness-receipt", preparation["readiness_receipt"]["path"],
    )


def command_finalize(args):
    state, path = load_state(args.run_dir)
    require_stage(state, "audit_review")
    grounding = state["completed"]["grounded"]["artifacts"]
    preflight = state["completed"]["preflight"]["artifacts"]
    review_draft = state["completed"]["review_draft"]
    review = state["completed"]["audit_review"]
    reader_replay = state["completed"]["reader_replay"]
    visual_replay = state["completed"]["visual_replay"]
    verify_group(grounding, ("source_before", "source_snapshot", "inventory", "claim_ledger"))
    verify_group(preflight, tuple(preflight))
    verify_group(review["artifacts"], tuple(review["artifacts"]))
    verify_group(reader_replay["artifacts"], tuple(reader_replay["artifacts"]))
    verify_group(visual_replay["artifacts"], tuple(visual_replay["artifacts"]))
    verify_reviewed_set(state)
    source_after = require_file(args.source_after, "raw source snapshot after generation", 20)
    if sha256_file(source_after) != grounding["source_before"]["sha256"]:
        raise ContractError("source changed during generation; final delivery is blocked")
    output_ref = args.output_ref or review_draft["output_ref"]
    if normalize_ref(output_ref) != normalize_ref(review_draft["output_ref"]):
        raise ContractError("final output reference differs from the reviewed draft")
    require_distinct_output(state, output_ref)
    live_records = {}
    if state["output_type"] == "feishu":
        required = (args.final_document_snapshot, args.whiteboard_query, args.whiteboard_preview)
        if not all(required):
            raise ContractError("Feishu finalization requires final document snapshot, whiteboard query, and live preview")
        live_records = validate_feishu_live_evidence(
            args.final_document_snapshot,
            args.whiteboard_query,
            args.whiteboard_preview,
            review_draft["whiteboard_token"],
            review_draft["whiteboard_block_id"],
        )
    else:
        live_records["output_file"] = artifact(output_ref, "final generated output", 20)
    receipt = {
        "schema_version": 1,
        "run_id": state["run_id"],
        "verdict": "PASS",
        "generated_output": output_ref,
        "source": state["source_ref"],
        "output_type": state["output_type"],
        "profile": state["profile"],
        "checks": {
            "source_unchanged": "PASS",
            "output_distinct_and_accessible": "PASS",
            "grounding_frozen": "PASS",
            "deterministic_preflight": "PASS",
            "visual_blind_replay": "PASS" if visual_replay["mode"] == "independent" else "LIMITED",
            "review": "PASS" if review["mode"] == "independent" else "LIMITED",
            "blind_reader_replay": "PASS" if reader_replay["mode"] == "independent" else "NOT_RUN",
            "native_editable_whiteboard": "PASS" if state["output_type"] == "feishu" else "NOT_APPLICABLE",
            "live_output_verification": "PASS",
        },
        "artifact_set_id": review["artifact_set_id"],
        "completed_at": now_utc(),
    }
    receipt_path = Path(args.run_dir).expanduser().resolve() / "delivery_receipt.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    clear_from(state, "finalized")
    state["completed"]["finalized"] = {
        "at": now_utc(),
        "source_after": artifact(source_after, "raw source snapshot after generation", 20),
        "live_artifacts": live_records,
        "delivery_receipt": artifact(receipt_path, "delivery receipt", 20),
    }
    state["status"] = "PASS"
    state["delivery_allowed"] = True
    save_state(state, path)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


def command_status(args):
    state, _ = load_state(args.run_dir)
    if state.get("delivery_allowed"):
        for stage in ("grounded", "preflight", "review_draft", "visual_replay", "reader_replay", "audit_review"):
            records = state.get("completed", {}).get(stage, {}).get("artifacts", {})
            verify_group(records, tuple(records))
        preparation = state.get("review_preparation", {})
        for label in (
            "tldr",
            "body",
            "document_preview",
            "visual_preview",
            "source_outline",
            "source_excerpts",
            "readiness_receipt",
            "validation_notes",
        ):
            verify_artifact_record(preparation.get(label), label)
        for label in ("html_design_plan",):
            if preparation.get(label):
                verify_artifact_record(preparation[label], label)
        finalized = state.get("completed", {}).get("finalized", {})
        verify_artifact_record(finalized.get("source_after"), "source_after")
        verify_artifact_record(finalized.get("delivery_receipt"), "delivery_receipt")
        live_records = finalized.get("live_artifacts", {})
        verify_group(live_records, tuple(live_records))
    print_status(state)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("run_dir")
    init.add_argument("--source-ref", required=True)
    init.add_argument("--source-type", choices=("feishu", "docx", "markdown", "html", "other"), required=True)
    init.add_argument("--output-type", choices=("feishu", "docx", "markdown", "html"), required=True)
    init.add_argument("--profile", choices=("fast", "standard", "strict"), default="standard")
    init.set_defaults(handler=command_init)

    ground = subparsers.add_parser("ground")
    ground.add_argument("run_dir")
    ground.add_argument("--source-before", required=True)
    ground.add_argument("--source-snapshot", required=True)
    ground.add_argument("--inventory", required=True)
    ground.add_argument("--claim-ledger", required=True)
    ground.set_defaults(handler=command_ground)

    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("run_dir")
    preflight.add_argument("--draft", required=True)
    preflight.add_argument("--visual-spec", required=True)
    preflight.add_argument("--whiteboard-svg", default="")
    preflight.add_argument("--html-design", default="")
    preflight.set_defaults(handler=command_preflight)

    output = subparsers.add_parser("record-output")
    output.add_argument("run_dir")
    output.add_argument("--output-ref", required=True)
    output.add_argument("--document-snapshot", default="")
    output.add_argument("--whiteboard-query", default="")
    output.add_argument("--whiteboard-preview", default="")
    output.add_argument("--whiteboard-token", default="")
    output.add_argument("--whiteboard-block-id", default="")
    output.add_argument("--one-picture-preview", default="")
    output.set_defaults(handler=command_record_output)

    visual_replay = subparsers.add_parser("record-visual-replay")
    visual_replay.add_argument("run_dir")
    visual_replay.add_argument("--visual-replay-result", default="")
    visual_replay.add_argument("--fast-self-check", default="")
    visual_replay.set_defaults(handler=command_record_visual_replay)

    prepare = subparsers.add_parser("prepare-review")
    prepare.add_argument("run_dir")
    prepare.add_argument("--tldr", default="")
    prepare.add_argument("--body", default="")
    prepare.add_argument("--user-request", default="")
    prepare.add_argument("--source-outline", default="")
    prepare.add_argument("--source-excerpts", default="")
    prepare.add_argument("--whiteboard-summary", default="")
    prepare.add_argument("--document-preview", required=True)
    prepare.add_argument("--validation-notes", required=True)
    prepare.add_argument("--round", type=int, default=1)
    prepare.set_defaults(handler=command_prepare_review)

    review = subparsers.add_parser("record-review")
    review.add_argument("run_dir")
    review.add_argument("--reader-review", required=True)
    review.add_argument("--source-review", required=True)
    review.add_argument("--visual-review", required=True)
    review.set_defaults(handler=command_record_review)

    reader = subparsers.add_parser("record-reader")
    reader.add_argument("run_dir")
    reader.add_argument("--blind-reader-result", required=True)
    reader.add_argument("--blind-reader-escalation", choices=("none", "required"), default="none")
    reader.add_argument("--technical-blind-reader-result", default="")
    reader.add_argument("--decision-blind-reader-result", default="")
    reader.set_defaults(handler=command_record_reader)

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("run_dir")
    finalize.add_argument("--source-after", required=True)
    finalize.add_argument("--output-ref", default="")
    finalize.add_argument("--final-document-snapshot", default="")
    finalize.add_argument("--whiteboard-query", default="")
    finalize.add_argument("--whiteboard-preview", default="")
    finalize.set_defaults(handler=command_finalize)

    status = subparsers.add_parser("status")
    status.add_argument("run_dir")
    status.set_defaults(handler=command_status)
    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.handler(args)
    except ContractError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
