"""Deterministic, family-specific engineering attribute extraction.

These extractors add explicit evidence to the existing hybrid matcher. They do
not infer values that are absent from the source description.
"""
import re


def _value(pattern, text, formatter=lambda match: match.group(1)):
    match = re.search(pattern, text)
    return formatter(match) if match else None


def _keyword(text, choices):
    return next((value for phrase, value in choices if phrase in text), None)


def detect_family(text):
    # Precedence is intentional: "flanged ball valve" is a valve, not a flange.
    rules = [
        (r"\b(?:BALL|GATE|GLOBE|CHECK|BUTTERFLY)?\s*VALVE\b", "VALVE"),
        (r"\b(?:ELECTRIC|INDUCTION|SYNCHRONOUS|ASYNCHRONOUS)?\s*MOTOR\b", "MOTOR"),
        (r"\bBEARING\b|\b(?:[126789]|NU|NJ|NUP)\d{3,4}(?:[- ][A-Z0-9]+)?\b", "BEARING"),
        (r"\b(?:CENTRIFUGAL|RECIPROCATING|GEAR|SCREW|SUBMERSIBLE)?\s*PUMP\b", "PUMP"),
        (r"\bFLANGE\b", "FLANGE"),
        (r"\bPIPE\b|\bTUBE\b", "PIPE"),
        (r"\b(?:BOLT|NUT|WASHER|SCREW)\b", "FASTENER"),
    ]
    return next((family for pattern, family in rules if re.search(pattern, text)), None)


def _material(text):
    return _keyword(text, [
        ("STAINLESS STEEL 316", "SS316"), ("STAINLESS STEEL 304", "SS304"),
        ("SS 316", "SS316"), ("SS316", "SS316"), ("SS 304", "SS304"),
        ("SS304", "SS304"), ("CAST IRON", "CAST IRON"),
        ("DUCTILE IRON", "DUCTILE IRON"), ("CARBON STEEL", "CARBON STEEL"),
        ("MILD STEEL", "MILD STEEL"), ("BRONZE", "BRONZE"),
    ])


def _connection(text):
    return _keyword(text, [
        ("SOCKET WELD", "SOCKET WELD"), ("BUTT WELD", "BUTT WELD"),
        ("THREADED", "THREADED"), ("SCREWED", "THREADED"),
        ("WAFER", "WAFER"), ("LUGGED", "LUGGED"),
        ("FLANGED", "FLANGED"), ("FLANGE", "FLANGED"),
    ])


def _standard(text):
    return _value(r"\b((?:ASME|ANSI|API|ISO|IEC|IS)\s*[A-Z]?[0-9]+(?:\.[0-9]+)?)\b", text,
                  lambda m: re.sub(r"\s+", " ", m.group(1)))


def _nominal_diameter(text):
    return _value(r"\bDN\s*(\d+(?:\.\d+)?)\b", text, lambda m: f"DN{float(m.group(1)):g}")


def _pressure(text):
    pn = _value(r"\bPN\s*(\d+(?:\.\d+)?)\b", text, lambda m: f"PN{float(m.group(1)):g}")
    return pn or _value(r"\b(?:CLASS|CL)\s*(\d+)\b", text, lambda m: f"CLASS{m.group(1)}")


def extract_valve(text):
    return {
        "family": "VALVE",
        "valve_type": _keyword(text, [(f"{name} VALVE", name) for name in ("BALL", "GATE", "GLOBE", "CHECK", "BUTTERFLY")]),
        "nominal_diameter": _nominal_diameter(text),
        "pressure_rating": _pressure(text),
        "body_material": _material(text),
        "connection": _connection(text),
        "standard": _standard(text),
    }


def extract_motor(text):
    power = _value(r"\b(\d+(?:\.\d+)?)\s*(KW|HP)\b", text,
                   lambda m: f"{(float(m.group(1)) if m.group(2) == 'KW' else float(m.group(1)) * 0.7457):.3f}KW")
    voltage = _value(r"\b(\d+(?:\.\d+)?)\s*(KV|V)\b", text,
                     lambda m: f"{float(m.group(1)) * (1000 if m.group(2) == 'KV' else 1):g}V")
    return {
        "family": "MOTOR",
        "motor_type": _keyword(text, [("INDUCTION", "INDUCTION"), ("SYNCHRONOUS", "SYNCHRONOUS"), ("ASYNCHRONOUS", "ASYNCHRONOUS")]),
        "power": power,
        "voltage": voltage,
        "phase": _value(r"\b([13])\s*(?:PH|PHASE)\b", text, lambda m: f"{m.group(1)}PH"),
        "frequency": _value(r"\b(\d+(?:\.\d+)?)\s*HZ\b", text, lambda m: f"{float(m.group(1)):g}HZ"),
        "rpm": _value(r"\b(\d{2,5})\s*RPM\b", text, lambda m: f"{m.group(1)}RPM"),
        "frame": _value(r"\bFRAME\s*([A-Z0-9-]+)\b", text),
        "ip_rating": _value(r"\b(IP\s*\d{2})\b", text, lambda m: re.sub(r"\s+", "", m.group(1))),
        "efficiency_class": _value(r"\bIE\s*([1-5])\b", text, lambda m: f"IE{m.group(1)}"),
    }


def extract_bearing(text):
    designation = _value(r"\b((?:[126789]|NU|NJ|NUP)\d{3,4}(?:[- ]?(?:2RS|RS|ZZ|Z|C3))?)\b", text,
                         lambda m: re.sub(r"\s+", "", m.group(1)))
    dimensions = re.search(r"\b(\d+(?:\.\d+)?)\s*[X×]\s*(\d+(?:\.\d+)?)\s*[X×]\s*(\d+(?:\.\d+)?)\s*MM\b", text)
    return {
        "family": "BEARING",
        "bearing_designation": designation,
        "bearing_type": _keyword(text, [("DEEP GROOVE", "DEEP GROOVE BALL"), ("ROLLER", "ROLLER"), ("THRUST", "THRUST"), ("BALL BEARING", "BALL")]),
        "bore": f"{float(dimensions.group(1)):g}MM" if dimensions else None,
        "outer_diameter": f"{float(dimensions.group(2)):g}MM" if dimensions else None,
        "width": f"{float(dimensions.group(3)):g}MM" if dimensions else None,
        "seal_designation": _value(r"\b(2RS|RS|ZZ|Z)\b", text),
        "manufacturer": _keyword(text, [("SKF", "SKF"), ("FAG", "FAG"), ("NSK", "NSK"), ("TIMKEN", "TIMKEN")]),
    }


def extract_pump(text):
    return {
        "family": "PUMP",
        "pump_type": _keyword(text, [("CENTRIFUGAL", "CENTRIFUGAL"), ("RECIPROCATING", "RECIPROCATING"), ("GEAR PUMP", "GEAR"), ("SCREW PUMP", "SCREW"), ("SUBMERSIBLE", "SUBMERSIBLE")]),
        "flow": _value(r"\b(?:FLOW\s*)?(\d+(?:\.\d+)?)\s*(?:M3/H|M3HR|M³/H)\b", text, lambda m: f"{float(m.group(1)):g}M3/H"),
        "head": _value(r"\b(?:HEAD\s*)?(\d+(?:\.\d+)?)\s*M(?:WC)?\b", text, lambda m: f"{float(m.group(1)):g}M"),
        "power": _value(r"\b(\d+(?:\.\d+)?)\s*KW\b", text, lambda m: f"{float(m.group(1)):g}KW"),
        "rpm": _value(r"\b(\d{2,5})\s*RPM\b", text, lambda m: f"{m.group(1)}RPM"),
        "body_material": _material(text),
        "connection": _connection(text),
    }


def extract_pipe_or_flange(text, family):
    diameter = _nominal_diameter(text) or _value(
        r"\b(\d+(?:\.\d+)?)\s*(?:INCH|IN|\")\b", text,
        lambda m: f"{float(m.group(1)):g}IN",
    ) or _value(r"\b(\d+(?:\.\d+)?)\s*MM\b", text, lambda m: f"{float(m.group(1)):g}MM")
    return {
        "family": family,
        "nominal_diameter": diameter,
        "schedule": _value(r"\b(?:SCH|SCHEDULE)\s*(\d+\s*[A-Z]?)\b", text, lambda m: "SCH" + re.sub(r"\s+", "", m.group(1))),
        "pressure_rating": _pressure(text),
        "body_material": _material(text),
        "standard": _standard(text),
        "connection": _connection(text) or _keyword(text, [("PLAIN END", "PLAIN END"), ("BEVEL END", "BEVEL END")]),
    }


EXTRACTORS = {
    "VALVE": extract_valve,
    "MOTOR": extract_motor,
    "BEARING": extract_bearing,
    "PUMP": extract_pump,
    "PIPE": lambda text: extract_pipe_or_flange(text, "PIPE"),
    "FLANGE": lambda text: extract_pipe_or_flange(text, "FLANGE"),
}


def extract_family_attributes(text):
    family = detect_family(text)
    if not family:
        return {}
    extractor = EXTRACTORS.get(family)
    result = extractor(text) if extractor else {"family": family}
    return {key: value for key, value in result.items() if value is not None}
