"""Technology-focused scoring engine with 10-level ratings.

Evaluates TECHNOLOGY ONLY (no team assessment).
Each dimension is rated on a 10-level scale with clear criteria,
then converted to a 100-point weighted score.

Dimensions (weights sum to 1.0):
1. Technical Originality  (0.25) - Is this real IP or an API wrapper?
2. Technology Advancement  (0.20) - How cutting-edge is the technology?
3. Implementation Depth    (0.20) - Is the implementation production-grade?
4. Architecture Quality    (0.15) - Is the architecture scalable and well-designed?
5. Claim Consistency       (0.10) - Do docs match code?
6. Security Posture        (0.10) - Security practices
"""

from __future__ import annotations

import math
from typing import Any

from due_diligence_engine.models import (
    AnalysisResult,
    RedFlag,
    Score,
    ScoreDimension,
    Severity,
    TechLevel,
    TechLevelRating,
)


# 10-level technology rating criteria
TECH_LEVEL_CRITERIA: dict[str, list[TechLevel]] = {
    "technical_originality": [
        TechLevel(level=1, label="Lv.1 — Copy", description="Existing OSS/API をそのまま利用。独自コードなし"),
        TechLevel(level=2, label="Lv.2 — Wrapper", description="API薄いラッパー。設定変更程度のカスタマイズ"),
        TechLevel(level=3, label="Lv.3 — Glue", description="複数APIの組み合わせ。独自ロジックはルーティングのみ"),
        TechLevel(level=4, label="Lv.4 — Customized", description="既存技術のカスタマイズ。一部独自処理あり"),
        TechLevel(level=5, label="Lv.5 — Extended", description="既存フレームワークの大幅拡張。独自アルゴリズム一部あり"),
        TechLevel(level=6, label="Lv.6 — Hybrid", description="既存+独自技術のハイブリッド。明確なIP領域あり"),
        TechLevel(level=7, label="Lv.7 — Original", description="コア技術が独自実装。特許申請可能レベル"),
        TechLevel(level=8, label="Lv.8 — Advanced", description="業界先端の独自実装。学会発表レベル"),
        TechLevel(level=9, label="Lv.9 — Breakthrough", description="新しい技術パラダイムの提案。論文引用されるレベル"),
        TechLevel(level=10, label="Lv.10 — Frontier", description="世界最先端。既存技術を根本的に置き換える可能性"),
    ],
    "technology_advancement": [
        TechLevel(level=1, label="Lv.1 — Legacy", description="10年以上前の技術。メンテナンスモード"),
        TechLevel(level=2, label="Lv.2 — Outdated", description="5-10年前の技術。後継技術が存在"),
        TechLevel(level=3, label="Lv.3 — Established", description="広く普及した安定技術。新規性なし"),
        TechLevel(level=4, label="Lv.4 — Current", description="現在の業界標準レベル"),
        TechLevel(level=5, label="Lv.5 — Modern", description="最新のベストプラクティスを採用"),
        TechLevel(level=6, label="Lv.6 — Progressive", description="次世代技術の早期採用者"),
        TechLevel(level=7, label="Lv.7 — Innovative", description="業界内で先進的。競合が追随中"),
        TechLevel(level=8, label="Lv.8 — Leading", description="業界をリードする技術選択"),
        TechLevel(level=9, label="Lv.9 — Pioneering", description="新カテゴリを定義する技術"),
        TechLevel(level=10, label="Lv.10 — Visionary", description="5年先の技術を今実装。市場が追いつく段階"),
    ],
    "implementation_depth": [
        TechLevel(level=1, label="Lv.1 — Mockup", description="UIモックのみ。バックエンド未実装"),
        TechLevel(level=2, label="Lv.2 — PoC", description="概念実証レベル。ハードコード多数"),
        TechLevel(level=3, label="Lv.3 — Prototype", description="動くプロトタイプ。エラー処理なし"),
        TechLevel(level=4, label="Lv.4 — Alpha", description="基本機能動作。テストなし"),
        TechLevel(level=5, label="Lv.5 — Beta", description="主要機能実装済み。基本テストあり"),
        TechLevel(level=6, label="Lv.6 — RC", description="本番想定の実装。CI/CDあり"),
        TechLevel(level=7, label="Lv.7 — Production", description="本番運用中。監視・ログあり"),
        TechLevel(level=8, label="Lv.8 — Mature", description="長期運用実績。パフォーマンス最適化済み"),
        TechLevel(level=9, label="Lv.9 — Enterprise", description="大規模運用対応。SLA保証レベル"),
        TechLevel(level=10, label="Lv.10 — Mission-Critical", description="ミッションクリティカル対応。冗長性・DR完備"),
    ],
    "architecture_quality": [
        TechLevel(level=1, label="Lv.1 — Spaghetti", description="構造なし。単一ファイルに全コード"),
        TechLevel(level=2, label="Lv.2 — Monolith", description="最小限の分離。全結合"),
        TechLevel(level=3, label="Lv.3 — Layered", description="基本的なレイヤー分離あり"),
        TechLevel(level=4, label="Lv.4 — Modular", description="モジュール分割。一部密結合"),
        TechLevel(level=5, label="Lv.5 — Clean", description="関心の分離が明確。テスト容易"),
        TechLevel(level=6, label="Lv.6 — Scalable", description="水平スケーリング対応設計"),
        TechLevel(level=7, label="Lv.7 — Microservice", description="適切なサービス分割。API契約明確"),
        TechLevel(level=8, label="Lv.8 — Event-Driven", description="イベント駆動。非同期処理最適化"),
        TechLevel(level=9, label="Lv.9 — Cloud-Native", description="クラウドネイティブ設計。自動スケール"),
        TechLevel(level=10, label="Lv.10 — Distributed", description="分散システム。CAP定理を意識した設計"),
    ],
    "claim_consistency": [
        TechLevel(level=1, label="Lv.1 — Fabricated", description="主張と実装が完全に乖離。意図的虚偽の疑い"),
        TechLevel(level=2, label="Lv.2 — Misleading", description="重要な点で誤解を招く主張"),
        TechLevel(level=3, label="Lv.3 — Exaggerated", description="大幅な誇張。実装は主張の30%以下"),
        TechLevel(level=4, label="Lv.4 — Overstated", description="一部誇張あり。コア機能は存在"),
        TechLevel(level=5, label="Lv.5 — Partial", description="主張の半分程度が検証可能"),
        TechLevel(level=6, label="Lv.6 — Mostly True", description="大部分が事実。軽微な不一致あり"),
        TechLevel(level=7, label="Lv.7 — Accurate", description="主張が実装と一致。ベンチマーク一部あり"),
        TechLevel(level=8, label="Lv.8 — Verified", description="主張がコードで完全に検証可能"),
        TechLevel(level=9, label="Lv.9 — Conservative", description="実装が主張以上。控えめな表現"),
        TechLevel(level=10, label="Lv.10 — Transparent", description="全主張に証拠付き。第三者検証済み"),
    ],
    "security_posture": [
        TechLevel(level=1, label="Lv.1 — Negligent", description="ハードコードされた秘密鍵。SQLi脆弱性"),
        TechLevel(level=2, label="Lv.2 — Minimal", description="基本的な問題あり。入力検証なし"),
        TechLevel(level=3, label="Lv.3 — Basic", description="最低限の対策。OWASP Top10未対応"),
        TechLevel(level=4, label="Lv.4 — Standard", description="基本的なセキュリティ対策済み"),
        TechLevel(level=5, label="Lv.5 — Compliant", description="業界標準準拠。定期的な依存関係更新"),
        TechLevel(level=6, label="Lv.6 — Hardened", description="セキュリティスキャン自動化。脆弱性管理あり"),
        TechLevel(level=7, label="Lv.7 — Defense-in-Depth", description="多層防御。ペネトレーションテスト実施"),
        TechLevel(level=8, label="Lv.8 — Zero-Trust", description="ゼロトラスト設計。暗号化完備"),
        TechLevel(level=9, label="Lv.9 — Certified", description="SOC2/ISO27001等の認証取得レベル"),
        TechLevel(level=10, label="Lv.10 — Military-Grade", description="国防レベル。形式検証・監査完備"),
    ],
}


# Dimension definitions with weights (v0.3 — 5 dimensions, equal 20% each)
# Security Posture was merged into Architecture Quality for a more balanced view.
DIMENSIONS = {
    "technical_originality": {
        "name": "Technical Originality",
        "name_ja": "技術独自性",
        "weight": 0.20,
    },
    "technology_advancement": {
        "name": "Technology Advancement",
        "name_ja": "技術先進性",
        "weight": 0.20,
    },
    "implementation_depth": {
        "name": "Implementation Depth",
        "name_ja": "実装深度",
        "weight": 0.20,
    },
    "architecture_quality": {
        "name": "Architecture Quality (incl. Security Posture)",
        "name_ja": "アーキテクチャ品質（セキュリティ態勢を含む）",
        "weight": 0.20,
    },
    "claim_consistency": {
        "name": "Claim Consistency",
        "name_ja": "主張整合性",
        "weight": 0.20,
    },
}


# Industry-Specific Domain Evaluation Packs (v0.9.0)
INDUSTRY_DOMAIN_PACKS: dict[str, dict[str, Any]] = {
    "messaging_cyber": {
        "id": "messaging_cyber",
        "label_en": "Secure Messaging & Cybersecurity (E2EE / Zero-Knowledge / Defense)",
        "label_ja": "秘匿通信・サイバーセキュリティ（E2EE / ゼロ知識 / 防衛）",
        "keywords": [
            "signal", "ratchet", "pqxdh", "x3dh", "kyber", "ml-kem", "noise",
            "mls", "nostr", "fernet", "aes-gcm", "chacha20", "ed25519", "ecdsa",
            "e2ee", "zero-retention", "dod 5220",
        ],
        "mandatory_controls": [
            "Cryptographic Primitive & Post-Quantum Agility (X3DH/PQXDH, Double Ratchet, MLS, or AEAD)",
            "Zero-Retention Ephemeral Key & Memory Hygiene (DoD 5220.22-M / explicit key zeroization)",
            "Strict Metadata & SSRF/Relay Isolation (Zero plaintext leakage to relay or log sinks)",
        ],
        "regulatory_frameworks": ["NIST FIPS 140-3 / PQC", "DoD 5220.22-M", "SOC2 Type II"],
    },
    "fintech": {
        "id": "fintech",
        "label_en": "FinTech, Payments & Institutional Ledger (PCI-DSS / Double-Entry / Custody)",
        "label_ja": "金融・決済・デジタル資産基盤（PCI-DSS / 複式簿記 / カストディ）",
        "keywords": [
            "stripe", "plaid", "ledger", "payment", "wallet", "settlement",
            "kyc", "aml", "pci", "iban", "swift", "custody", "invoice", "billing",
        ],
        "mandatory_controls": [
            "Idempotent Transaction & Double-Entry Ledger Integrity (Zero float rounding on currency)",
            "PCI-DSS / Tokenized Secret Boundary & Audit Trail Immutability",
            "Strong Consistency, Replay Protection & Rate-Limited Settlement Endpoints",
        ],
        "regulatory_frameworks": ["PCI-DSS v4.0", "SOX / SOC1 Type II", "FATF AML/KYC"],
    },
    "medical": {
        "id": "medical",
        "label_en": "MedTech, Clinical AI & Digital Health (HIPAA / SaMD / HL7 FHIR)",
        "label_ja": "医療・ヘルスケア・臨床AI（HIPAA / SaMD医療機器 / HL7 FHIR）",
        "keywords": [
            "hipaa", "fhir", "hl7", "dicom", "patient", "clinical",
            "ehr", "emr", "medical", "fda", "samd", "phi",
        ],
        "mandatory_controls": [
            "PHI Encryption at Rest/In-Transit & HIPAA Tamper-Evident Audit Logging",
            "Deterministic Clinical Safety Guardrails & Hallucination Prevention",
            "Strict Consent, Role-Based Access Control (RBAC) & Data Anonymization",
        ],
        "regulatory_frameworks": ["HIPAA Security Rule", "FDA SaMD / IEC 62304", "ISO 13485"],
    },
    "ai_agent": {
        "id": "ai_agent",
        "label_en": "Frontier AI, LLM Agents & RAG Orchestration (Zero-Retention / Eval / Sandbox)",
        "label_ja": "先端AI・自律エージェント・RAG基盤（Zero-Retention / 評価ハーネス / サンドボックス）",
        "keywords": [
            "openai", "anthropic", "genai", "gemini", "langchain", "llamaindex",
            "mcp", "vector", "embedding", "rag", "prompt", "agent", "llm",
        ],
        "mandatory_controls": [
            "Zero-Retention AI Inference Policy (store=False / ZDR enforcement)",
            "Prompt Injection & Untrusted Tool-Call Sandbox Isolation",
            "Deterministic Schema Validation & Multi-Model Cost/Token FinOps Guardrails",
        ],
        "regulatory_frameworks": ["EU AI Act", "NIST AI RMF 1.0", "OWASP LLM Top 10"],
    },
    "gaming": {
        "id": "gaming",
        "label_en": "Real-Time Gaming, 3D Spatial Engine & Interactive Simulation",
        "label_ja": "リアルタイムゲーム・3D空間エンジン・インタラクティブシミュレーション",
        "keywords": [
            "unity", "unreal", "godot", "webgl", "three", "vulkan",
            "metal", "shader", "physics", "ecs", "netcode", "tick", "matchmaking",
        ],
        "mandatory_controls": [
            "Frame-Budget Determinism & Zero-GC Hot-Loop Allocation Discipline",
            "Server-Authoritative Netcode & Anti-Cheat State Validation",
            "Asset Streaming Pipeline & Cross-Platform GPU Shader Fallbacks",
        ],
        "regulatory_frameworks": ["COPPA / GDPR-K", "Platform TRC/Lotcheck", "OWASP API Security"],
    },
    "enterprise_saas": {
        "id": "enterprise_saas",
        "label_en": "Enterprise B2B SaaS & Cloud-Native Platform (SOC2 / Multi-Tenant)",
        "label_ja": "エンタープライズB2B SaaS・クラウドネイティブ基盤（SOC2 / マルチテナント）",
        "keywords": [
            "tenant", "rbac", "sso", "saml", "oidc", "webhook",
            "graphql", "rest", "microservice", "kubernetes", "terraform",
        ],
        "mandatory_controls": [
            "Tenant Isolation Boundary & Row-Level Security (RLS) Enforcement",
            "Automated CI/CD, Deterministic Lockfile & SBOM Supply-Chain Provenance",
            "Horizontal Scalability (Zero Async-Blocking / Zero N+1 Query Hotspots)",
        ],
        "regulatory_frameworks": ["SOC2 Type II", "ISO/IEC 27001", "GDPR / CCPA"],
    },
}


class Scorer:
    """Computes a technology-focused due diligence score.

    Evaluates technology ONLY (no team/process assessment).
    Each dimension is rated on a 10-level scale and converted to 100-point score.
    """

    def score(self, result: AnalysisResult) -> Score:
        """ヒューリスティックスコアとAI結果を統合して最終スコアを算出。

        AI結果がある場合: (heuristic * 0.3 + ai_avg * 0.7)
        AI結果がない場合: ヒューリスティック100%
        """
        # Note: security_posture is MERGED into architecture_quality (v0.3).
        # We still compute the security-posture signal internally, then fold it
        # into architecture_quality's score via a weighted blend inside
        # `_score_architecture_quality`.
        dimensions = [
            self._score_technical_originality(result),
            self._score_technology_advancement(result),
            self._score_implementation_depth(result),
            self._score_architecture_quality(result),  # now includes security dimension
            self._score_claim_consistency(result),
        ]

        # マルチAI結果がある場合、各次元のスコアをAI平均と加重統合
        if result.ai_results:
            dimensions = self._integrate_ai_scores(dimensions, result)

        # Collect all red flags
        all_flags: list[RedFlag] = []
        all_flags.extend(result.code_analysis.red_flags)
        all_flags.extend(result.doc_analysis.red_flags)
        all_flags.extend(result.git_forensics.red_flags)
        all_flags.extend(result.consistency.red_flags)

        # Compute tech level ratings
        tech_ratings = self._compute_tech_ratings(result, dimensions)

        score = Score(
            dimensions=dimensions,
            red_flags=all_flags,
            tech_ratings=tech_ratings,
        )
        score.compute()
        score.tech_ratings = self._compute_tech_ratings(result, score.dimensions)
        result.code_analysis.complexity_metrics["industry_pack"] = self.detect_industry_pack(
            result
        )
        result.code_analysis.complexity_metrics["pmi_estimate"] = self.compute_pmi_estimate(
            result, score
        )
        return score

    @staticmethod
    def detect_industry_pack(
        result: AnalysisResult, override_industry: str | None = None
    ) -> dict[str, Any]:
        """Auto-detect or apply explicit Industry-Specific Domain Evaluation Pack."""
        code = result.code_analysis
        override = (
            override_industry
            or str(code.complexity_metrics.get("industry_override") or "").strip().lower()
        )
        if override and override in INDUSTRY_DOMAIN_PACKS:
            pack = dict(INDUSTRY_DOMAIN_PACKS[override])
            pack["detection_mode"] = "explicit"
            pack["matched_keywords"] = [override]
            return pack

        corpus_parts: list[str] = [
            result.project_name.lower(),
            " ".join(code.findings).lower(),
            " ".join(getattr(code, "architecture_patterns", [])).lower(),
            " ".join(code.complexity_metrics.get("crypto_signals", [])).lower(),
            " ".join(result.doc_analysis.claims).lower(),
        ]
        corpus = " ".join(corpus_parts)

        best_key = "enterprise_saas"
        best_hits: list[str] = []
        for key, spec in INDUSTRY_DOMAIN_PACKS.items():
            hits = [kw for kw in spec["keywords"] if kw in corpus]
            if len(hits) > len(best_hits):
                best_key = key
                best_hits = hits

        if not best_hits and code.complexity_metrics.get("crypto_signals"):
            best_key = "messaging_cyber"
            best_hits = list(code.complexity_metrics.get("crypto_signals", []))[:3]

        pack = dict(INDUSTRY_DOMAIN_PACKS[best_key])
        pack["detection_mode"] = "auto"
        pack["matched_keywords"] = best_hits
        return pack

    @staticmethod
    def compute_pmi_estimate(
        result: AnalysisResult, score: Score | None = None
    ) -> dict[str, Any]:
        """Task 4: Compute deterministic M&A Post-Merger Integration (Day-1 / Day-30 / Day-100) effort and technical debt."""
        code = result.code_analysis
        git = result.git_forensics
        all_flags = list(score.red_flags) if score is not None else list(code.red_flags)

        crit_count = sum(1 for f in all_flags if f.severity == Severity.CRITICAL)
        high_count = sum(1 for f in all_flags if f.severity == Severity.HIGH)
        med_count = sum(1 for f in all_flags if f.severity == Severity.MEDIUM)

        async_blocking = len(code.complexity_metrics.get("async_blocking", []))
        n_plus_one = len(code.complexity_metrics.get("n_plus_one_hotspots", []))
        nested_loops = len(code.complexity_metrics.get("nested_loop_hotspots", []))
        copyleft = code.complexity_metrics.get("copyleft_licenses", [])
        has_lockfile = bool(code.complexity_metrics.get("has_lockfile", False))

        # Quantify engineering remediation effort in person-days
        person_days = (
            crit_count * 5.0
            + high_count * 3.0
            + med_count * 1.5
            + async_blocking * 0.5
            + n_plus_one * 1.0
            + (0.0 if code.has_tests else 5.0)
            + (0.0 if code.has_ci_cd else 3.0)
            + (0.0 if has_lockfile else 1.0)
        )
        person_days = round(max(1.0, person_days), 1)

        if git.unique_authors == 1 and code.total_lines > 2000:
            bus_factor_risk = "high"
        elif git.unique_authors <= 2 and code.total_lines > 5000:
            bus_factor_risk = "moderate"
        else:
            bus_factor_risk = "low"

        day_1_actions: list[str] = []
        if crit_count > 0 or high_count > 0:
            day_1_actions.append(
                f"Remediate {crit_count} CRITICAL and {high_count} HIGH code-verified security/injection defects"
            )
        if copyleft:
            day_1_actions.append(
                f"Isolate or replace viral copyleft dependencies ({', '.join(copyleft)}) before M&A closing"
            )
        if not has_lockfile and code.dependency_count > 0:
            day_1_actions.append("Freeze deterministic dependency lockfile & generate SBOM")
        if not day_1_actions:
            day_1_actions.append("Verify production secret rotation & zero-trust access boundaries")

        day_30_actions: list[str] = []
        if not code.has_ci_cd:
            day_30_actions.append("Establish automated CI/CD + SAST/secret-scanning release gates")
        if not code.has_tests:
            day_30_actions.append("Add regression test suite covering core domain & security boundaries")
        if async_blocking > 0 or n_plus_one > 0:
            day_30_actions.append(
                f"Eliminate {async_blocking} async-blocking I/O call(s) and {n_plus_one} N+1 query hotspot(s)"
            )
        if not day_30_actions:
            day_30_actions.append("Enforce p99 latency SLO telemetry & automated dependency auditing")

        day_100_actions: list[str] = []
        if nested_loops > 0:
            day_100_actions.append(
                f"Refactor {nested_loops} nested-loop hotspot(s) to O(1) indexed lookups"
            )
        if bus_factor_risk in {"high", "moderate"}:
            day_100_actions.append(
                f"Mitigate {bus_factor_risk} bus-factor concentration via architecture runbooks & pair ownership"
            )
        day_100_actions.append("Complete multi-region scale hardening & unit-economics COGS optimization")

        return {
            "estimated_person_days": person_days,
            "bus_factor_risk": bus_factor_risk,
            "day_1_actions": day_1_actions,
            "day_30_actions": day_30_actions,
            "day_100_actions": day_100_actions,
        }

    def _integrate_ai_scores(
        self,
        heuristic_dims: list[ScoreDimension],
        result: AnalysisResult,
    ) -> list[ScoreDimension]:
        """ヒューリスティックスコアとマルチAI平均スコアを加重統合。

        各次元: 統合スコア = heuristic * 0.3 + ai_avg * 0.7
        """
        # v0.3: security_posture merged into architecture_quality (no separate key).
        # Accept both old display name and new one for backward compat with AI outputs.
        dim_key_map = {
            "Technical Originality": "technical_originality",
            "Technology Advancement": "technology_advancement",
            "Implementation Depth": "implementation_depth",
            "Architecture Quality": "architecture_quality",
            "Architecture Quality (incl. Security Posture)": "architecture_quality",
            "Claim Consistency": "claim_consistency",
        }

        valid_ai = [
            r for r in result.ai_results.values()
            if r.error is None and r.dimension_scores
        ]

        if not valid_ai:
            return heuristic_dims

        def _clean_score(val: Any) -> float | None:
            if not isinstance(val, (int, float)) or not math.isfinite(val):
                return None
            return max(0.0, min(100.0, float(val)))

        integrated: list[ScoreDimension] = []
        for dim in heuristic_dims:
            ai_key = dim_key_map.get(dim.name)
            if not ai_key:
                integrated.append(dim)
                continue

            ai_scores: list[float] = []
            provider_details_list: list[str] = []

            for r in valid_ai:
                if ai_key == "architecture_quality":
                    arch_val = _clean_score(r.dimension_scores.get("architecture_quality"))
                    sec_val = _clean_score(r.dimension_scores.get("security_posture"))
                    if arch_val is not None and sec_val is not None:
                        score_val = arch_val * 0.6 + sec_val * 0.4
                    elif arch_val is not None:
                        score_val = arch_val
                    elif sec_val is not None:
                        score_val = sec_val
                    else:
                        score_val = None
                else:
                    score_val = _clean_score(r.dimension_scores.get(ai_key))

                if score_val is not None:
                    ai_scores.append(score_val)
                    provider_details_list.append(f"{r.provider.capitalize()}: {score_val:.0f}")

            if ai_scores:
                ai_avg = sum(ai_scores) / len(ai_scores)
                blended = dim.score * 0.3 + ai_avg * 0.7

                provider_details = ", ".join(provider_details_list)
                rationale = (
                    f"{dim.rationale} "
                    f"[AI avg: {ai_avg:.0f} ({provider_details}) | "
                    f"Heuristic: {dim.score:.0f} | Blended: {blended:.0f}]"
                )

                integrated.append(ScoreDimension(
                    name=dim.name,
                    score=round(blended, 1),
                    weight=dim.weight,
                    rationale=rationale,
                    sub_scores=dim.sub_scores,
                    flags=dim.flags,
                ))
            else:
                integrated.append(dim)

        return integrated

    def get_level_criteria(self, dimension_key: str) -> list[TechLevel]:
        """Get the 10-level criteria for a given dimension."""
        return TECH_LEVEL_CRITERIA.get(dimension_key, [])

    def _compute_tech_ratings(
        self,
        result: AnalysisResult,
        dimensions: list[ScoreDimension] | None = None,
    ) -> list[TechLevelRating]:
        """Compute 10-level ratings for all dimensions."""
        ratings: list[TechLevelRating] = []

        dim_scores: dict[str, float] = {}
        if dimensions:
            for d in dimensions:
                for k in (
                    "technical_originality",
                    "technology_advancement",
                    "implementation_depth",
                    "architecture_quality",
                    "claim_consistency",
                ):
                    if DIMENSIONS[k]["name"] == d.name:
                        dim_scores[k] = d.score

        # Technical Originality
        if "technical_originality" in dim_scores:
            orig_level = max(1, min(10, int(round(dim_scores["technical_originality"] / 10.0))))
        else:
            orig_level = self._determine_originality_level(result)
        criteria = TECH_LEVEL_CRITERIA["technical_originality"]
        ratings.append(TechLevelRating(
            dimension="Technical Originality",
            dimension_ja="技術独自性",
            level=orig_level,
            label=criteria[orig_level - 1].label,
            description=criteria[orig_level - 1].description,
            criteria=criteria,
        ))

        # Technology Advancement
        if "technology_advancement" in dim_scores:
            adv_level = max(1, min(10, int(round(dim_scores["technology_advancement"] / 10.0))))
        else:
            adv_level = self._determine_advancement_level(result)
        criteria = TECH_LEVEL_CRITERIA["technology_advancement"]
        ratings.append(TechLevelRating(
            dimension="Technology Advancement",
            dimension_ja="技術先進性",
            level=adv_level,
            label=criteria[adv_level - 1].label,
            description=criteria[adv_level - 1].description,
            criteria=criteria,
        ))

        # Implementation Depth
        if "implementation_depth" in dim_scores:
            impl_level = max(1, min(10, int(round(dim_scores["implementation_depth"] / 10.0))))
        else:
            impl_level = self._determine_implementation_level(result)
        criteria = TECH_LEVEL_CRITERIA["implementation_depth"]
        ratings.append(TechLevelRating(
            dimension="Implementation Depth",
            dimension_ja="実装深度",
            level=impl_level,
            label=criteria[impl_level - 1].label,
            description=criteria[impl_level - 1].description,
            criteria=criteria,
        ))

        # Architecture Quality
        if "architecture_quality" in dim_scores:
            arch_level = max(1, min(10, int(round(dim_scores["architecture_quality"] / 10.0))))
        else:
            arch_level = self._determine_architecture_level(result)
        criteria = TECH_LEVEL_CRITERIA["architecture_quality"]
        ratings.append(TechLevelRating(
            dimension="Architecture Quality",
            dimension_ja="アーキテクチャ品質",
            level=arch_level,
            label=criteria[arch_level - 1].label,
            description=criteria[arch_level - 1].description,
            criteria=criteria,
        ))

        # Claim Consistency
        if "claim_consistency" in dim_scores:
            claim_level = max(1, min(10, int(round(dim_scores["claim_consistency"] / 10.0))))
        else:
            claim_level = self._determine_claim_level(result)
        criteria = TECH_LEVEL_CRITERIA["claim_consistency"]
        ratings.append(TechLevelRating(
            dimension="Claim Consistency",
            dimension_ja="主張整合性",
            level=claim_level,
            label=criteria[claim_level - 1].label,
            description=criteria[claim_level - 1].description,
            criteria=criteria,
        ))

        # v0.3: Security Posture as a standalone tech rating is removed —
        # it has been merged into Architecture Quality. Internal security
        # level is still computed (via _determine_security_level) and factored
        # into _score_architecture_quality's blended output.

        return ratings

    # --- Level determination methods (heuristic-based) ---

    def _determine_originality_level(self, result: AnalysisResult) -> int:
        code = result.code_analysis
        ratio = code.api_wrapper_ratio
        lines = code.total_lines

        if ratio > 0.8:
            return 1 if lines < 500 else 2
        if ratio > 0.6:
            return 3
        if ratio > 0.4:
            return 4
        if ratio > 0.2:
            base = 5
        else:
            base = 6

        # Boost for large, diverse codebases
        if lines > 20000 and len(code.languages) >= 3:
            base = min(base + 2, 10)
        elif lines > 10000:
            base = min(base + 1, 10)

        return base

    def _determine_advancement_level(self, result: AnalysisResult) -> int:
        code = result.code_analysis
        base = 4  # Start at "Current"

        # Language modernity heuristics
        modern_langs = {"TypeScript", "Rust", "Go", "Kotlin", "Swift", "Dart"}
        legacy_langs = {"Perl", "COBOL", "Fortran", "VB"}

        project_langs = set(code.languages.keys())
        # Normalize extensions to language names
        ext_to_lang = {
            ".ts": "TypeScript", ".tsx": "TypeScript",
            ".rs": "Rust", ".go": "Go",
            ".kt": "Kotlin", ".swift": "Swift", ".dart": "Dart",
            ".py": "Python", ".js": "JavaScript",
        }
        actual_langs = {ext_to_lang.get(ext, ext) for ext in project_langs}

        if actual_langs & modern_langs:
            base += 1
        if actual_langs & legacy_langs:
            base -= 2

        # Dependency freshness proxy: more deps = potentially more modern ecosystem
        if code.dependency_count > 30:
            base += 1
        if code.has_ci_cd:
            base += 1

        return max(1, min(base, 10))

    def _determine_implementation_level(self, result: AnalysisResult) -> int:
        code = result.code_analysis
        base = 3  # Start at "Prototype"

        if code.total_lines > 500:
            base = 4
        if code.total_lines > 2000:
            base = 5
        if code.has_tests:
            base += 1
        if code.has_ci_cd:
            base += 1
        if code.total_lines > 10000 and code.has_tests and code.has_ci_cd:
            base += 1
        if code.total_files > 100 and code.has_documentation:
            base += 1

        return max(1, min(base, 10))

    def _determine_architecture_level(self, result: AnalysisResult) -> int:
        code = result.code_analysis
        base = 3  # Start at "Layered"

        if code.total_files > 20:
            base = 4
        if code.total_files > 50 and len(code.languages) >= 2:
            base = 5
        if code.total_files > 100:
            base += 1
        if code.has_ci_cd and code.has_tests:
            base += 1
        if code.has_documentation:
            base += 1

        # Penalty for excessive dependencies (can indicate poor architecture)
        if code.dependency_count > 100:
            base -= 1

        return max(1, min(base, 10))

    def _determine_claim_level(self, result: AnalysisResult) -> int:
        consistency = result.consistency
        score = consistency.consistency_score
        contradictions = len(consistency.contradictions)

        if contradictions > 5:
            return max(1, min(2, int(score / 20)))
        if contradictions > 2:
            return max(1, min(4, int(score / 15)))

        # Map consistency_score (0-100) to level (1-10)
        level = max(1, min(10, int(score / 10)))
        return level

    def _determine_security_level(self, result: AnalysisResult) -> int:
        code = result.code_analysis
        base = 4  # Start at "Standard"

        security_flags = [f for f in code.red_flags if "security" in f.category.lower()]

        if any(f.severity == Severity.CRITICAL for f in security_flags):
            return 1
        if any(f.severity == Severity.HIGH for f in security_flags):
            base -= 2

        base -= len(security_flags)

        if code.has_ci_cd:
            base += 1
        if code.has_tests:
            base += 1
        if code.dependency_count < 50:
            base += 1
        if code.complexity_metrics.get("crypto_signals") and not security_flags:
            base += 1

        return max(1, min(base, 10))

    # --- Score computation methods (convert level to 100-point) ---

    def _score_technical_originality(self, result: AnalysisResult) -> ScoreDimension:
        level = self._determine_originality_level(result)
        score = level * 10.0
        code = result.code_analysis

        return ScoreDimension(
            name=DIMENSIONS["technical_originality"]["name"],
            score=score,
            weight=DIMENSIONS["technical_originality"]["weight"],
            rationale=(
                f"Tech Level {level}/10. "
                f"API wrapper ratio: {code.api_wrapper_ratio:.0%}, "
                f"{code.total_lines} lines across {len(code.languages)} languages."
            ),
            sub_scores={
                "api_wrapper_ratio": max(0, 100 - code.api_wrapper_ratio * 100),
                "codebase_size": min(100, code.total_lines / 100),
            },
            flags=[f for f in code.red_flags if f.category == "code_originality"],
        )

    def _score_technology_advancement(self, result: AnalysisResult) -> ScoreDimension:
        level = self._determine_advancement_level(result)
        score = level * 10.0

        return ScoreDimension(
            name=DIMENSIONS["technology_advancement"]["name"],
            score=score,
            weight=DIMENSIONS["technology_advancement"]["weight"],
            rationale=f"Tech Level {level}/10. Technology stack modernity assessment.",
            sub_scores={
                "language_modernity": score,
                "ecosystem_freshness": score,
            },
        )

    def _score_implementation_depth(self, result: AnalysisResult) -> ScoreDimension:
        level = self._determine_implementation_level(result)
        score = level * 10.0
        code = result.code_analysis

        rationale_parts = [f"Tech Level {level}/10."]
        if code.has_tests:
            rationale_parts.append("Tests present.")
        else:
            rationale_parts.append("No tests.")
        if code.has_ci_cd:
            rationale_parts.append("CI/CD configured.")
        else:
            rationale_parts.append("No CI/CD.")

        return ScoreDimension(
            name=DIMENSIONS["implementation_depth"]["name"],
            score=score,
            weight=DIMENSIONS["implementation_depth"]["weight"],
            rationale=" ".join(rationale_parts),
            sub_scores={
                "tests": 100 if code.has_tests else 0,
                "ci_cd": 100 if code.has_ci_cd else 0,
                "documentation": 100 if code.has_documentation else 0,
            },
            flags=[f for f in code.red_flags if f.category in ("code_quality", "engineering_maturity")],
        )

    def _score_architecture_quality(self, result: AnalysisResult) -> ScoreDimension:
        """Architecture Quality (now includes Security Posture, v0.3).

        Blends architecture signal + security signal 60/40 — architecture is
        the primary axis but security maturity is an integral part of
        production-grade architecture.
        """
        arch_level = self._determine_architecture_level(result)
        sec_level = self._determine_security_level(result)
        # Blended level — architecture 60%, security 40%
        blended_level = (arch_level * 0.6) + (sec_level * 0.4)
        score = blended_level * 10.0
        code = result.code_analysis
        security_flags = [f for f in code.red_flags if "security" in f.category.lower()]

        return ScoreDimension(
            name=DIMENSIONS["architecture_quality"]["name"],
            score=score,
            weight=DIMENSIONS["architecture_quality"]["weight"],
            rationale=(
                f"Architecture Lv.{arch_level}/10, Security Lv.{sec_level}/10 → blended {blended_level:.1f}. "
                f"{code.total_files} files, {code.dependency_count} deps, "
                f"{len(security_flags)} security findings."
            ),
            sub_scores={
                "architecture_level": arch_level * 10.0,
                "security_level": sec_level * 10.0,
                "file_structure": min(100, code.total_files * 2),
                "dependency_health": max(0, 100 - max(0, code.dependency_count - 50)),
            },
            flags=security_flags,
        )

    def _score_claim_consistency(self, result: AnalysisResult) -> ScoreDimension:
        level = self._determine_claim_level(result)
        score = level * 10.0
        consistency = result.consistency

        return ScoreDimension(
            name=DIMENSIONS["claim_consistency"]["name"],
            score=score,
            weight=DIMENSIONS["claim_consistency"]["weight"],
            rationale=(
                f"Tech Level {level}/10. "
                f"{len(consistency.verified_claims)} verified, "
                f"{len(consistency.unverified_claims)} unverified, "
                f"{len(consistency.contradictions)} contradictions."
            ),
            sub_scores={
                "verified_ratio": consistency.consistency_score,
                "contradiction_count": max(0, 100 - len(consistency.contradictions) * 20),
            },
            flags=consistency.red_flags,
        )

    # NOTE: _score_security_posture was removed in v0.3.
    # Security is now folded into _score_architecture_quality (60/40 blend).
    # _determine_security_level() is kept — it's called by the new blended
    # architecture scorer above.
