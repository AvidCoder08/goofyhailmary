import re

# Safely import role config with defaults
try:
    from role_config import SUPERADMIN_IDS, CR_IDS_BY_CLASS
except (ImportError, KeyError, ModuleNotFoundError):
    # Fallback to empty defaults if import fails
    SUPERADMIN_IDS = set()
    CR_IDS_BY_CLASS = {}


def _get_personal(profile):
    if isinstance(profile, dict):
        return profile.get("personal", {})
    return getattr(profile, "personal", {})


def _get_value(personal, key, default=""):
    if isinstance(personal, dict):
        return personal.get(key, default)
    return getattr(personal, key, default)


def get_user_ids(profile):
    personal = _get_personal(profile)
    srn = str(_get_value(personal, "srn", "")).strip()
    email = str(_get_value(personal, "email_id", "")).strip()
    pesu_id = str(_get_value(personal, "pesu_id", "")).strip()
    ids = {srn.lower(), email.lower(), pesu_id.lower()}
    return {i for i in ids if i}


def _normalize_class_part(value: str) -> str:
    value = value.strip()
    return re.sub(r"[^A-Za-z0-9]", "", value)


def get_class_id(profile):
    personal = _get_personal(profile)
    section = str(_get_value(personal, "section", "")).strip()
    semester_raw = str(_get_value(personal, "semester", "")).strip()

    match = re.search(r"\d+", semester_raw)
    semester = match.group(0) if match else semester_raw

    section_clean = _normalize_class_part(section)
    semester_clean = _normalize_class_part(semester)

    return f"Sem{semester_clean}-{section_clean}"


def get_class_id_variants(profile):
    class_id = get_class_id(profile)
    return [class_id]


def get_section_from_class_id(class_id):
    """Extract section from class_id. Format: Sem{semester}-{section}"""
    parts = class_id.split("-")
    if len(parts) >= 2:
        return parts[-1]  # Last part is the section
    return None


def is_superadmin(profile):
    user_ids = get_user_ids(profile)
    return any(uid in {x.lower() for x in SUPERADMIN_IDS} for uid in user_ids)


def is_cr(profile):
    user_ids = get_user_ids(profile)
    class_variants = [cid.lower() for cid in get_class_id_variants(profile)]

    normalized_map = {k.lower(): v for k, v in CR_IDS_BY_CLASS.items()}
    for class_id in class_variants:
        allowed_ids = {x.lower() for x in normalized_map.get(class_id, set())}
        if any(uid in allowed_ids for uid in user_ids):
            return True
    return False
