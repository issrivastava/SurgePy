from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

app = FastAPI()   # 👈 MUST come before routes


@app.get("/issues", response_model=schemas.IssueListResponse)
def list_issues(db: Session = Depends(get_db)):
    issues = db.query(models.Issue).all()
    return {"items": issues}
from fastapi import HTTPException

@app.get("/issues/{issue_id}", response_model=schemas.IssueResponse)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(models.Issue).filter(models.Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return issue
@app.patch("/issues/{issue_id}", response_model=schemas.IssueResponse)
def update_issue(
    issue_id: int,
    issue_data: schemas.IssueUpdate,
    db: Session = Depends(get_db)
):
    issue = db.query(models.Issue).filter(models.Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(404, "Issue not found")

    if issue.version != issue_data.version:
        raise HTTPException(409, "Version conflict")

    update_fields = issue_data.dict(exclude={"version"}, exclude_unset=True)

    for key, value in update_fields.items():
        setattr(issue, key, value)

    issue.version += 1

    db.commit()
    db.refresh(issue)

    return issue
@app.post("/issues/{issue_id}/comments", response_model=schemas.CommentResponse)
def add_comment(
    issue_id: int,
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db)
):
    issue = db.query(models.Issue).filter(models.Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")

    if not comment.body.strip():
        raise HTTPException(400, "Comment body cannot be empty")

    author = db.query(models.User).filter(models.User.id == comment.author_id).first()
    if not author:
        raise HTTPException(400, "Invalid author")

    new_comment = models.Comment(
        issue_id=issue_id,
        author_id=comment.author_id,
        body=comment.body
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment

@app.put("/issues/{issue_id}/labels")
def replace_labels(
    issue_id: int,
    data: schemas.LabelReplace,
    db: Session = Depends(get_db)
):
    issue = db.query(models.Issue).filter(models.Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")

    try:
        with db.begin():
            # Remove existing labels
            db.query(models.IssueLabel).filter(
                models.IssueLabel.issue_id == issue_id
            ).delete()

            for label_name in data.labels:
                label = db.query(models.Label).filter(
                    models.Label.name == label_name
                ).first()

                if not label:
                    label = models.Label(name=label_name)
                    db.add(label)
                    db.flush()  # get label.id

                issue_label = models.IssueLabel(
                    issue_id=issue_id,
                    label_id=label.id
                )
                db.add(issue_label)

    except Exception:
        raise HTTPException(400, "Failed to replace labels")

    return {"message": "Labels updated successfully"}
from sqlalchemy.exc import SQLAlchemyError

@app.post("/issues/bulk-status", response_model=schemas.BulkStatusResponse)
def bulk_status_update(
    data: schemas.BulkStatusUpdate,
    db: Session = Depends(get_db)
):
    failed = []
    updated_count = 0

    try:
        with db.begin():  # Transaction block
            for issue_id in data.issue_ids:
                issue = db.query(models.Issue).filter(models.Issue.id == issue_id).first()
                if not issue:
                    failed.append(issue_id)
                else:
                    issue.status = data.status
                    issue.version += 1
                    updated_count += 1

            if failed:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to update issues: {failed}"
                )
        return {"updated": updated_count, "failed": failed}

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Transaction failed, rolled back")
