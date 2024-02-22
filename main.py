from fastapi import FastAPI
from controller.ad_controller import router as ad_router
from controller.user_controller import router as auth_router
from fastapi import status, Request
from fastapi.responses import JSONResponse
import uvicorn

from service.exception.entity_not_found import EntityNotFound
from service.user_service import InvalidTokenException

app = FastAPI()

app.include_router(ad_router)
app.include_router(auth_router)


@app.middleware("http")
async def general_exception_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except InvalidTokenException:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid authentication token"}
        )
    except EntityNotFound:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Invalid identification for entity"}
        )


if __name__ == "__main__":
    uvicorn.run(app)
