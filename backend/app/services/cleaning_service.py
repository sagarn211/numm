import re
import pandas as pd

UOM_MAP = {
    "PCS": "EA", "PC": "EA", "PIECE": "EA", "PIECES": "EA", "EACH": "EA",
    "NOS": "EA", "NO": "EA", "KGS": "KG", "MTR": "M", "METER": "M",
    "METRE": "M", "LTR": "L", "LITRE": "L",
}
DESCRIPTION_ABBREVIATIONS = {
    "HEX": "HEXAGONAL", "SS": "STAINLESS STEEL", "MS": "MILD STEEL",
    "CS": "CARBON STEEL", "GI": "GALVANIZED IRON", "DIA": "DIAMETER",
    "ASSY": "ASSEMBLY", "BRG": "BEARING",
}

def clean_text(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = re.sub(r"\s+", " ", str(value).strip())
    return text or None

def clean_description(value):
    text = clean_text(value)
    if not text:
        return None
    return re.sub(r"\s+", " ", text).strip()

def standardize_description(value):
    text = clean_description(value)
    if not text:
        return None
    text = text.upper().replace("*", " X ")
    text = re.sub(r"(?<=\d)\s*(MM|CM|KV|KW|KVA|MVA|RPM|HZ)\b", r" \1", text)
    tokens = []
    for token in re.sub(r"\s+", " ", text).split():
        tokens.extend(DESCRIPTION_ABBREVIATIONS.get(token, token).split())
    return " ".join(tokens)

def normalize_uom(value):
    text = clean_text(value)
    if not text:
        return None
    key = text.upper().replace(".", "")
    return UOM_MAP.get(key, key)

def clean_dataframe(df: pd.DataFrame):
    df = df.copy()
    df.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")
        for c in df.columns
    ]
    return df.where(pd.notnull(df), None)
