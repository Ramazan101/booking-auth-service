from fastapi import FastAPI
import uvicorn
from booking.api import auth, user

from booking.admin.setup import setup_admin

mini_shop_app = FastAPI(title="Auth User")
mini_shop_app.include_router(auth.auth_router)
mini_shop_app.include_router(user.user_router)
setup_admin(mini_shop_app)

if __name__ == "__main__":
    uvicorn.run("main:mini_shop_app", host="127.0.0.1", port=8001, reload=True)