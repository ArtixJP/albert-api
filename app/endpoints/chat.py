import uuid
from typing import Optional, Union

from fastapi import APIRouter, Security, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    ChatHistory,
    ChatHistoryResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from app.utils.security import check_api_key, secure_data
from app.utils.lifespan import clients
from app.tools import *
from app.tools import __all__ as tools_list


router = APIRouter()


@router.post("/chat/completions")
@secure_data
async def chat_completions(
    request: ChatCompletionRequest, api_key: str = Security(check_api_key)
) -> ChatCompletionResponse:
    """Completion API similar to OpenAI's API.
    See https://platform.openai.com/docs/api-reference/chat/create for the API specification.
    """

    request = dict(request)
    chat_id = request.pop("id")
    try:
        client = clients["openai"][request["model"]]
    except KeyError:
        raise HTTPException(status_code=404, detail="Model not found.")

    # chat history
    if request["user"]:
        if chat_id:
            chat_history = clients["chathistory"].get_chat_history(
                user_id=request["user"], chat_id=chat_id
            )
            if "messages" in chat_history.keys():  # to avoid empty chat history
                request["messages"] = chat_history["messages"] + request["messages"]
        else:
            chat_id = str(uuid.uuid4())

    # tools
    user_message = request["messages"][-1]  # keep user message without tools for chat history
    tools = request.get("tools")
    if tools:
        for tool in tools:
            if tool["function"]["name"] not in tools_list:
                raise HTTPException(status_code=404, detail="Tool not found")
            func = globals()[tool["function"]["name"]](clients=clients)
            params = request | tool["function"]["parameters"]
            params["api_key"] = api_key
            try:
                prompt = await func.get_prompt(**params)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"tool error {e}")

            request["messages"] = [{"role": "user", "content": prompt}]
        request.pop("tools")

    # non stream case
    if not request["stream"]:
        response = client.chat.completions.create(**request)
        
        # add messages to chat history
        if request["user"]:
            response.id = chat_id

            clients["chathistory"].add_messages(
                user_id=request["user"],
                chat_id=chat_id,
                user_message=user_message,
                assistant_message={
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                },
            )

        return response

    # stream case
    def get_openai_generator(client, **request):
        content = ["" for n in range(request["n"])]
        stream = client.chat.completions.create(**request)
        for event in stream:
            # capture messages for chat history
            message = event.choices[0].delta.content
            message = "" if message is None else message
            content[event.choices[0].index] = content[event.choices[0].index] + message

            event = dict(event)
            if request["user"]:
                event["id"] = chat_id
            event = str(event).replace("None", "null")

            yield "data: " + event + "\n\n"
        yield "data: [DONE] \n\n"

        # add messages to chat history
        if request["user"]:
            clients["chathistory"].add_messages(
                user_id=request["user"],
                chat_id=chat_id,
                user_message=user_message,
                assistant_message={"role": "assistant", "content": content[0]},
            )

    return StreamingResponse(get_openai_generator(client, **request), media_type="text/event-stream")  # fmt: off


@router.get("/chat/history/{user}/{id}")
@router.get("/chat/history/{user}")
@secure_data
async def chat_history(
    user: str, id: Optional[str] = None, api_key: str = Security(check_api_key)
) -> Union[ChatHistoryResponse, ChatHistory]:
    """
    Get chat history of a user.
    """
    chat_history = clients["chathistory"].get_chat_history(user_id=user, chat_id=id)
    
    # @TODO: add pydantic model for chat history
    return chat_history
