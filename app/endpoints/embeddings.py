from fastapi import APIRouter, Security, HTTPException

from app.schemas.embeddings import EmbeddingsRequest, Embeddings
from app.utils.lifespan import clients
from app.utils.security import check_api_key
from app.schemas.config import EMBEDDINGS_MODEL_TYPE

router = APIRouter()


@router.post("/embeddings")
async def embeddings(
    request: EmbeddingsRequest, user: str = Security(check_api_key)
) -> Embeddings:
    """
    Embedding API similar to OpenAI's API.
    See https://platform.openai.com/docs/api-reference/embeddings/create for the API specification.
    """

    request = dict(request)
    client = clients["models"][request["model"]]
    if client.type != EMBEDDINGS_MODEL_TYPE:
        raise HTTPException(status_code=400, detail=f"Model type must be {EMBEDDINGS_MODEL_TYPE}")
    response = client.embeddings.create(**request)

    return response
