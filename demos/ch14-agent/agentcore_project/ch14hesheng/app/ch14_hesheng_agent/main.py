"""AgentCore Runtime entrypoint for the Ch14 Hesheng triage agent.

Wraps the Strands agent defined in our local ch14_agent package. The Lambda
ARN for the alarm-code tool is read from an env var (LAMBDA_ARN) injected
at deploy time. Tool source code (ch14_agent + hesheng_core) is vendored
into _vendor/ at deploy time.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_VENDOR = _HERE / "_vendor"
if _VENDOR.exists() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from bedrock_agentcore.runtime import BedrockAgentCoreApp  # noqa: E402

# Tell the vendored hesheng_core where stack-outputs lives inside the bundle.
# config.py looks for `<core_dir>/data/stack-outputs.json` by default; we ship
# the file as `_vendor/hesheng_core/_stack-outputs.json` and patch the path.
from hesheng_core import config as _core_config  # noqa: E402

_CORE_OUT = _VENDOR / "hesheng_core" / "_stack-outputs.json"
if _CORE_OUT.exists():
    _core_config.STACK_OUTPUTS = _CORE_OUT

from ch14_agent.agent import make_strands_agent  # noqa: E402

app = BedrockAgentCoreApp()
log = app.logger

_LAMBDA_ARN = os.environ.get("LAMBDA_ARN", "")
_REGION = os.environ.get("AWS_REGION", "us-east-1")
_agent = None


def get_or_create_agent():
    global _agent
    if _agent is None:
        _agent = make_strands_agent(lambda_arn=_LAMBDA_ARN or None, region=_REGION)
    return _agent


@app.entrypoint
async def invoke(payload, context):
    log.info("ch14 agent invoked")
    agent = get_or_create_agent()
    prompt = payload.get("prompt") if isinstance(payload, dict) else str(payload)
    stream = agent.stream_async(prompt)
    async for event in stream:
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]


if __name__ == "__main__":
    app.run()
