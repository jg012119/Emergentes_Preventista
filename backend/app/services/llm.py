"""LLM fallback service via Ollama.

Uses llama3.1:8b (or aje-preventista) running locally.
Returns a validated LlamaIntent Pydantic object — never raw text.

Configuration (read from env at import time):
    OLLAMA_URL            Base URL of the Ollama HTTP API  (default: http://localhost:11434)
    OLLAMA_MODEL          Model tag to use                 (default: llama3.1:8b)
    OLLAMA_TIMEOUT        Seconds to wait for a response   (default: 30)
    LLM_FALLBACK_ENABLED  Set to "false" to disable        (default: true)
"""

from __future__ import annotations

import json
from dotenv import load_dotenv

load_dotenv()
import logging
import os
import re
import time
from typing import Any

import httpx

from app.models.schemas import LlamaIntent, LlamaProduct  # noqa: F401 – re-exported

try:
    from assistant_prompt import FEW_SHOT_EXAMPLES
except ImportError:  # pragma: no cover
    FEW_SHOT_EXAMPLES = ""

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "30"))
LLM_FALLBACK_ENABLED: bool = os.getenv("LLM_FALLBACK_ENABLED", "true").lower() != "false"

# ---------------------------------------------------------------------------
# System prompt template
# The {catalog} section is injected at runtime with real DB products.
# ---------------------------------------------------------------------------

_SYSTEM_TEMPLATE = """\
Eres un extractor de intención para pedidos de bebidas de AJE Bolivia.
NO eres un chatbot libre. Tu única función es interpretar mensajes de preventistas.

### Catálogo disponible (SOLO estos productos existen):
{catalog}

### Reglas estrictas:
1. Devuelve SOLO JSON válido con el schema dado. Sin texto adicional.
2. NUNCA inventes productos que no están en el catálogo.
3. Si el usuario pide alcohol (cerveza, cheba, chela, birra, vino, whisky, ron, vodka):
   intencion="fuera_de_alcance", motivo_rechazo="alcohol"
4. Si el usuario pide comida sólida (papas, nachos, hamburguesa, pizza, snack):
   intencion="fuera_de_alcance", motivo_rechazo="comida_solida"
5. Si el mensaje es un saludo: intencion="saludo"
6. Si el usuario pregunta por el menú o catálogo: intencion="consulta_catalogo"
7. Si pide ver todos sus pedidos, historial o pedidos pendientes: intencion="listar_pedidos" (ej. "muéstrame mis pedidos pendientes", "qué pedidos tengo").
8. Si pregunta específicamente por el estado, ubicación o seguimiento de un pedido actual: intencion="estado_pedido" (ej. "cómo va mi pedido?", "dónde está mi entrega?").
9. Si el usuario confirma ("sí", "dale", "ok", "listo", "confirmo"): intencion="confirmacion"
10. Si el usuario niega o cancela ("no", "cancelar", "no gracias"): intencion="negacion"
11. Si el mensaje es una aclaración corta que indica una presentación, volumen o respuesta a una pregunta de tamaño (ej. "de litro", "la de 500", "el de dos litros", "de tres litros", "chico", "el grande", "mediano"):
    - Si el mensaje contiene verbos de pedido (como "quiero", "dame", "manda", "ponme", "trae", "agrega") o marcas/productos del catálogo (como "big", "cola", "cielo", "volt", "oro", "cifrut", "pulp", "free tea", "sporade", "agua"), entonces NUNCA es una aclaración simple, sino un pedido completo. Clasifícalo como intencion="pedido" y extrae el producto.
    - Si NO contiene esos verbos ni marcas, y es solo la frase de tamaño/volumen: establece intencion="aclaracion" y deja la lista de productos vacía (productos=[]), y NO intentes crear un producto con nombre "litro" o similar.
12. Para pedidos: extrae CADA producto con cantidad y presentación.
13. Si hay múltiples presentaciones posibles para un producto, marca requiere_aclaracion=true
    en ese producto y pon pregunta_aclaracion con la pregunta al usuario.
14. El campo sku_sugerido DEBE ser el nombre oficial EXACTO del catálogo o null.
15. Para consulta_catalogo, mensaje_libre = "Te paso el menú de bebidas disponibles."

### Sinónimos bolivianos conocidos:
- "coquita" / "cocaca" = Coca-Cola
- "agüita" / "agüita cielo" / "cielito" = Agua Cielo
- "voltcito" = Volt 300ml | "volt grande" = Volt 500ml
- "orito" = Oro 500ml | "oro grande" = Oro 2L
- "pulpito" = Pulp 300ml
- "cheba" / "chela" / "birra" = cerveza (ALCOHOL — rechazar)
- "papitas" / "nachos" = comida sólida (SÓLIDO — rechazar)
- "familiar" / "grande" ≈ 2L-2.5L | "chico" / "personal" / "chika" ≈ 500ml
- "pa" = para
- "eso nomas" / "nomas" = expresión boliviana de cierre, ignorar
- "me das" / "me manda" / "oye" = formas de pedir

### IMPORTANTE — Transcripciones de voz:
Los mensajes pueden provenir de transcripciones de voz (speech-to-text).
Estos mensajes suelen:
- Carecer de puntuación y mayúsculas
- Tener vacilaciones como "ehhh", "este", "a ver", "entonces", "bueno"
- Tener palabras unidas o separadas de forma inusual
- Incluir saludos al inicio como "hola buenas" seguido del pedido
Interprétalos con la misma lógica que un mensaje escrito normal.
Ignora las vacilaciones y concéntrate en los productos, cantidades y fechas.

{few_shot_examples}
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_catalog_text(products: list[dict[str, Any]]) -> str:
    """Format a list of DB product dicts into a readable catalog string."""
    if not products:
        return "(sin productos disponibles)"
    lines: list[str] = []
    for p in products:
        name = p.get("name", "Producto")
        price = p.get("price")
        stock = p.get("stock")
        parts = [f"- {name}"]
        if price is not None:
            parts.append(f"Bs {float(price):.2f}")
        if stock is not None:
            parts.append(f"stock: {int(stock)}")
        lines.append("  ".join(parts))
    return "\n".join(lines)


def build_compact_catalog(products: list[dict[str, Any]]) -> list[dict]:
    """Devuelve un catálogo compacto con solo los campos que el LLM necesita.

    Reduce el número de tokens sin perder información relevante para el matching.
    """
    return [
        {
            "id": p.get("id", ""),
            "name": p.get("name", ""),
            "category": p.get("category", ""),
            "price": round(float(p.get("price") or 0), 2),
        }
        for p in products
        if p.get("active", True)
    ]


async def warmup() -> bool:
    """Pre-load the model into GPU/RAM to avoid cold-start timeouts.

    Call this once at application startup. Returns True if successful.
    """
    if not LLM_FALLBACK_ENABLED:
        return False
    try:
        logger.info("Warming up Ollama model '%s'...", OLLAMA_MODEL)
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": "hola"}],
                    "stream": False,
                    "options": {"num_predict": 5, "temperature": 0},
                },
            )
            resp.raise_for_status()
        logger.info("Ollama warmup complete.")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ollama warmup failed: %s", exc)
        return False


def _log_to_db(
    user_id: str | None,
    model: str,
    message: str,
    intent: str | None,
    raw_response: str | None,
    parsed_json: dict | None,
    success: bool,
    error: str | None,
    latency_ms: int,
    prompt_tokens: int | None,
    eval_tokens: int | None,
) -> None:
    """Helper to log LLM inference outcomes to database (Supabase or Local SQLite)."""
    try:
        from app.config import get_supabase_admin
        db = get_supabase_admin()
        db.table("llm_logs").insert({
            "user_id": user_id,
            "model": model,
            "message": message,
            "intent": intent,
            "raw_response": raw_response,
            "parsed_json": parsed_json,
            "success": success,
            "error": error,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "eval_tokens": eval_tokens,
        }).execute()
    except Exception as exc:
        logger.warning("Failed to save LLM log: %s", exc)


async def ask_llm(
    user_message: str,
    products: list[dict[str, Any]],
    conversation_history: list[dict[str, str]] | None = None,
    user_id: str | None = None,
    _retry: int = 0,
) -> LlamaIntent | None:
    """Call Ollama and return a validated LlamaIntent object.

    Uses Ollama's structured output feature (format= JSON Schema) to guarantee
    the response is always a valid JSON matching the LlamaIntent schema.

    Returns None if:
    - LLM_FALLBACK_ENABLED is False
    - Ollama is not reachable
    - The model response cannot be validated after 1 retry

    The caller must validate 'sku_sugerido' fields against the real DB —
    this function never writes to the database.
    """
    if not LLM_FALLBACK_ENABLED:
        logger.debug("LLM fallback is disabled via LLM_FALLBACK_ENABLED=false")
        return None

    catalog_text = build_catalog_text(products)
    system_prompt = _SYSTEM_TEMPLATE.format(
        catalog=catalog_text,
        few_shot_examples=FEW_SHOT_EXAMPLES.strip(),
    )

    # Build message list: system + optional recent history + user message
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        # Include at most the last 6 turns to keep context manageable
        for turn in conversation_history[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})

    # On retry: append a hard JSON reminder
    if _retry > 0:
        messages.append({
            "role": "user",
            "content": (
                f"{user_message}\n\n"
                "[IMPORTANTE: Responde SOLO con JSON válido según el schema. "
                "Sin texto adicional, sin explicaciones, sin markdown.]"
            ),
        })
    else:
        messages.append({"role": "user", "content": user_message})

    # Use Ollama structured output with the LlamaIntent JSON Schema
    # This guarantees the model output matches our Pydantic model structure.
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "format": LlamaIntent.model_json_schema(),  # ← Structured output
        "options": {
            "temperature": 0,          # Fully deterministic
            "top_p": 0.2,
            "num_predict": 512,
            "num_ctx": 4096,
        },
        "keep_alive": "30m",
    }

    t_start = time.monotonic()
    raw_content: str = ""

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
            )
            response.raise_for_status()
    except httpx.ConnectError as exc:
        logger.warning("Ollama is not reachable at %s — LLM fallback skipped", OLLAMA_URL)
        _log_to_db(
            user_id=user_id,
            model=OLLAMA_MODEL,
            message=user_message,
            intent=None,
            raw_response=None,
            parsed_json=None,
            success=False,
            error=f"ConnectError: {exc}",
            latency_ms=int((time.monotonic() - t_start) * 1000),
            prompt_tokens=None,
            eval_tokens=None,
        )
        return None
    except httpx.TimeoutException as exc:
        logger.warning("Ollama request timed out after %.0f seconds", OLLAMA_TIMEOUT)
        _log_to_db(
            user_id=user_id,
            model=OLLAMA_MODEL,
            message=user_message,
            intent=None,
            raw_response=None,
            parsed_json=None,
            success=False,
            error=f"TimeoutException: {exc}",
            latency_ms=int((time.monotonic() - t_start) * 1000),
            prompt_tokens=None,
            eval_tokens=None,
        )
        return None
    except httpx.HTTPStatusError as exc:
        err_msg = f"HTTPStatusError {exc.response.status_code}: {exc.response.text[:200]}"
        logger.warning("Ollama returned HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
        _log_to_db(
            user_id=user_id,
            model=OLLAMA_MODEL,
            message=user_message,
            intent=None,
            raw_response=None,
            parsed_json=None,
            success=False,
            error=err_msg,
            latency_ms=int((time.monotonic() - t_start) * 1000),
            prompt_tokens=None,
            eval_tokens=None,
        )
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unexpected error calling Ollama: %s", exc)
        _log_to_db(
            user_id=user_id,
            model=OLLAMA_MODEL,
            message=user_message,
            intent=None,
            raw_response=None,
            parsed_json=None,
            success=False,
            error=f"UnexpectedError: {exc}",
            latency_ms=int((time.monotonic() - t_start) * 1000),
            prompt_tokens=None,
            eval_tokens=None,
        )
        return None

    latency_ms = int((time.monotonic() - t_start) * 1000)
    resp_json = response.json()
    raw_content = resp_json.get("message", {}).get("content", "")

    # Extract Ollama metrics for logging
    prompt_tokens = resp_json.get("prompt_eval_count")
    eval_tokens = resp_json.get("eval_count")

    logger.debug("Ollama raw response (%dms): %s", latency_ms, raw_content[:500])

    # --- Validate with Pydantic ---
    try:
        parsed = LlamaIntent.model_validate_json(raw_content)
        logger.debug(
            "LLM intent=%s confidence=%.2f products=%d latency=%dms",
            parsed.intencion, parsed.confianza, len(parsed.productos), latency_ms,
        )
        _log_to_db(
            user_id=user_id,
            model=OLLAMA_MODEL,
            message=user_message,
            intent=parsed.intencion,
            raw_response=raw_content,
            parsed_json=parsed.model_dump(),
            success=True,
            error=None,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            eval_tokens=eval_tokens,
        )
        return parsed

    except Exception as validation_err:
        err_str = str(validation_err)
        # Structured output failed — this should be rare with format= set
        if _retry < 1:
            logger.warning(
                "LlamaIntent validation failed (attempt %d): %s — retrying...",
                _retry + 1,
                err_str[:200],
            )
            # Log the failed attempt first
            _log_to_db(
                user_id=user_id,
                model=OLLAMA_MODEL,
                message=user_message,
                intent=None,
                raw_response=raw_content,
                parsed_json=None,
                success=False,
                error=f"ValidationError (attempt 1): {err_str}",
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                eval_tokens=eval_tokens,
            )
            return await ask_llm(user_message, products, conversation_history, user_id=user_id, _retry=_retry + 1)

        logger.warning(
            "LlamaIntent validation failed after retry. raw=%s error=%s",
            raw_content[:300],
            err_str[:200],
        )
        _log_to_db(
            user_id=user_id,
            model=OLLAMA_MODEL,
            message=user_message,
            intent=None,
            raw_response=raw_content,
            parsed_json=None,
            success=False,
            error=f"ValidationError (final): {err_str}",
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            eval_tokens=eval_tokens,
        )
        return None


async def check_ollama_status() -> dict[str, Any]:
    """Return a status dict for the /nlp/llm-status diagnostic endpoint."""
    if not LLM_FALLBACK_ENABLED:
        return {"enabled": False, "model": OLLAMA_MODEL, "reachable": None}

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            models = [m.get("name") for m in resp.json().get("models", [])]
            model_loaded = any(OLLAMA_MODEL in (m or "") for m in models)
            return {
                "enabled": True,
                "reachable": True,
                "model": OLLAMA_MODEL,
                "model_loaded": model_loaded,
                "available_models": models,
                "url": OLLAMA_URL,
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "enabled": True,
            "reachable": False,
            "model": OLLAMA_MODEL,
            "error": str(exc),
            "url": OLLAMA_URL,
        }
