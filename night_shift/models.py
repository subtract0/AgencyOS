from pydantic import BaseModel
from typing import List


class CycleSummary(BaseModel):
    id: int
    name: str
    status: str


class BacklogCounts(BaseModel):
    high: int
    medium: int
    low: int


class CMPSignal(BaseModel):
    signal: str
    value: float


class GitCommit(BaseModel):
    sha: str
    author: str
    message: str
