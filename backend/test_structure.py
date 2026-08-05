from app.llm.model import get_gemini_model
from app.llm.schemas import MeetingIntelligence

model = get_gemini_model().with_structured_output(MeetingIntelligence)

result = model.invoke(
    """
    Meeting:

    John: Finish the report tomorrow.
    Sarah: I agree.
    """
)

print(result)