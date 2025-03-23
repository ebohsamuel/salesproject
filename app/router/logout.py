import asyncio
from app.authentication import get_current_active_user
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, status, Depends

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/logout")
async def logout():
    await asyncio.sleep(0)
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token", httponly=True, samesite='strict')
    return response
