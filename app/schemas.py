from typing import List
from pydantic import BaseModel


class IssueBase(BaseModel):
    title: str
    description: str | None = None


class IssueCreate(IssueBase):
    pass


class IssueResponse(IssueBase):
    id: int

    class Config:
        from_attributes = True


class IssueListResponse(BaseModel):
    items: List[IssueResponse]

class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    assignee_id: int | None = None
    version: int
class CommentCreate(BaseModel):
    author_id: int
    body: str

class CommentResponse(BaseModel):
    id: int
    author_id: int
    body: str
    created_at: str

    class Config:
        orm_mode = True

class LabelReplace(BaseModel):
    labels: list[str]
from typing import List

class BulkStatusUpdate(BaseModel):
    issue_ids: List[int]
    status: str

class BulkStatusResponse(BaseModel):
    updated: int
    failed: List[int]  # IDs of failed issues
