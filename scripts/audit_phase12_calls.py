import json
import os

from dotenv import load_dotenv

load_dotenv()
from langsmith import Client

client = Client()

traces = [
    ("Scenario 1", "01a0aed6-58ca-7032-8a40-636ce0daedbf"),
    ("Scenario 2", "01a0aed8-ef0f-75f2-98a2-588173af7352"),
    ("Scenario 3", "01a0aedc-1ded-7850-aa4b-e03b5169d075"),
]

full_data = {}
for label, tid in traces:
    runs = list(client.list_runs(trace_id=tid))
    runs = sorted(runs, key=lambda r: str(r.start_time or ""))
    llm_runs = [r for r in runs if r.run_type == "llm"]
    full_data[label] = []
    for idx, r in enumerate(llm_runs, 1):
        meta = r.extra.get("metadata", {}) if r.extra else {}
        role = meta.get("role", "unknown")
        model = meta.get("model", r.name)
        in_tok = meta.get("input_tokens") or r.prompt_tokens or 0
        out_tok = meta.get("output_tokens") or r.completion_tokens or 0
        cost = meta.get("provider_reported_cost") or meta.get("internally_estimated_cost") or 0.0
        ttft = meta.get("ttft_seconds")
        dur = meta.get("total_latency_seconds")
        if dur is None and r.end_time and r.start_time:
            dur = (r.end_time - r.start_time).total_seconds()

        out_summary = ""
        if r.outputs:
            if r.outputs.get("tool_calls"):
                tc_names = [
                    tc.get("name") or tc.get("function", {}).get("name", "")
                    for tc in r.outputs["tool_calls"]
                ]
                out_summary = f"Emitted tool_calls: {tc_names}"
            elif r.outputs.get("content"):
                c = str(r.outputs["content"])
                out_summary = c[:80] + "..." if len(c) > 80 else c
            elif r.outputs.get("finish_reason"):
                out_summary = f"finish_reason: {r.outputs.get('finish_reason')}"

        full_data[label].append(
            {
                "index": idx,
                "role": role,
                "model": model,
                "latency_s": round(dur, 2) if dur is not None else None,
                "ttft_s": round(ttft, 2) if ttft is not None else None,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cost": float(cost),
                "summary": out_summary,
            }
        )

os.makedirs("evaluations", exist_ok=True)
with open("evaluations/phase12_llm_call_audit.json", "w", encoding="utf-8") as f:
    json.dump(full_data, f, indent=2)

print("Saved evaluations/phase12_llm_call_audit.json successfully")
