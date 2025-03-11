import requests

BASE_URL = "http://127.0.0.1:8000"

def test_init():
    """Test initializing a Git repository"""
    response = requests.post(f"{BASE_URL}/init")
    print("Init:", response.json())

def test_commit():
    """Test committing changes"""
    data = {"message": "Initial commit"}
    response = requests.post(f"{BASE_URL}/commit", json=data)
    print("Commit:", response.json())

def test_push():
    """Test pushing to a remote repository"""
    data = {"remote_url": "https://github.com/PanzerTurtle/Dexto-git-test.git", "branch": "main"}
    response = requests.post(f"{BASE_URL}/push", json=data)
    print("Push:", response.json())

if __name__ == "__main__":
    test_init()
    test_commit()
    test_push()
