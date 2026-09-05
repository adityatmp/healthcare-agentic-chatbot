# Healthcare Safety & Security Architecture

## Guardrails
1. **No Clinical Authority**: Emergency or diagnosis queries receive conservative safety directions without diagnostic/prescription claims.
2. **Prompt Injection Boundary**: PDF context is placed in `<context>` XML blocks. System prompt specifies context is DATA, preventing embedded PDF prompt overrides.
3. **Local Privacy**: Document embeddings, vector storage, and LLM inference operate 100% locally via Ollama. No healthcare data is sent to external clouds.
