"""Semantic Effect Tailor for Techno Ravan / Vibha Effects.

Analyzes scene speech, topic, and creator branding to author meaningful,
tailored effect parameters (text, metrics, labels, kinetic words, and options)
for all studio effects, eliminating generic template placeholders.
"""

import re
from typing import Dict, Any, Optional

def extract_numbers_and_keywords(speech: str, topic: str = ""):
    text = (speech + " " + topic).strip()
    
    # Extract numbers (e.g. "10 years", "500k", "100%", "3 apps")
    nums = re.findall(r"\b\d+[\w%+]*\b", text)
    primary_num = nums[0] if nums else "01"
    
    # Clean words
    words = [w.strip(".,!?:;\"'()[]{}") for w in speech.split() if len(w.strip(".,!?:;\"'()[]{}")) > 2]
    
    # Topic words
    topic_words = [w.strip(".,!?:;\"'()[]{}") for w in topic.split() if len(w.strip(".,!?:;\"'()[]{}")) > 2]
    
    return {
        "primary_num": primary_num,
        "all_nums": nums,
        "words": words,
        "topic_words": topic_words,
    }

def tailor_effect_options(
    effect_id_or_name: str,
    speech: str = "",
    topic: str = "",
    creator: str = "Nayan",
    handle: str = "@TechnoRavan",
    channel: str = "Techno Ravan",
    existing_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate meaningful, contextual options for any effect."""
    options = dict(existing_options or {})
    
    name = str(effect_id_or_name).lower().strip()
    speech_clean = speech.strip()
    topic_clean = topic.strip()
    
    extracted = extract_numbers_and_keywords(speech_clean, topic_clean)
    num = extracted["primary_num"]
    
    # 23: glass-widgets
    if name in ("23", "glass-widgets", "glass", "widgets"):
        options.setdefault("title", "Experience" if "year" in speech_clean.lower() else "System")
        options.setdefault("text", f"{num}+" if num.isdigit() else num)
        
        if "mobile" in speech_clean.lower() or "app" in speech_clean.lower():
            options.setdefault("sub", "Years|Mobile Apps" if "year" in speech_clean.lower() else "Mobile|Production")
            options.setdefault("label", "Mobile Architecture")
            options.setdefault("card_title", "Production Apps")
            options.setdefault("event", "Production Systems · iOS & Android")
        elif "ai" in speech_clean.lower() or "agent" in speech_clean.lower():
            options.setdefault("sub", "AI Systems|Autonomous")
            options.setdefault("label", "AI Engineering")
            options.setdefault("card_title", "Agent Workflows")
            options.setdefault("event", "Production AI Agents")
        else:
            options.setdefault("sub", "Engineering|Architecture")
            options.setdefault("label", "System Architecture")
            options.setdefault("card_title", "Core Systems")
            options.setdefault("event", f"{topic_clean or channel} · Engineering")
            
        options.setdefault("name", creator or "Nayan")
        options.setdefault("handle", handle or "@TechnoRavan")
        options.setdefault("status_title", "Architecture")
        options.setdefault("card_stat", f"{num} YRS" if "year" in speech_clean.lower() else f"{num}X")
        options.setdefault("media_tag", channel.upper() if channel else "TECHNO RAVAN")
        options.setdefault("song", "System Design")
        options.setdefault("day", "EXP")
        options.setdefault("date", num if num.isdigit() else "01")
        return options

    # 46: spotlight / tape-label
    if name in ("46", "tape-label", "tape", "spotlight"):
        if "year" in speech_clean.lower() and num.isdigit():
            options.setdefault("text", f"{num} YEARS EXP")
        elif topic_clean:
            options.setdefault("text", topic_clean.upper()[:24])
        else:
            options.setdefault("text", "CORE ARCHITECTURE")
        return options

    # 6: backdrop-word
    if name in ("6", "backdrop-word"):
        if "mobile" in speech_clean.lower():
            options.setdefault("text", "MOBILE")
        elif "app" in speech_clean.lower():
            options.setdefault("text", "APPS")
        elif "arch" in speech_clean.lower():
            options.setdefault("text", "SYSTEMS")
        elif topic_clean:
            options.setdefault("text", topic_clean.split()[0].upper())
        else:
            options.setdefault("text", "ENGINEER")
        return options

    # 24: red-collage
    if name in ("24", "red-collage"):
        options.setdefault("text", "MOBILE" if "mobile" in speech_clean.lower() else "SYSTEMS")
        if "year" in speech_clean.lower():
            options.setdefault("lines", f"{num} YEARS.|PRODUCTION APPS.|REAL ARCHITECTURE.")
        else:
            options.setdefault("lines", "DESIGN.|ENGINEER.|SCALE.")
        return options

    # 25: split-headline
    if name in ("25", "split-headline"):
        if "year" in speech_clean.lower():
            options.setdefault("text", f"{num} Years Building|Mobile Apps")
            options.setdefault("hl", "Mobile")
        elif topic_clean:
            parts = topic_clean.split()
            mid = max(1, len(parts)//2)
            options.setdefault("text", f"{' '.join(parts[:mid])}|{' '.join(parts[mid:])}")
            options.setdefault("hl", parts[mid] if len(parts) > mid else parts[0])
        else:
            options.setdefault("text", "Full Stack|Architecture")
            options.setdefault("hl", "Architecture")
        return options

    # 28: timeline
    if name in ("28", "timeline"):
        options.setdefault("text", "MOBILE ARCHITECTURE" if "mobile" in speech_clean.lower() else "SYSTEM TIMELINE")
        return options

    # 49: huge-strike
    if name in ("49", "huge-strike"):
        options.setdefault("text", f"{num} YEARS" if "year" in speech_clean.lower() else f"{num} APPS")
        return options

    # 2: lineup
    if name in ("2", "lineup"):
        options.setdefault("text", "Architecture|Performance|Scale")
        return options

    # 8: the-bill
    if name in ("8", "the-bill"):
        options.setdefault("text", "Design|Code|Test|Ship")
        return options

    # 11: todo, 36: checklist
    if name in ("11", "todo", "36", "checklist"):
        options.setdefault("text", "Architecture::done|Implementation::done|Production::next")
        return options

    # 16: reel-frame
    if name in ("16", "reel-frame"):
        options.setdefault("text", handle or "@TechnoRavan")
        return options

    # 26: pastel-word
    if name in ("26", "pastel-word"):
        options.setdefault("text", "MOBILE" if "mobile" in speech_clean.lower() else "SYSTEMS")
        options.setdefault("handle", handle or "@TechnoRavan")
        return options

    # 27: check-pills, 40: apple-toggles
    if name in ("27", "check-pills", "40", "apple-toggles"):
        options.setdefault("text", "iOS|Android|Architecture")
        return options

    # 3: locked-on, 5: lean-in, 42: slow-push
    if name in ("3", "locked-on"):
        options.setdefault("zoom", 1.25)
        return options
    if name in ("5", "lean-in"):
        options.setdefault("zoom", 1.35)
        return options

    return options
