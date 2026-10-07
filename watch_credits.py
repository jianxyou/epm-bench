#!/usr/bin/env python3
"""Probe API credits every 30 min; if available, fire the LLM pilot once."""
import subprocess
import time

KEY = open("/Users/jianxin/Desktop/my_project/.anthropic_key").read().strip()


def probe():
    try:
        import anthropic
        c = anthropic.Anthropic(api_key=KEY)
        c.messages.create(model="claude-haiku-4-5-20251001", max_tokens=1,
                          messages=[{"role": "user", "content": "hi"}])
        return True
    except Exception as e:
        if "credit" in str(e).lower():
            return False
        print("probe error:", str(e)[:120], flush=True)
        return False


for i in range(20):  # ~10 hours
    if probe():
        print("CREDITS AVAILABLE — launching llm_pilot.sh", flush=True)
        subprocess.run(["bash", "llm_pilot.sh"])
        print("LLM_PILOT_FINISHED", flush=True)
        break
    print(f"probe {i+1}: still exhausted", flush=True)
    time.sleep(1800)
print("watcher exit", flush=True)
