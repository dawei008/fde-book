"""ch15-mcp — stateful MCP server demo for Hesheng overseas tickets.

Exposes 3 tools that share state through a DynamoDB table keyed by
ticket_no, demonstrating cross-session persistence on AgentCore Runtime
stateful MCP.
"""
