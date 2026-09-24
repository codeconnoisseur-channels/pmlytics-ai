import asyncio
import json

import httpx


async def main():
    query = "Why did checkout conversion drop for Android users this week?"
    print(f"Creating investigation through Next.js proxy: {query}")

    async with httpx.AsyncClient(timeout=180.0) as client:
        # 1. POST through frontend proxy
        post_resp = await client.post(
            "http://localhost:3000/api/v1/investigations",
            json={"user_query": query},
        )
        print(f"POST response: {post_resp.status_code} {post_resp.text}")
        if post_resp.status_code != 202:
            print("Failed to create investigation")
            return

        data = post_resp.json()
        inv_id = data["investigation_id"]
        print(f"Created Investigation ID: {inv_id}")

        # 2. Track SSE stream through frontend proxy
        events_url = f"http://localhost:3000/api/v1/investigations/{inv_id}/events"
        print(f"Connecting to SSE stream at {events_url}...")

        lifecycle_events = []
        is_completed = False

        try:
            async with client.stream("GET", events_url, timeout=180.0) as response:
                print(f"SSE stream connected: HTTP {response.status_code}")
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        payload_str = line[5:].strip()
                        try:
                            event_data = json.loads(payload_str)
                            lifecycle_events.append(event_data)
                            stage = event_data.get("stage") or event_data.get("status")
                            agent = event_data.get("active_agent")
                            msg = event_data.get("message")
                            elapsed = event_data.get("elapsed_seconds")
                            print(f"  [{elapsed}s] Stage: {stage} | Agent: {agent} | Msg: {msg}")

                            if (
                                event_data.get("status") == "completed"
                                or event_data.get("event") == "complete"
                            ):
                                is_completed = True
                                break
                            elif (
                                event_data.get("status") == "failed"
                                or event_data.get("event") == "failed"
                            ):
                                print(f"Investigation failed: {event_data.get('error')}")
                                break
                        except json.JSONDecodeError:
                            print(f"Raw SSE line: {line}")
        except Exception as e:
            print(f"SSE stream closed or error: {e}")

        # 3. Check status if not completed via SSE
        if not is_completed:
            print("Polling status for completion...")
            for _ in range(30):
                status_resp = await client.get(
                    f"http://localhost:3000/api/v1/investigations/{inv_id}"
                )
                status_data = status_resp.json()
                print(f"Poll status: {status_data.get('status')}")
                if status_data.get("status") == "completed":
                    is_completed = True
                    break
                elif status_data.get("status") == "failed":
                    print(f"Investigation failed: {status_data.get('error')}")
                    break
                await asyncio.sleep(3)

        # 4. Retrieve synthesized result from frontend proxy
        result_resp = await client.get(
            f"http://localhost:3000/api/v1/investigations/{inv_id}/result"
        )
        print(f"GET result response code: {result_resp.status_code}")
        if result_resp.status_code == 200:
            result_data = result_resp.json()
            rec = result_data.get("recommendation", {})
            evidence = result_data.get("evidence_ledger", {})
            critic = result_data.get("critic_review", {})

            print("\n================ LIVE INVESTIGATION REPORT ================")
            print(f"Investigation ID: {result_data.get('investigation_id')}")
            print(f"User Query: {result_data.get('user_query')}")
            print(f"Status: {result_data.get('status')}")
            print(f"Duration: {result_data.get('duration_seconds')}s")
            print(f"LLM Calls: {result_data.get('telemetry_summary', {}).get('llm_calls')}")
            print(f"Evidence Count: {len(evidence)}")
            print(f"Recommendation Type: {rec.get('recommendation_type')}")
            print(f"Confidence: {rec.get('confidence')}")
            print(f"Problem Statement: {rec.get('problem_statement')}")
            print(f"Recommendation: {rec.get('recommendation')}")
            print(f"Critic Decision: {critic.get('status')}")
            print(f"Total Lifecycle Events Logged: {len(lifecycle_events)}")
            print("===========================================================\n")

            # Save report to a JSON file for inspection
            with open("scripts/live_investigation_result.json", "w") as f:
                json.dump(
                    {
                        "investigation_id": inv_id,
                        "query": query,
                        "lifecycle_events": lifecycle_events,
                        "result": result_data,
                    },
                    f,
                    indent=2,
                )
                print("Saved scripts/live_investigation_result.json")


if __name__ == "__main__":
    asyncio.run(main())
