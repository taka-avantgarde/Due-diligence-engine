"""Zero-Dependency Standards-Compliant JSON-RPC 2.0 stdio MCP Server.

Provides a Model Context Protocol (MCP) server for Due Diligence Engine,
enabling AI coding assistants (Claude Code, Cursor, Codex, Gemini, Antigravity)
to autonomously run institutional-grade software due diligence audits.
"""

from __future__ import annotations

import contextlib
import json
import math
import sys
from typing import Any

import due_diligence_engine
from due_diligence_engine.models import ConsultingReport
from due_diligence_engine.prompt.generator import (
    _ATLAS_FOUR_AXIS_INSTRUCTIONS_EN,
    DIMENSIONS_EN,
    DIMENSIONS_JA,
)

SUPPORTED_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[0]

# Tool names mapped to internal API functions
TOOL_DISPATCH_MAP: dict[str, str] = {
    "dde_prepare_audit": "prepare_audit",
    "dde_list_evidence": "list_evidence",
    "dde_read_evidence": "read_evidence",
    "dde_verify_sites": "verify_sites",
    "dde_validate_report": "validate_report",
    "dde_render_report": "render_report",
    "dde_close_audit": "close_audit",
}

# 7 Native DDE MCP Tools
MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "dde_prepare_audit",
        "description": "Initialize a technical due diligence audit session on a target repository, local path, or zip archive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target git URL (https://github.com/...), shorthand (owner/repo), local path, or zip file.",
                },
                "name": {
                    "type": "string",
                    "description": "Optional project name (auto-detected if omitted).",
                },
                "lang": {
                    "type": "string",
                    "description": "Evaluation language code (en, ja, es, fr, de, ar, etc.). Default: 'en'.",
                    "default": "en",
                },
                "stage": {
                    "type": "string",
                    "description": "Company stage: seed, series_a, series_b, or growth. Default: 'series_a'.",
                    "default": "series_a",
                },
                "skip_git": {
                    "type": "boolean",
                    "description": "Skip git forensics history analysis. Default: False.",
                    "default": False,
                },
            },
            "required": ["target"],
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    },
    {
        "name": "dde_list_evidence",
        "description": "List extracted files, AST metrics, and evidence catalog for an active audit session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audit_id": {
                    "type": "string",
                    "description": "Active audit session ID returned by dde_prepare_audit.",
                },
                "offset": {
                    "type": "integer",
                    "description": "Pagination offset (0-based). Default: 0.",
                    "default": 0,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of evidence files to return. Default: 100.",
                    "default": 100,
                },
            },
            "required": ["audit_id"],
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "dde_read_evidence",
        "description": "Read file contents or specific lines from the audited codebase evidence snapshot.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audit_id": {
                    "type": "string",
                    "description": "Active audit session ID.",
                },
                "file_id": {
                    "type": "string",
                    "description": "Opaque file_id returned by dde_list_evidence; raw paths are rejected.",
                },
                "start_line": {
                    "type": "integer",
                    "description": "1-based starting line number. Default: 1.",
                    "default": 1,
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to return. Default: 200.",
                    "default": 200,
                },
            },
            "required": ["audit_id", "file_id"],
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "dde_verify_sites",
        "description": "Verify external domains, live product endpoints, and claims with SSRF pinning and security checks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audit_id": {
                    "type": "string",
                    "description": "Active audit session ID.",
                },
                "urls": {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                    "description": "Optional public URLs to verify. Omitted or empty URLs return an empty result.",
                },
                "use_ai": {
                    "type": "boolean", "default": False,
                    "description": "Explicitly enable paid external AI scoring; default is heuristic only.",
                },
            },
            "required": ["audit_id"],
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    },
    {
        "name": "dde_validate_report",
        "description": "Validate AI-generated ConsultingReport JSON against schema, invariant rubrics, and snapshot hash.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audit_id": {
                    "type": "string",
                    "description": "Active audit session ID.",
                },
                "snapshot_sha256": {
                    "type": "string",
                    "description": "SHA-256 snapshot checksum returned by dde_prepare_audit.",
                },
                "report": {
                    "type": "object",
                    "description": "AI-generated ConsultingReport JSON object adhering to dde://schemas/consulting/v1.",
                },
            },
            "required": ["audit_id", "snapshot_sha256", "report"],
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "dde_render_report",
        "description": "Render a validated consulting report into a PDF.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audit_id": {
                    "type": "string",
                    "description": "Active audit session ID.",
                },
                "validation_id": {
                    "type": "string",
                    "description": "Validation ID returned by dde_validate_report.",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Optional directory to save rendered deliverables (default: cwd/dde_output).",
                },
                "lang": {
                    "type": "string",
                    "description": "Report delivery language code (en, ja, es, fr, de, ar, etc.). Default: 'en'.",
                    "default": "en",
                },
            },
            "required": ["audit_id", "validation_id"],
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "dde_close_audit",
        "description": "Close audit session, execute DoD 5220.22-M 3-pass cryptographic wipe, and generate Purge Certificate.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audit_id": {
                    "type": "string",
                    "description": "Active audit session ID to securely purge.",
                },
            },
            "required": ["audit_id"],
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    },
]

# MCP Resources
MCP_RESOURCES: list[dict[str, Any]] = [
    {
        "uri": "dde://schemas/consulting/v1",
        "name": "Consulting Report JSON Schema & Field Guide",
        "description": "JSON schema and structural field guide for 5-dimension consulting report.",
        "mimeType": "application/json",
    },
    {
        "uri": "dde://rubrics/technical-5/v1",
        "name": "5-Dimension Technical Rubric",
        "description": "Core 5-dimension scoring rubric (20% each: originality, advancement, depth, architecture, consistency).",
        "mimeType": "application/json",
    },
    {
        "uri": "dde://rubrics/atlas-4/v1",
        "name": "Atlas 4-Axis Supplementary Rubric",
        "description": "Atlas Associates 4-axis philosophy rubric: performance (20%), stability (20%), lightweight (5%), security (55% with 5 sub-items).",
        "mimeType": "application/json",
    },
]

# MCP Prompts
MCP_PROMPTS: list[dict[str, Any]] = [
    {
        "name": "dde-audit",
        "description": "End-to-end autonomous technical due diligence audit workflow prompt for AI coding agents.",
        "arguments": [
            {
                "name": "target",
                "description": "Target repository path, URL, or zip archive to audit.",
                "required": True,
            },
            {
                "name": "lang",
                "description": "Report language (en, ja, es, fr, de, ar, etc.). Default: 'en'.",
                "required": False,
            },
            {
                "name": "stage",
                "description": "Company stage: seed, series_a, series_b, or growth. Default: 'series_a'.",
                "required": False,
            },
        ],
    }
]


def _get_consulting_schema_data() -> dict[str, Any]:
    """Return JSON schema and field guide for ConsultingReport."""
    schema = ConsultingReport.model_json_schema()
    return {
        "title": "Due Diligence Engine Consulting Report Schema v1",
        "version": due_diligence_engine.__version__,
        "field_guide": {
            "dimensions": "5 core dimensions at 20% each (technical_originality, technology_advancement, implementation_depth, architecture_quality, claim_consistency)",
            "swot": "2x2 SWOT analysis matrix (strengths, weaknesses, opportunities, threats)",
            "future_outlook": "3-year projected trajectory and technical risk assessment",
            "strategic_advice": "Actionable recommendations prioritized across immediate, medium, and long term",
            "investment_thesis": "Institutional investment recommendation, valuation impact, and key caveats",
            "red_flags": "Code-verified architectural, security, license, or falsification defects with line snippets",
            "site_verification": "Live domain inspection, SSL/TLS posture, header security, and marketing claim verification",
            "competitive_analysis": "6-market x 7-chart radar/position matrix relative to verified competitors",
            "competitor_rationales": "Explicit rationale for each competitor included in the benchmark",
            "implementation_matrix": "Industry-tailored matrix of technical capabilities vs. industry peers",
            "atlas_four_axis": "Atlas Associates philosophy assessment: performance (20%), stability (20%), lightweight (5%), security (55%)",
            "data_freshness": "Timestamped verification audit trail and consulted evidence sources",
        },
        "json_schema": schema,
    }


def _get_technical_5_rubric_data() -> dict[str, Any]:
    """Return 5-dimension technical rubric."""
    return {
        "title": "DDE 5-Dimension Technical Rubric (20% each)",
        "rubric_version": "1.0",
        "dimensions": DIMENSIONS_EN,
        "dimensions_ja": DIMENSIONS_JA,
        "scoring_scale": {
            "1-2": "Critical deficiency / Toy prototype / High false claims",
            "3-4": "Early prototype / Basic boilerplate / Significant gaps",
            "5-6": "Standard production readiness / Typical industry baseline",
            "7-8": "Enterprise hardened / Advanced engineering / High transparency",
            "9-10": "Frontier grade / Paradigm-shifting originality / Mission-critical",
        },
    }


def _get_atlas_4_rubric_data() -> dict[str, Any]:
    """Return Atlas 4-axis supplementary rubric."""
    return {
        "title": "Atlas Associates 4-Axis Supplementary Rubric",
        "version": "2.0",
        "philosophy": "We judge the code, not the badge. Third-party certifications are reference-only; code implementation is scored.",
        "axes": [
            {
                "key": "performance",
                "name_en": "Performance",
                "name_ja": "高速化",
                "weight_pct": 20,
                "scope": "Algorithmic efficiency, async/parallel, connection pooling, multi-layer caching, DB query optimization",
            },
            {
                "key": "stability",
                "name_en": "Stability",
                "name_ja": "安定化",
                "weight_pct": 20,
                "scope": "Error handling depth, circuit breakers, graceful degradation, observability, deployment safety, test coverage",
            },
            {
                "key": "lightweight",
                "name_en": "Lightweight",
                "name_ja": "軽量化",
                "weight_pct": 5,
                "scope": "Bundle size, memory footprint, dependency minimalism, bandwidth efficiency, container image hygiene",
            },
            {
                "key": "security",
                "name_en": "Security Strength",
                "name_ja": "セキュリティ強度",
                "weight_pct": 55,
                "scope": "Cryptographic depth, privacy implementation, communication safety, defense-in-depth architecture",
                "sub_items": [
                    {
                        "key": "encryption",
                        "name_en": "Cryptographic Sophistication",
                        "name_ja": "暗号化技術の高度さ",
                        "weight_pct": 35,
                        "description": "Signal Protocol, PQXDH, ML-KEM-1024, AEAD everywhere, no self-rolled crypto.",
                    },
                    {
                        "key": "privacy",
                        "name_en": "Privacy Protection",
                        "name_ja": "プライバシー保護",
                        "weight_pct": 8,
                        "description": "Code-level privacy controls, data minimization, deletion cascades, PII isolation.",
                    },
                    {
                        "key": "posture",
                        "name_en": "Basic Hygiene (MFA/WebAuthn)",
                        "name_ja": "基本衛生（MFA・WebAuthn）",
                        "weight_pct": 2,
                        "description": "Auth flow, rate limiting, dependency auditing hooks in code (certifications are un-scored).",
                    },
                    {
                        "key": "comms",
                        "name_en": "Communication Safety",
                        "name_ja": "通信の安全",
                        "weight_pct": 7,
                        "description": "TLS 1.3, Certificate Pinning, Sealed Sender, mTLS, side-channel defense.",
                    },
                    {
                        "key": "layers",
                        "name_en": "Layer Composition",
                        "name_ja": "レイヤー構成",
                        "weight_pct": 3,
                        "description": "Defense-in-depth, VPC/subnet boundary isolation, fail-secure defaults, TEE/enclave computing.",
                    },
                ],
            },
        ],
        "full_text_guidance": _ATLAS_FOUR_AXIS_INSTRUCTIONS_EN,
    }


def _get_audit_prompt_text(target: str, lang: str = "en", stage: str = "series-a") -> str:
    """Return autonomous audit instruction prompt for AI coding agents."""
    stage = stage.replace("-", "_")
    return f"""You are conducting an autonomous technical due diligence audit on:
Target: {target}
Language: {lang}
Stage: {stage}

Please follow the strict DDE autonomous audit workflow using the DDE MCP tools:

1. **Initialize Audit Session**:
   Call `dde_prepare_audit(target="{target}", lang="{lang}", stage="{stage}")`.
   Record the returned `audit_id` and `snapshot_sha256`.

2. **Inspect Evidence & Architecture**:
   Call `dde_list_evidence(audit_id=...)` to discover key source files, AST metrics, and dependencies.
   Call `dde_read_evidence(audit_id=..., file_id=...)` to inspect critical entrypoints, security routines, database queries, and algorithms.

3. **Verify Public Endpoints & Claims**:
   Call `dde_verify_sites(audit_id=...)` to test public endpoints, SSL/TLS posture, and cross-validate site claims against actual code.

4. **Formulate & Validate Consulting Report**:
   Consult `dde://schemas/consulting/v1`, `dde://rubrics/technical-5/v1`, and `dde://rubrics/atlas-4/v1`.
   Synthesize a comprehensive `ConsultingReport` JSON matching the schema (5 dimensions at 20% each, SWOT, future outlook, strategic advice, investment thesis, code-verified red flags, competitive analysis, competitor rationales, implementation matrix, and Atlas 4-axis assessment).
   Call `dde_validate_report(audit_id=..., snapshot_sha256=..., report=...)`.
   If validation reports any errors, fix the JSON and re-validate.

5. **Render Deliverables**:
   Call `dde_render_report(audit_id=..., validation_id=..., lang="{lang}")` to produce an institutional PDF.

6. **Close & Cryptographically Wipe Audit Session**:
   Call `dde_close_audit(audit_id=...)` to run DoD 5220.22-M 3-pass data wipe and generate an ECDSA P-256 Purge Certificate.

Begin by calling `dde_prepare_audit`.
"""


class MCPServer:
    """Zero-dependency standards-compliant JSON-RPC 2.0 stdio MCP Server for DDE."""

    def __init__(self, api_module: Any | None = None) -> None:
        """Initialize MCP server with optional API module override for testing."""
        self.api_module = api_module
        self._protocol_version: str = PROTOCOL_VERSION

    def _get_api(self) -> Any:
        """Lazily load due_diligence_engine.api if not injected."""
        if self.api_module is not None:
            return self.api_module
        from due_diligence_engine import api
        return api

    @staticmethod
    def _serialize(obj: Any) -> Any:
        """Recursively serialize Pydantic models, dataclasses, and custom objects to dict."""
        if obj is None:
            return None
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode="json")
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if isinstance(obj, (int, float, str, bool)):
            return obj
        if isinstance(obj, (list, tuple)):
            return [MCPServer._serialize(item) for item in obj]
        if isinstance(obj, dict):
            return {k: MCPServer._serialize(v) for k, v in obj.items()}
        if hasattr(obj, "__dict__"):
            return {
                k: MCPServer._serialize(v)
                for k, v in obj.__dict__.items()
                if not k.startswith("_")
            }
        return str(obj)

    @staticmethod
    def _error(req_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def handle_mcp_message(self, msg: Any) -> Any:
        """Validate envelopes and handle batches, including null request IDs."""
        if isinstance(msg, list):
            if not msg:
                return self._error(None, -32600, "Invalid Request: empty batch")
            responses = [self.handle_mcp_message(item) if not isinstance(item, list)
                         else self._error(None, -32600, "Invalid Request") for item in msg]
            return [r for r in responses if r is not None] or None
        if not isinstance(msg, dict):
            return self._error(None, -32600, "Invalid Request: expected object")
        req_id = msg.get("id")
        valid_id = (req_id is None or isinstance(req_id, str) or
                    (type(req_id) is int or (type(req_id) is float and math.isfinite(req_id))))
        if (msg.get("jsonrpc") != "2.0" or not isinstance(msg.get("method"), str)
                or not msg["method"] or not valid_id):
            return self._error(req_id if valid_id else None, -32600, "Invalid Request")
        notification = "id" not in msg
        params = msg.get("params")
        if params is not None and not isinstance(params, dict):
            return None if notification else self._error(req_id, -32602, "Invalid Params: expected object or null")
        response = self._handle_request(req_id, msg["method"], params or {})
        return None if notification else response

    @staticmethod
    def _valid_argument(value: Any, schema: dict[str, Any]) -> bool:
        expected = schema.get("type")
        types = expected if isinstance(expected, list) else [expected]
        checks = {
            "string": lambda: isinstance(value, str),
            "integer": lambda: type(value) is int,
            "boolean": lambda: type(value) is bool,
            "object": lambda: isinstance(value, dict),
            "array": lambda: isinstance(value, list) and all(
                MCPServer._valid_argument(v, schema.get("items", {})) for v in value),
            "null": lambda: value is None,
        }
        return any(checks[t]() for t in types if t in checks)

    def _handle_request(self, req_id: Any, method: str, params: dict[str, Any]) -> dict[str, Any]:
        # Protocol methods
        if method == "initialize":
            client_version = params.get("protocolVersion")
            chosen_version = client_version if client_version in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION
            self._protocol_version = chosen_version
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": chosen_version,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": "due-diligence-engine",
                        "version": due_diligence_engine.__version__,
                    },
                },
            }

        if method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            }

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": MCP_TOOLS,
                },
            }

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if not isinstance(tool_name, str) or not isinstance(arguments, dict):
                return self._error(req_id, -32602, "Invalid Params: name and object arguments required")

            if not tool_name or tool_name not in TOOL_DISPATCH_MAP:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: '{tool_name}'",
                    },
                }

            schema = next(t["inputSchema"] for t in MCP_TOOLS if t["name"] == tool_name)
            if any(k not in arguments for k in schema.get("required", [])):
                return self._error(req_id, -32602, "Invalid Params: missing required tool argument")
            for key, value in arguments.items():
                if key not in schema["properties"] or not self._valid_argument(value, schema["properties"][key]):
                    return self._error(req_id, -32602, f"Invalid Params: {key}")
            arguments = dict(arguments)
            if "stage" in arguments:
                arguments["stage"] = arguments["stage"].replace("-", "_")
            func_name = TOOL_DISPATCH_MAP[tool_name]

            # Direct all standard output to stderr during tool invocation so stdout remains pristine JSON-RPC
            with contextlib.redirect_stdout(sys.stderr):
                try:
                    api = self._get_api()
                    func = getattr(api, func_name, None)
                    if func is None:
                        raise AttributeError(
                            f"Function '{func_name}' is not exposed in due_diligence_engine.api"
                        )
                    res = func(**arguments)
                    serialized = self._serialize(res)
                    content_text = json.dumps(
                        serialized, ensure_ascii=False, indent=2, default=str
                    )
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": content_text,
                                }
                            ],
                            "structuredContent": serialized,
                            "isError": False,
                        },
                    }
                except Exception as exc:  # noqa: BLE001
                    err_info = {
                        "error": exc.__class__.__name__,
                        "message": str(exc),
                    }
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(err_info, ensure_ascii=False),
                                }
                            ],
                            "structuredContent": err_info,
                            "isError": True,
                        },
                    }

        if method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "resources": MCP_RESOURCES,
                },
            }

        if method == "resources/read":
            uri = params.get("uri")
            if uri == "dde://schemas/consulting/v1":
                data = _get_consulting_schema_data()
            elif uri == "dde://rubrics/technical-5/v1":
                data = _get_technical_5_rubric_data()
            elif uri == "dde://rubrics/atlas-4/v1":
                data = _get_atlas_4_rubric_data()
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32602,
                        "message": f"Resource not found: '{uri}'",
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(data, ensure_ascii=False, indent=2),
                        }
                    ],
                },
            }

        if method == "prompts/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "prompts": MCP_PROMPTS,
                },
            }

        if method == "prompts/get":
            prompt_name = params.get("name")
            prompt_args = params.get("arguments", {})
            if not isinstance(prompt_args, dict) or any(not isinstance(v, str) for v in prompt_args.values()):
                return self._error(req_id, -32602, "Invalid Params: prompt arguments must be strings")
            if prompt_name != "dde-audit":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32602,
                        "message": f"Prompt not found: '{prompt_name}'",
                    },
                }

            target = prompt_args.get("target", "<target_repo_or_path>")
            lang = prompt_args.get("lang", "en")
            stage = prompt_args.get("stage", "series-a")
            prompt_text = _get_audit_prompt_text(target=target, lang=lang, stage=stage)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "description": "End-to-end autonomous audit workflow prompt",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": prompt_text,
                            },
                        }
                    ],
                },
            }

        # Unknown method
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: '{method}'",
            },
        }


def handle_mcp_message(
    msg: dict[str, Any], api_module: Any | None = None
) -> dict[str, Any] | None:
    """Convenience function to handle a single JSON-RPC 2.0 MCP message in-memory."""
    return MCPServer(api_module=api_module).handle_mcp_message(msg)


def run_stdio_mcp_server(api_module: Any | None = None) -> None:
    """Run the MCP server over standard input / standard output using JSON-RPC 2.0.

    All operational logging and diagnostics are written strictly to sys.stderr
    so as not to corrupt the JSON-RPC message stream on sys.stdout.
    """
    server = MCPServer(api_module=api_module)
    sys.stderr.write(
        f"[DDE MCP] Server started (version {due_diligence_engine.__version__}) on stdio\n"
    )
    sys.stderr.flush()

    try:
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break  # EOF reached

                stripped = line.strip()
                if not stripped:
                    continue

                try:
                    def invalid_constant(value):
                        raise ValueError(f"Invalid JSON constant: {value}")
                    msg = json.loads(stripped, parse_constant=invalid_constant)
                except (json.JSONDecodeError, ValueError) as decode_err:
                    err_resp = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {decode_err}",
                        },
                    }
                    sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
                    sys.stdout.flush()
                    continue

                resp = server.handle_mcp_message(msg)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                    sys.stdout.flush()

            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as unhandled_err:  # noqa: BLE001
                sys.stderr.write(f"[DDE MCP ERROR] {unhandled_err}\n")
                sys.stderr.flush()
    finally:
        with contextlib.redirect_stdout(sys.stderr):
            cleanup = server._get_api().close_all_sessions()
        if cleanup and cleanup.get("failed"):
            sys.stderr.write(f"[DDE MCP] Cleanup failed for {len(cleanup['failed'])} session(s)\n")

    sys.stderr.write("[DDE MCP] Server stopped cleanly.\n")
    sys.stderr.flush()
