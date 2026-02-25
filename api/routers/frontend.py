import asyncio

from fastapi import APIRouter, HTTPException
from bs4 import BeautifulSoup, Comment
from pydantic import ValidationError as PydanticValidationError
import logging

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"message": "pong"}