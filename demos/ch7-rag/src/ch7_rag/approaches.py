"""The three approaches under comparison: prompting / RAG / RAG+rerank."""

from __future__ import annotations

import json
import time

import boto3

GEN_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
RERANK_MODEL = "cohere.rerank-v3-5:0"

SYSTEM_BASE = (
    "你是合昇精密重工海外服务部的工单分诊助手。回答要简短、直接、具体。"
    "如果问题超出已知信息范围, 直接说\"手册中未提及\"或\"无法回答\", 不要编造。"
)

# Custom KB prompt — Bedrock's default RetrieveAndGenerate prompt is over-defensive
# and refuses on mid-range scores. $search_results$ + $query$ are the documented placeholders.
KB_PROMPT = (
    "你是合昇精密重工海外服务部的工单分诊助手。\n"
    "下面是检索到的手册片段:\n$search_results$\n\n"
    "用户问题: $query$\n\n"
    "请基于上述片段直接、简短地回答。如果片段中确实没有答案, 才说\"手册中未提及\"。"
)


def approach_a(br_runtime, question: str) -> dict:
    """Prompting only — no manual context."""
    t0 = time.time()
    r = br_runtime.converse(
        modelId=GEN_MODEL,
        system=[{"text": SYSTEM_BASE}],
        messages=[{"role": "user", "content": [{"text": question}]}],
        inferenceConfig={"maxTokens": 400, "temperature": 0.0},
    )
    latency = (time.time() - t0) * 1000
    text = r["output"]["message"]["content"][0]["text"]
    u = r["usage"]
    return {"text": text, "latency_ms": latency,
            "input_tokens": u["inputTokens"], "output_tokens": u["outputTokens"]}


def approach_b(br_agent_runtime, kb_id: str, question: str, region: str, account: str) -> dict:
    """RAG via Bedrock RetrieveAndGenerate (KB + Claude in one call)."""
    t0 = time.time()
    r = br_agent_runtime.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": kb_id,
                "modelArn": f"arn:aws:bedrock:{region}:{account}:inference-profile/{GEN_MODEL}",
                "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": 5}},
                "generationConfiguration": {
                    "inferenceConfig": {"textInferenceConfig": {"maxTokens": 400, "temperature": 0.0}},
                    "promptTemplate": {"textPromptTemplate": KB_PROMPT},
                },
            },
        },
    )
    latency = (time.time() - t0) * 1000
    text = r["output"]["text"]
    citations = sum(len(c.get("retrievedReferences", [])) for c in r.get("citations", []))
    # RetrieveAndGenerate doesn't report usage; estimate by char count (~3 chars/token for CJK+English mix)
    in_tokens = (len(question) + sum(len(json.dumps(c, ensure_ascii=False)) for c in r.get("citations", []))) // 3
    out_tokens = len(text) // 3
    return {"text": text, "latency_ms": latency,
            "input_tokens": in_tokens, "output_tokens": out_tokens, "citations": citations}


def approach_c(br_agent_runtime, br_runtime, kb_id: str, question: str) -> dict:
    """Retrieve top 10 -> Cohere rerank -> top 3 -> Converse."""
    t0 = time.time()
    raw = br_agent_runtime.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={"text": question},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 10}},
    )
    chunks = [r["content"]["text"] for r in raw["retrievalResults"]]

    if chunks:
        rr = br_runtime.invoke_model(
            modelId=RERANK_MODEL,
            body=json.dumps({"api_version": 2, "query": question,
                             "documents": chunks, "top_n": min(3, len(chunks))}),
        )
        rr_body = json.loads(rr["body"].read())
        top_chunks = [chunks[r["index"]] for r in rr_body["results"]]
    else:
        top_chunks = []

    context = "\n\n---\n\n".join(top_chunks) if top_chunks else "(无相关手册片段)"
    user_msg = (f"参考资料:\n{context}\n\n问题: {question}\n\n"
                f"基于上述资料回答, 资料中没有就说\"手册中未提及\"。")
    g = br_runtime.converse(
        modelId=GEN_MODEL,
        system=[{"text": SYSTEM_BASE}],
        messages=[{"role": "user", "content": [{"text": user_msg}]}],
        inferenceConfig={"maxTokens": 400, "temperature": 0.0},
    )
    latency = (time.time() - t0) * 1000
    text = g["output"]["message"]["content"][0]["text"]
    u = g["usage"]
    return {"text": text, "latency_ms": latency,
            "input_tokens": u["inputTokens"], "output_tokens": u["outputTokens"],
            "retrieved": len(chunks), "reranked": len(top_chunks)}
