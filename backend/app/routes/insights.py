from fastapi import APIRouter

router = APIRouter(prefix="/insights", tags=["insights"])


# ---------------------------------------------------------------------------
# GET /insights
# Returns AI-generated spending insights. Implemented in Phase 5 — see
# app/services/insights_service.py for the OpenAI wiring.
# ---------------------------------------------------------------------------
@router.get("")
def get_insights():
    return {
        "message": "Insights endpoint placeholder — implement AI analysis here!",
        "insights": None,
    }
