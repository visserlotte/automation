import time

from ai_helpers.ai_utils import gpt, last_msgs
from ai_helpers.master_ai_config import PROJECT


def process_large_task(prompt, project=PROJECT):
    chunk_size = 25000
    responses = []

    for i in range(0, len(prompt), chunk_size):
        chunk = prompt[i : i + chunk_size]
        try:
            response = gpt(chunk, last_msgs(project))
            responses.append(response)
            time.sleep(2)
        except Exception as e:
            responses.append(f"❌ Error processing chunk: {e}")

    return "\n".join(responses)
