"""
prompt.py

Contains ONLY PromptTemplate objects used for meeting analysis. No
model or chain-building logic lives here — see model.py and
summarizer.py for that.

Three templates are defined:
- MEETING_ANALYSIS_PROMPT: single-request path for short transcripts.
- MAP_CHUNK_PROMPT: analyzes one chunk of a long transcript in isolation.
- REDUCE_PROMPT: merges several partial analyses into one final result.
"""

from langchain_core.prompts import PromptTemplate

_SHARED_RULES = """Rules you MUST follow:
- Base your answer ONLY on the transcript provided. Never invent names, tasks, dates, or facts that are not clearly present.
- Ignore filler speech, small talk, and off-topic chatter — focus on substantive content.
- If a field has no supporting evidence in the transcript, return an empty list for it (or an empty string, for individual text fields).
- For action items, if the owner or deadline isn't clearly stated, use an empty string rather than guessing."""


MEETING_ANALYSIS_TEMPLATE = f"""You are an experienced Meeting Intelligence Assistant analyzing a business meeting transcript. Your job is to produce an executive summary and extract action items, decisions, deadlines, and key discussion topics.

{_SHARED_RULES}

Transcript:
{{transcript}}
"""

MEETING_ANALYSIS_PROMPT = PromptTemplate.from_template(MEETING_ANALYSIS_TEMPLATE)


MAP_CHUNK_TEMPLATE = f"""You are an experienced Meeting Intelligence Assistant. You are analyzing ONE PART of a longer business meeting transcript (part {{chunk_index}} of {{chunk_total}}). Additional parts exist before and/or after this excerpt, so do not assume this is the entire meeting — just analyze what's in front of you.

{_SHARED_RULES}

Transcript excerpt:
{{transcript}}
"""

MAP_CHUNK_PROMPT = PromptTemplate.from_template(MAP_CHUNK_TEMPLATE)


REDUCE_TEMPLATE = """You are an experienced Meeting Intelligence Assistant. You are given several partial analyses of ONE business meeting, produced from consecutive chronological excerpts of the same transcript. Combine them into a single, final, de-duplicated meeting intelligence report.

Rules you MUST follow:
- Merge overlapping or duplicate action items, decisions, deadlines, and topics into single entries.
- Preserve chronological order where it's meaningful (e.g. topics should roughly follow the order they were discussed).
- Write ONE cohesive executive summary covering the whole meeting — do not just concatenate the partial summaries.
- Do not invent anything that isn't supported by the partial analyses below.

Partial analyses (in chronological order):
{partial_results}
"""

REDUCE_PROMPT = PromptTemplate.from_template(REDUCE_TEMPLATE)