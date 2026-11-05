import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedSignalResult:
    is_parsed: bool
    direction: Optional[str] = None          # "COMPRA" | "VENTA"
    instrument: Optional[str] = None         # "XAUUSD" | "GC"
    entry_price: Optional[float] = None
    entry_range_low: Optional[float] = None
    entry_range_high: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profits: list[float] = field(default_factory=list)
    parse_notes: Optional[str] = None


# Rango plausible para precios de Oro (XAUUSD / futuros GC) en USD/oz
MIN_GOLD_PRICE = 1000.0
MAX_GOLD_PRICE = 10000.0


def _is_valid_gold_price(val: float) -> bool:
    return MIN_GOLD_PRICE <= val <= MAX_GOLD_PRICE


def _clean_number(num_str: str) -> Optional[float]:
    """Convierte cadena numérica como '2,650.50' o '2650,5' en float si es un precio válido."""
    s = num_str.strip()
    if not s:
        return None
    # Si tiene coma y punto (ej. 2,650.50), quitar la coma de miles
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        # Si la coma separa 1 o 2 decimales (ej. 2650,50) -> punto decimal
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        val = float(s)
        return val if _is_valid_gold_price(val) else None
    except ValueError:
        return None


def _detect_instrument(text: str, default_channel_is_gold: bool = True) -> Optional[str]:
    upper = text.upper()
    # Verificar futuros GC explícitos (incluyendo símbolos como GC1! o GC=F donde '!' o '=' no son word chars)
    if re.search(r"(GC1!|GC=F|\bGC\s+FUTURES|\bFUTUROS?\s+(?:DE\s+)?(?:ORO\s+)?GC\b|\bCOMEX\s+GC\b|\bGC[FGHJKMNQUVXZ]\d{1,2}\b)", upper):
        return "GC"
    if re.search(r"\bGC\b", upper):
        return "GC"
    # Verificar XAUUSD / Oro explícito
    if re.search(r"(XAU\s*/?\s*USD|XAUUSD|GOLD|ORO\b)", upper):
        return "XAUUSD"
    # Si el canal es exclusivamente de oro (ej. @tagsignals) y los precios son de rango XAUUSD
    if default_channel_is_gold:
        return "XAUUSD"
    return None


def _detect_direction(text: str) -> Optional[str]:
    upper = text.upper()
    buy_match = re.search(
        r"\b(BUY|COMPRA|COMPRAR|LONG|ALCISTA|BUY\s+LIMIT|BUY\s+STOP|BUY\s+NOW)\b",
        upper,
    )
    sell_match = re.search(
        r"\b(SELL|VENTA|VENDER|SHORT|BAJISTA|SELL\s+LIMIT|SELL\s+STOP|SELL\s+NOW)\b",
        upper,
    )
    if buy_match and not sell_match:
        return "COMPRA"
    if sell_match and not buy_match:
        return "VENTA"
    if buy_match and sell_match:
        # Tomar el que aparezca primero en el encabezado del mensaje
        return "COMPRA" if buy_match.start() < sell_match.start() else "VENTA"
    return None


def _extract_stop_loss(text: str) -> Optional[float]:
    patterns = [
        r"(?:STOP\s*LOSS|STOPLOSS|\bS\.?L\.?\b)\s*[:=@\-–—]?\s*(\d[\d.,]*)",
        r"🛑\s*(?:SL|STOP\s*LOSS)?\s*[:=@\-–—]?\s*(\d[\d.,]*)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            val = _clean_number(m.group(1))
            if val is not None:
                return val
    return None


def _extract_take_profits(text: str, entry_ref: Optional[float], direction: Optional[str]) -> list[float]:
    tps: list[float] = []

    # 1. Buscar líneas con TP / Take Profit / Target / Objetivo
    tp_line_pattern = re.compile(
        r"(?:TAKE\s*PROFIT\s*\d*|\bT\.?P\.?\s*\d*|\bTARGET\s*\d*|\bOBJETIVO\s*\d*|🎯)\s*[:=@\-–—]?\s*([^\n\r]+)",
        flags=re.IGNORECASE,
    )
    for m in tp_line_pattern.finditer(text):
        line_tail = m.group(1)
        # Evitar capturar si la línea dice "TP1 HIT" sin un precio real de oro
        if re.search(r"\b(HIT|REACHED|DONE|PIPS)\b", line_tail, flags=re.IGNORECASE):
            # Aún así revisar si hay un precio válido (1000..10000)
            pass
        nums = re.findall(r"\d{4}(?:[.,]\d{1,2})?", line_tail)
        for n in nums:
            val = _clean_number(n)
            if val is not None and val not in tps:
                tps.append(val)

    # 2. Si hay dirección y entrada, validar que los TPs estén del lado correcto
    if entry_ref is not None and direction in ("COMPRA", "VENTA"):
        valid_tps = []
        for tp in tps:
            if direction == "COMPRA" and tp > entry_ref:
                valid_tps.append(tp)
            elif direction == "VENTA" and tp < entry_ref:
                valid_tps.append(tp)
        valid_tps.sort(reverse=(direction == "VENTA"))
        return valid_tps[:4]

    return tps[:4]


def _extract_entry(text: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Devuelve (entry_price, entry_range_low, entry_range_high).
    Soporta tanto precio único ('Entry: 2650.5') como zona/rango ('Buy Gold 2650 - 2646').
    """
    # 1. Buscar etiqueta explícita de entrada o zona con rango
    range_patterns = [
        r"(?:ENTRY\s*(?:ZONE|PRICE)?|ENTRADA|ZONA(?:\s+DE\s+(?:COMPRA|VENTA|ENTRADA))?|PRICE|PRECIO|@)\s*[:=@\-–—]?\s*(\d{4}(?:[.,]\d{1,2})?)\s*(?:[-–—/]|TO|A)\s*(\d{4}(?:[.,]\d{1,2})?)",
        r"(?:BUY|SELL|COMPRA|COMPRAR|VENTA|VENDER|LONG|SHORT)\s+(?:XAU/?USD|GOLD|ORO|GC(?:1!|=F)?|NOW|LIMIT|STOP|ZONE)?\s*(?:@|AT|EN|ZONE|ZONA|:)?\s*(\d{4}(?:[.,]\d{1,2})?)\s*(?:[-–—/]|TO|A)\s*(\d{4}(?:[.,]\d{1,2})?)",
        r"(?:XAU/?USD|GOLD|ORO|GC)\s+(?:BUY|SELL|COMPRA|VENTA|LONG|SHORT)\s*(?:NOW|LIMIT|STOP|ZONE|@|:)?\s*(\d{4}(?:[.,]\d{1,2})?)\s*(?:[-–—/]|TO|A)\s*(\d{4}(?:[.,]\d{1,2})?)",
    ]
    for pat in range_patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            v1 = _clean_number(m.group(1))
            v2 = _clean_number(m.group(2))
            if v1 is not None and v2 is not None and abs(v1 - v2) <= 60:
                low, high = min(v1, v2), max(v1, v2)
                mid = round((low + high) / 2.0, 2)
                return mid, low, high

    # 2. Buscar precio único tras etiqueta de entrada o junto a la orden
    single_patterns = [
        r"(?:ENTRY\s*(?:PRICE)?|ENTRADA|PRECIO(?:\s+DE\s+ENTRADA)?|ENTER(?:\s+AT)?)\s*[:=@\-–—]?\s*(\d{4}(?:[.,]\d{1,2})?)",
        r"(?:BUY|SELL|COMPRA|COMPRAR|VENTA|VENDER|LONG|SHORT)\s+(?:XAU/?USD|GOLD|ORO|GC(?:1!|=F)?)?\s*(?:NOW|LIMIT|STOP)?\s*(?:@|AT|EN|:|-)?\s*(\d{4}(?:[.,]\d{1,2})?)",
        r"(?:XAU/?USD|GOLD|ORO|GC(?:1!|=F)?)\s*(?:[-–—:]|\s+)?\s*(?:BUY|SELL|COMPRA|VENTA|LONG|SHORT)\s*(?:NOW|LIMIT|STOP)?\s*(?:@|AT|EN|:|-)?\s*(\d{4}(?:[.,]\d{1,2})?)",
    ]
    for pat in single_patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            val = _clean_number(m.group(1))
            if val is not None:
                return val, val, val

    return None, None, None


def parse_signal_message(raw_text: str, default_channel_is_gold: bool = True) -> ParsedSignalResult:
    """
    Analiza un mensaje de texto libre de Telegram para detectar una señal de trading de oro.
    Nunca inventa datos: si falta dirección, entrada o al menos un SL/TP coherente,
    devuelve is_parsed=False con el motivo en parse_notes.
    """
    if not raw_text or not raw_text.strip():
        return ParsedSignalResult(is_parsed=False, parse_notes="Mensaje vacío")

    text = raw_text.strip()

    # Filtrar mensajes que son claramente actualizaciones o resúmenes de resultados pasados sin nueva orden
    # (Por ejemplo: "TP1 HIT +50 PIPS 🔥" cuando no trae SL ni estructura completa)
    direction = _detect_direction(text)
    if not direction:
        return ParsedSignalResult(
            is_parsed=False,
            parse_notes="Sin dirección de operación (Compra/Venta no detectada)",
        )

    instrument = _detect_instrument(text, default_channel_is_gold=default_channel_is_gold)
    if not instrument:
        return ParsedSignalResult(
            is_parsed=False,
            direction=direction,
            parse_notes="Instrumento de oro (XAUUSD / GC) no identificado",
        )

    entry_price, entry_low, entry_high = _extract_entry(text)
    if entry_price is None:
        return ParsedSignalResult(
            is_parsed=False,
            direction=direction,
            instrument=instrument,
            parse_notes="Precio de entrada no encontrado o fuera de rango válido",
        )

    stop_loss = _extract_stop_loss(text)
    take_profits = _extract_take_profits(text, entry_ref=entry_price, direction=direction)

    # Validar coherencia del Stop Loss respecto a la entrada y dirección
    if stop_loss is not None:
        if direction == "COMPRA" and stop_loss >= entry_price:
            return ParsedSignalResult(
                is_parsed=False,
                direction=direction,
                instrument=instrument,
                parse_notes=f"Inconsistencia: COMPRA con SL ({stop_loss}) >= Entrada ({entry_price})",
            )
        if direction == "VENTA" and stop_loss <= entry_price:
            return ParsedSignalResult(
                is_parsed=False,
                direction=direction,
                instrument=instrument,
                parse_notes=f"Inconsistencia: VENTA con SL ({stop_loss}) <= Entrada ({entry_price})",
            )

    # Exigir tanto Stop Loss como al menos un Take Profit para considerarla señal operativa completa
    if stop_loss is None and not take_profits:
        return ParsedSignalResult(
            is_parsed=False,
            direction=direction,
            instrument=instrument,
            entry_price=entry_price,
            parse_notes="Mensaje sin Stop Loss ni Take Profit identificables",
        )

    if stop_loss is None:
        return ParsedSignalResult(
            is_parsed=False,
            direction=direction,
            instrument=instrument,
            entry_price=entry_price,
            take_profits=take_profits,
            parse_notes="Señal incompleta: falta Stop Loss",
        )

    if not take_profits:
        return ParsedSignalResult(
            is_parsed=False,
            direction=direction,
            instrument=instrument,
            entry_price=entry_price,
            stop_loss=stop_loss,
            parse_notes="Señal incompleta: falta Take Profit",
        )

    return ParsedSignalResult(
        is_parsed=True,
        direction=direction,
        instrument=instrument,
        entry_price=entry_price,
        entry_range_low=entry_low,
        entry_range_high=entry_high,
        stop_loss=stop_loss,
        take_profits=take_profits,
        parse_notes="Señal interpretada correctamente",
    )
