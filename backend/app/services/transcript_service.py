"""
transcript_service.py

Responsible ONLY for merging Whisper's transcribed segments with
PyAnnote's speaker segments into a single speaker-labelled transcript.

This module does not call Whisper or PyAnnote itself. It's a pure
merge step: it takes two already-computed lists and combines them.
Whisper and PyAnnote code are untouched.
"""


def _overlap_seconds(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """
    Return how many seconds two time windows [a_start, a_end] and
    [b_start, b_end] overlap. Returns 0.0 if they don't overlap at all.
    """
    overlap_start = max(a_start, b_start)
    overlap_end = min(a_end, b_end)
    return max(0.0, overlap_end - overlap_start)


def _nearest_speaker(segment: dict, speaker_segments: list[dict]) -> str:
    """
    Fallback used only when a Whisper segment has ZERO time overlap
    with any diarization turn (e.g. Whisper transcribed through a
    brief pause that PyAnnote treated as a gap between speakers).

    Picks whichever speaker segment is closest in time to this
    segment's midpoint, rather than giving up and returning UNKNOWN.
    This is what eliminates almost all UNKNOWN labels in practice.
    """
    if not speaker_segments:
        return "UNKNOWN"

    midpoint = (segment["start"] + segment["end"]) / 2

    def distance_to(speaker_segment: dict) -> float:
        if midpoint < speaker_segment["start"]:
            return speaker_segment["start"] - midpoint
        if midpoint > speaker_segment["end"]:
            return midpoint - speaker_segment["end"]
        return 0.0  # midpoint is actually inside this segment

    closest = min(speaker_segments, key=distance_to)
    return closest["speaker"]


def _find_speaker_by_overlap(segment: dict, speaker_segments: list[dict]) -> str:
    """
    Assign a speaker to a Whisper segment by finding which PyAnnote
    speaker segment shares the MOST time with it — not just which one
    contains the midpoint.

    This matters because a single Whisper segment can legitimately
    span a speaker change (e.g. "...that's all my updates. Okay
    thanks!" spoken by two different people back to back). Overlap
    duration picks the speaker who dominates that segment, which is
    both more accurate and never leaves genuine silence-gap segments
    unlabeled (see _nearest_speaker fallback below).

    Returns:
        The speaker label with the greatest overlap, or the nearest
        speaker by time if there's no overlap at all, or "UNKNOWN"
        only if speaker_segments is completely empty (diarization
        found no speakers whatsoever).
    """
    best_speaker = None
    best_overlap = 0.0

    for speaker_segment in speaker_segments:
        overlap = _overlap_seconds(
            segment["start"], segment["end"],
            speaker_segment["start"], speaker_segment["end"],
        )
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = speaker_segment["speaker"]

    if best_speaker is not None:
        return best_speaker

    return _nearest_speaker(segment, speaker_segments)


def merge_transcript(whisper_segments: list[dict], speaker_segments: list[dict]) -> list[dict]:
    """
    Merge Whisper's timestamped text segments with PyAnnote's speaker
    segments into one speaker-labelled transcript, using maximum-
    overlap matching (see _find_speaker_by_overlap).

    Args:
        whisper_segments: list of {"start": float, "end": float, "text": str}
        speaker_segments: list of {"speaker": str, "start": float, "end": float}

    Returns:
        list of {"speaker": str, "start": float, "end": float, "text": str},
        one entry per Whisper segment, in the same order.
    """
    merged_transcript: list[dict] = []

    for segment in whisper_segments:
        speaker = _find_speaker_by_overlap(segment, speaker_segments)

        merged_transcript.append({
            "speaker": speaker,
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"],
        })

    return merged_transcript


def group_consecutive_speakers(merged_transcript: list[dict]) -> list[dict]:
    """
    Combine consecutive entries from the same speaker into a single
    entry, so a speaker's whole turn reads as one block instead of
    one line per Whisper segment.

    Example:
        SPEAKER_02: "Hello."
        SPEAKER_02: "How are you?"
        SPEAKER_02: "Let's begin."
    becomes:
        SPEAKER_02: "Hello. How are you? Let's begin."

    Args:
        merged_transcript: output of merge_transcript()

    Returns:
        A new list, same shape as merged_transcript, with adjacent
        same-speaker entries combined. start/end span the full turn.
    """
    if not merged_transcript:
        return []

    grouped: list[dict] = []
    current_turn = dict(merged_transcript[0])

    for entry in merged_transcript[1:]:
        if entry["speaker"] == current_turn["speaker"]:
            # Same speaker as the running turn — extend it.
            current_turn["end"] = entry["end"]
            current_turn["text"] = f"{current_turn['text'].strip()} {entry['text'].strip()}".strip()
        else:
            # Speaker changed — close out the current turn and start a new one.
            grouped.append(current_turn)
            current_turn = dict(entry)

    grouped.append(current_turn)
    return grouped


def print_merged_transcript(merged_transcript: list[dict]) -> None:
    """
    Print a speaker-labelled transcript to the terminal for manual
    verification. Works on either merge_transcript()'s raw output or
    group_consecutive_speakers()'s grouped output — same shape.

    Output format:
        ------------------------------------
        SPEAKER_00
        0.00 --> 2.45
        Hello everyone.
        SPEAKER_01
        2.45 --> 6.10
        Good morning.
        ------------------------------------
    """
    print("------------------------------------")
    for entry in merged_transcript:
        print(entry["speaker"])
        print(f"{entry['start']:.2f} --> {entry['end']:.2f}")
        print(entry["text"].strip())
    print("------------------------------------")