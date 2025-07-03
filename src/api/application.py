import os
import sys
import inspect

from fastapi import FastAPI, APIRouter

router = APIRouter()

def create():
    return FastAPI(lifespan=lifespan)

def lifespan(app):
    
    print("server is stared...")

    yield

    print("server is shutting down...")

def start():
    list(lifespan(app))


app = create()