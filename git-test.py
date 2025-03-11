from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, git

app = FastAPI()

# Define repository path
REPO_PATH = "repo"

# Ensure the repo directory exists
if not os.path.exists(REPO_PATH):
    os.makedirs(REPO_PATH)

# Initialize the repo if it doesn't exist
try:
    repo = git.Repo(REPO_PATH)
except git.exc.InvalidGitRepositoryError:
    repo = git.Repo.init(REPO_PATH)


class CommitData(BaseModel):
    message: str


class PushData(BaseModel):
    remote_url: str
    branch: str = "main"


@app.post("/init")
def init_repo():
    """Initialize a Git repository"""
    try:
        repo.init(REPO_PATH)
        return {"message": "Repository initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/commit")
def commit_changes(data: CommitData):
    """Commit changes to the repository"""
    try:
        repo.git.add(A=True)  # Add all files
        repo.index.commit(data.message)
        return {"message": f"Committed: {data.message}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/push")
def push_changes(data: PushData):
    """Push changes to a remote repository"""
    try:
        # Set remote if not already set
        if "origin" not in [remote.name for remote in repo.remotes]:
            repo.create_remote("origin", data.remote_url)

        origin = repo.remotes.origin
        origin.push(refspec=f"{data.branch}:{data.branch}")

        return {"message": f"Pushed to {data.remote_url} on branch {data.branch}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
