from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class FeedbackOut(BaseModel):
    ok: bool = True
