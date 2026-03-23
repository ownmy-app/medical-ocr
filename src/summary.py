from __future__ import annotations
from typing import List, Dict
from models import TimelineEvent, SummaryArtifacts
from utils import expand_abbreviations_for_summary, join_unique

def craft_summary(events: List[TimelineEvent], artifacts: SummaryArtifacts, max_chars: int = 2000) -> str:
    if not events:
        return "No medical records were available to summarize."
    first_date = next((e.date for e in events if e.date), None)
    last_date  = next((e.date for e in reversed(events) if e.date), None)
    all_dx = join_unique([d for e in events for d in e.diagnoses])
    all_parts = join_unique([bp for e in events for bp in e.body_parts])
    last_restr = artifacts.last_restrictions or "Not documented."
    last_visit = artifacts.last_visit or "Unknown"  # noqa: F841
    mmi_line = artifacts.mmi_found or "Not documented."
    imp_line = artifacts.impairment_found or "Not documented."
    future_needs = join_unique(artifacts.future_needs_snippets, sep=" | ", limit=6)

    # Imaging takeaways
    rad_key = []
    for e in events:
        if e.doc_type == "Radiology Report" and e.plan:
            rad_key.append(e.plan.split("\\n")[0][:240])
    rad_key = join_unique(rad_key, sep=" | ", limit=6)

    # Procedures
    proc_key = []
    for e in events:
        if e.doc_type == "Operative/Procedure Note":
            proc_key.append(e.title.replace("Procedure: ", ""))
    proc_key = join_unique(proc_key, sep=" | ", limit=4)

    # Medications snapshot (last known)
    last_meds = []
    for e in reversed(events):
        if e.meds:
            last_meds = e.meds
            break
    meds_line = join_unique(last_meds, sep=", ", limit=10) or "Not documented."

    bg = []
    if first_date and last_date:
        bg.append(f"The medical records reviewed span {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}.")
    elif last_date:
        bg.append(f"The most recent medical record is dated {last_date.strftime('%Y-%m-%d')}.")
    if all_parts:
        bg.append(f"Body regions involved per records: {all_parts}.")
    if all_dx:
        bg.append(f"Diagnoses noted in provider documentation include: {all_dx}.")

    diag = []
    if rad_key:
        diag.append(f"Key imaging impressions: {rad_key}.")
    if proc_key:
        diag.append(f"Procedures performed: {proc_key}.")

    status = [
        f"Last known work restrictions: {last_restr}.",
        f"MMI status: {mmi_line}.",
        f"Impairment rating: {imp_line}.",
        f"Most recent medications: {meds_line}.",
    ]
    if future_needs:
        status.append(f"Future medical needs considered in the records include: {future_needs}.")

    # Concise recent chronology
    bullets = []
    for e in events[-12:]:
        d = e.date.strftime("%Y-%m-%d") if e.date else "Undated"
        core = []
        if e.diagnoses: 
            core.append(join_unique(e.diagnoses, sep="; ", limit=2))
        if e.plan: 
            core.append(e.plan.split("\\n")[0][:180])
        if e.restrictions: 
            core.append("Restrictions: " + join_unique(e.restrictions, sep="; ", limit=2))
        line = f"{d} | {e.doc_type}: " + " — ".join([c for c in core if c])
        bullets.append(line)

    paragraph = " ".join(bg + diag + status)
    paragraph, used_abbr = expand_abbreviations_for_summary(paragraph)
    artifacts.abbreviations_used = used_abbr

    tail = "\\n".join(f"• {b}" for b in bullets)
    summary = paragraph.strip() + "\\n\\nRecent Key Events:\\n" + tail
    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(" ", 1)[0] + "…"
    return summary


def attorney_faq(events: List[TimelineEvent], artifacts: SummaryArtifacts) -> Dict[str, str]:
    last_visit = artifacts.last_visit or "Unknown"  # noqa: F841
    last_restr = artifacts.last_restrictions or "Not documented."
    last_meds = "Not documented."
    for e in reversed(events):
        if e.meds:
            last_meds = ", ".join(e.meds[:10])
            break
    current_plan = "Not documented."
    for e in reversed(events):
        if e.plan:
            current_plan = e.plan.split("\n")[0][:200]
            break
    return {
    "What treatment to date?": f"{sum(1 for e in events if e.doc_type!='Laboratory Report')} encounters; {sum(1 for e in events if e.doc_type=='Radiology Report')} imaging; {sum(1 for e in events if e.doc_type=='Operative/Procedure Note')} procedures.",
    "Most recent restrictions?": last_restr,
    "Last medications?": last_meds,
    "Last doctor visit?": last_visit,
    "Current treatment plan?": current_plan,
    "MMI reached?": artifacts.mmi_found or "Not documented.",
    "Impairment rating?": artifacts.impairment_found or "Not documented.",
    "Causation statements?": "; ".join(artifacts.causation_statements[:4]) or "Not documented.",
    "Future medical needs?": "; ".join(artifacts.future_needs_snippets[:6]) or "Not documented."
    }