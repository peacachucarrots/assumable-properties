from __future__ import annotations
from typing import Iterable, Optional, Any

_DEFAULT_TRUE = {"yes","y","true","t","1","done","complete","completed","x","✓","✔"}
_DEFAULT_FALSE = {"no","n","false","f","0","not done","incomplete"}

def parse_boolish(
    val: Any,
    true_tokens: Iterable[str] = _DEFAULT_TRUE,
    false_tokens: Iterable[str] = _DEFAULT_FALSE,
) -> Optional[bool]:
    if val is None: return None
    s = str(val).strip().lower()
    if not s: return None
    if s in true_tokens: return True
    if s in false_tokens: return False
    if "yes" in s: return True
    if s.startswith("no"): return False
    return None

def to_bool_done(val: Any) -> Optional[bool]:
    return parse_boolish(val)
