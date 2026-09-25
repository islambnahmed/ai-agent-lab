# Capability Discovery

At the start of a run, an agent or worker may inspect which legitimate tools are actually available in that runtime and adapt its plan accordingly.

This is optional infrastructure, not a fixed checklist.

Useful questions:
- Which research, code, file, GitHub, Notion, Drive, or other safe tools are available now?
- Which tools can read, write, execute, test, search, or verify?
- Which capabilities are unavailable in this run?
- Is there a simpler or stronger method than the one previously used?
- Did any new capability become available since the last checkpoint?

Rules:
- Never assume a capability exists until confirmed by the runtime/tool.
- Never claim a tool action happened unless confirmed.
- Do not seek credentials, new accounts, security changes, or access outside authorized lab spaces.
- Record only durable capability discoveries that materially improve future work.
- Agents may modify or replace this discovery method if they find a better one.
