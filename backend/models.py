from typing import Literal
from pydantic import BaseModel, Field, model_validator, StrictInt

class Question(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=2000)
    type: Literal["single", "multiple", "likert", "short", "long", "number"]
    section: str = ""
    required: bool = True
    options: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def valid_options(self):
        if self.type in ("single", "multiple") and (len(self.options) < 2 or len(set(self.options)) != len(self.options)):
            raise ValueError("ตัวเลือกต้องมีอย่างน้อย 2 ค่าและไม่ซ้ำกัน")
        return self

class Questionnaire(BaseModel):
    title: str = ""
    source: str = ""
    scale_labels: list[str] = Field(default_factory=list, max_length=5)
    version: str = Field(min_length=1, max_length=50)
    questions: list[Question] = Field(max_length=100)

    @model_validator(mode="after")
    def unique(self):
        if len({q.id for q in self.questions}) != len(self.questions):
            raise ValueError("Question IDs must be unique")
        return self

class Task(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=200)
    instruction: str = Field(min_length=1, max_length=2000)
    route: str = Field(pattern=r"^/stimuli/[a-z0-9/_-]+$")
    target: str = Field(min_length=1, max_length=100)
    completion: Literal["target_click", "manual"] = "target_click"
    time_limit: int | None = Field(default=None, ge=5, le=3600)
    targets: list[str] = Field(default_factory=list)
    enabled: bool = True
    source_verified: bool = False

class Protocol(BaseModel):
    version: str = "draft-1"
    information: str = Field(min_length=10, max_length=20000)
    consent: str = Field(min_length=10, max_length=10000)
    retention: str = Field(min_length=5, max_length=5000)
    approved: bool = False

class Config(BaseModel):
    pre: Questionnaire
    post: Questionnaire
    tasks: list[Task]
    protocol: Protocol

    @model_validator(mode="after")
    def unique(self):
        if len({t.id for t in self.tasks}) != len(self.tasks):
            raise ValueError("Task IDs must be unique")
        return self

class CreateSession(BaseModel):
    participant_id: str = Field(pattern=r"^P[0-9]{3,8}$")
    mode: Literal["mock", "hardware"] = "mock"
    condition: Literal["good", "bad", "mixed"] = "good"
    order: Literal["fixed", "random"] = "fixed"
    seed: int | None = None
    random_targets: bool = False
    task_ids: list[str] = Field(min_length=1)

class Event(BaseModel):
    event_id: str = Field(min_length=1, max_length=100)
    event_type: Literal["click", "scroll", "navigation", "viewport"]
    trial_id: str
    timestamp: float = Field(allow_inf_nan=False)
    client_x: float | None = Field(default=None, allow_inf_nan=False)
    client_y: float | None = Field(default=None, allow_inf_nan=False)
    screen_x: float | None = Field(default=None, allow_inf_nan=False)
    screen_y: float | None = Field(default=None, allow_inf_nan=False)
    scroll_x: float = Field(default=0, allow_inf_nan=False)
    scroll_y: float = Field(default=0, allow_inf_nan=False)
    page_url: str = Field(max_length=2000)
    target_element_id: str = Field(default="", max_length=100)
    viewport: dict = Field(default_factory=dict)

class Events(BaseModel):
    events: list[Event] = Field(max_length=500)

class Answers(BaseModel):
    answers: dict[str, str | StrictInt | list[str]]

class Metadata(BaseModel):
    viewport: dict = Field(default_factory=dict)
    synchronization: list[dict] = Field(default_factory=list, max_length=20)

class CalibrationPoint(BaseModel):
    index: int = Field(ge=0, le=4)
    viewport: dict
    presented_at: float = Field(allow_inf_nan=False)


class DraftAnswers(Answers):
    revision: int = Field(ge=0)


class ValidationLimits(BaseModel):
    max_mean_error_norm: float = Field(default=0.04, ge=0.005, le=0.1, allow_inf_nan=False)
    min_valid_fraction: float = Field(default=0.7, ge=0.5, le=1, allow_inf_nan=False)
    min_samples: int = Field(default=20, ge=10, le=1000)

class ExternalSessionRequest(BaseModel):
    track_id: str = Field(pattern=r"^T(?:0[1-9]|[12][0-9]|30)$")
    participant_id: str | None = None
    mode: Literal["mock", "hardware"] = "mock"
    validation_limits: ValidationLimits = Field(default_factory=ValidationLimits)
    native_mouse: bool = True
