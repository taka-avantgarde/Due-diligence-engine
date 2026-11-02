# Rule 10: Security Boundaries & Zero-Retention Protocols

> **Scope**: Target code analysis, network verification, data encryption, and wiping lifecycle.  
> **Enforcement**: Mechanically verified by `tests/test_audit_regressions.py` and security audit suites.

---

## 1. Untrusted Code Execution Prohibition
- **NEVER** execute target repository code, scripts, build steps, git hooks, or binary fixtures during an audit.
- Ingestion and static analysis must rely strictly on read-only AST parsers, regex tokenizers, and static file inspection.
- Zip Slip, FIFO special devices, symlink traversal out-of-bounds, and path traversal (`..`) must be strictly blocked before unpacking or opening files.

---

## 2. SSRF Blocking & Network Guardrails (`analyze/site_analyzer.py`)
- Target infrastructure site checks (`_is_ip_safe`) must validate IP addresses against `ip.is_global`.
- **Blocked Ranges**:
  - Private networks (RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Loopback (`127.0.0.0/8`, `::1`)
  - Link-local / Cloud metadata (`169.254.0.0/16`, `fe80::/10`)
  - Carrier-grade NAT (RFC 6598: `100.64.0.0/10`)
  - Broadcast, multicast, and reserved ranges.
- DNS resolution must occur immediately before socket connection; redirects must re-validate the target IP.

---

## 3. Cryptographic Storage & DoD 5220.22-M Purge (`purge/purger.py`)
- **Encryption at Rest**:
  - Ephemeral analysis artifacts and decrypted caches must be stored with restricted POSIX permissions (`0o700` directory, `0o600` files).
  - Sensitive tokens and evidence are encrypted via Fernet keys generated in memory.
- **DoD 5220.22-M 3-Pass Overwrite**:
  - All temporary files containing client repository code or intermediate embeddings must be purged using `"r+b"` 3-pass binary overwrite:
    1. Pass 1: Zero bytes (`0x00`)
    2. Pass 2: One bytes (`0xFF`)
    3. Pass 3: Cryptographic pseudo-random bytes (`os.urandom`)
  - Files are flushed (`flush()`, `os.fsync()`) and unlinked.
- **ECDSA P-256 Purge Certificates**:
  - Every purge operation issues a non-repudiable certificate signed with an ephemeral ECDSA P-256 private key, certifying the exact files, timestamp, and SHA-256 hash.

---

## 4. Zero-Retention AI Provider Guardrail (`ai/providers.py`)
- In all API requests to upstream LLMs (Anthropic, Google Gemini, OpenAI), `store=False` (or provider equivalent zero-retention parameter) MUST be enforced.
- Target proprietary code fragments must never be sent to training queues, public prompt logs, or unencrypted persistent endpoints.
