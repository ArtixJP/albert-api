from typing import Dict, List, Optional, Union, Literal

from pydantic import BaseModel, Field
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletion,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    ChatCompletionChunk,
)

from app.schemas.tools import ToolOutput


class ChatCompletionRequest(BaseModel):
    messages: List[ChatCompletionMessageParam]
    model: str
    stream: Optional[Literal[True, False]] = False
    frequency_penalty: Optional[float] = 0.0
    max_tokens: Optional[int] = None
    n: Optional[int] = 1
    presence_penalty: Optional[float] = 0.0
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    user: Optional[str] = None
    seed: Optional[int] = None
    stop: Union[Optional[str], List[str]] = Field(default_factory=list)
    tool_choice: Optional[Union[Literal["none"], ChatCompletionToolChoiceOptionParam]] = "none"
    tools: List[ChatCompletionToolParam] = None


class ChatCompletion(ChatCompletion):
    metadata: Optional[List[Dict[str, ToolOutput]]] = []


class ChatCompletionChunk(ChatCompletionChunk):
    metadata: Optional[List[Dict[str, ToolOutput]]] = []
