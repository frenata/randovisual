import fastapi
import randovisual.extraction.rusa as rusa

router = fastapi.APIRouter(prefix="/extract")

@router.get("/rusa/year/{year}")
async def extract_year(year: int) -> int:
    members = rusa.find_rusa_members(year)
    return len(members)
