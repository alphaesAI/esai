import os
import inspect
import sys

from fastapi import FastAPI, APIRouter, Depends

from ..app import Application

from .factory import APIFactory
from .base import API
from .authorization import Authorization

def get():
    return INSTANCE 

def create():
    dependencies = []
    token = os.environ.get("TOKEN")
    if token:
        dependencies.append(Depends(Authorization(token)))
    
    return FastAPI(lifespan=lifespan, dependencies=dependencies if dependencies else None)

def lifespan(application):
    print("server is started...")

    global INSTANCE

    config = Application.read(os.environ.get("CONFIG"))

    api = os.environ.get("API_CLASS")
    INSTANCE = APIFactory.create(config, api) if api else API(config)
    print("Instance created:", INSTANCE)
    print("Application ID:", id(application))

    routers = apirouters()

    for name, router in routers.items():
        if name in config:
            application.include_router(router)

    yield
    print("server is shutting down")

def apirouters():
    api = sys.modules[".".join(__name__.split(".")[:-1])]

    available = {}
    for name, rclass in inspect.getmembers(api, inspect.ismodule):
        if hasattr(rclass, "router") and isinstance(rclass.router, APIRouter):
            available[name.lower()] = rclass.router

    return available

def start():
    list(lifespan(app))

app, INSTANCE = create(), None