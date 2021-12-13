import os
import motor.motor_asyncio

from typing import List
from datetime import datetime
from fastapi import FastAPI, Body, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from tools import generate_hash_pass
from models import (
    LoginModel, UserModel, CreateUserModel, UpdateUserModel, RoleEnum
)

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(
    os.environ["ME_CONFIG_MONGODB_URL"])
db = client['users']


@app.middleware("http")
async def verify_request(request: Request, call_next):
    if request.method == 'PUT':
        hashed_pass = request.headers.get('hashed_pass')
        user = await db["users"].find_one({"hashed_pass": hashed_pass})
        if user is not None and user['role'] in [RoleEnum.admin, RoleEnum.dev]:
            response = await call_next(request)
        else:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN,
                                content={"detail": "User doesn't have the privelage."})
    elif request.method == 'DELETE':
        hashed_pass = request.headers.get('hashed_pass')
        user = await db["users"].find_one({"hashed_pass": hashed_pass})
        if user is not None and user['role'] == RoleEnum.admin:
            response = await call_next(request)
        else:
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN,
                                content={"detail": "User doesn't have the privelage."})
    else:
        response = await call_next(request)
    return response


@app.post(
    "/login", response_description="Login"
)
async def login(user: LoginModel):
    user = jsonable_encoder(user)
    hash_pass = generate_hash_pass(user['hashed_pass'])
    print(user)

    user = await db["users"].find_one({
        "first_name": user['first_name'],
        "last_name": user['last_name'],
        "hashed_pass": hash_pass
    })

    if user is not None:
        if user['is_active'] == False:
            user['is_active'] = True
            user['last_login'] = datetime.utcnow()
            await db["users"].update_one({"_id": user["_id"]}, {"$set": user})
        return JSONResponse(status_code=status.HTTP_201_CREATED,
                            content={'hash_pass': hash_pass})
    raise HTTPException(status_code=401, detail="Incorrect credentials.")


@app.get(
    "/logout", response_description="Login"
)
async def logout(request: Request):
    hashed_pass = request.headers.get('hashed_pass')
    user = await db["users"].find_one({"hashed_pass": hashed_pass})
    if user['is_active'] == True:
        user['is_active'] = False
        await db["users"].update_one({"_id": user["_id"]}, {"$set": user})
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/", response_description="List all users", response_model=List[UserModel]
)
async def list_users():
    users = await db["users"].find().to_list(1000)
    return users


@app.get(
    "/{id}", response_description="Get a single user", response_model=UserModel
)
async def show_user(id: str):
    if (user := await db["users"].find_one({"_id": id})) is not None:
        return user

    raise HTTPException(status_code=404, detail=f"user {id} not found")


@app.post("/", response_description="Add new user", response_model=UserModel)
async def create_user(user: CreateUserModel = Body(...)):
    user = jsonable_encoder(user)
    new_user = await db["users"].insert_one(user)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@app.put("/{id}", response_description="Update a user", response_model=UserModel)
async def update_user(id: str, user: UpdateUserModel = Body(...)):
    user = {k: v for k, v in user.dict().items() if v is not None}

    if len(user) >= 1:
        update_result = await db["users"].update_one({"_id": id}, {"$set": user})

        if update_result.modified_count == 1:
            if (
                updated_user := await db["users"].find_one({"_id": id})
            ) is not None:
                return updated_user

    if (existing_user := await db["users"].find_one({"_id": id})) is not None:
        return existing_user

    raise HTTPException(status_code=404, detail=f"user {id} not found")


@app.delete("/{id}", response_description="Delete a user")
async def delete_user(id: str):
    delete_result = await db["users"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"user {id} not found")
