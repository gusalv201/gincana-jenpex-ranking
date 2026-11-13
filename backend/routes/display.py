from fastapi import APIRouter

from dependencies import SessionDep
from schemas import DisplayRankingResponse
from services.ranking import get_general_ranking

router = APIRouter(prefix="/display", tags=["display"])


@router.get("/ranking", response_model=DisplayRankingResponse)
async def read_display_ranking(
    session: SessionDep,
) -> DisplayRankingResponse:
    ranking = await get_general_ranking(session)
    return DisplayRankingResponse(ranking=ranking.ranking)
