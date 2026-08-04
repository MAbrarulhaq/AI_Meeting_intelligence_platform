"""
schemas.py

Pydantic models describing the structured output we want Gemini to
return. Passed to ChatGoogleGenerativeAI.with_structured_output(),
so LangChain handles getting the model to conform to this shape —
no manual JSON parsing anywhere in this codebase.
"""

from typing import List

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """A single task assigned during the meeting."""

    owner: str = Field(
        default="",
        description="The person responsible for this task, or an empty string if not specified in the transcript.",
    )
    task: str = Field(
        description="A clear, concise description of what needs to be done.",
    )
    deadline: str = Field(
        default="",
        description="When the task is due, or an empty string if no deadline was mentioned.",
    )


class Decision(BaseModel):
    """A single decision that was made during the meeting."""

    decision: str = Field(
        description="A concise description of a decision that was made during the meeting.",
    )


class Deadline(BaseModel):
    """A single deadline mentioned during the meeting, independent of specific action items."""

    deadline: str = Field(
        description="A concise description of a deadline that was mentioned during the meeting.",
    )


class Topic(BaseModel):
    """A single key topic discussed during the meeting."""

    topic: str = Field(
        description="A short label for a topic that was discussed during the meeting.",
    )


class MeetingIntelligence(BaseModel):
    """
    The complete structured analysis of a meeting (or meeting excerpt,
    when used as a Map-step output — see llm/summarizer.py).
    """

    summary: str = Field(
        description="A concise, professional executive summary of the meeting.",
    )
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="Concrete tasks that were assigned during the meeting.",
    )
    decisions: List[Decision] = Field(
        default_factory=list,
        description="Decisions that were made during the meeting.",
    )
    deadlines: List[Deadline] = Field(
        default_factory=list,
        description="Deadlines that were mentioned, independent of specific action items.",
    )
    key_topics: List[Topic] = Field(
        default_factory=list,
        description="The main topics discussed during the meeting.",
    )