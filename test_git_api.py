import requests, server

BASE_URL = server.get_server_ip()

def test_init():
    """Test initializing a Git repository"""
    response = requests.post(f"{BASE_URL}/init")
    print("Init:", response.json())

def test_commit(message : str):
    """Test committing changes"""
    data = {"message": message}
    response = requests.post(f"{BASE_URL}/commit", json=data)
    print("Commit:", response.json())

def test_push(github_url : str):
    """Test pushing to a remote repository"""
    data = {"remote_url": github_url, "branch": "main"}
    response = requests.post(f"{BASE_URL}/push", json=data)
    print("Push:", response.json())

if __name__ == "__main__":
    test_init()
    test_commit("test commit")
    test_push("https://github.com/PanzerTurtle/Dexto-git-test.git")
