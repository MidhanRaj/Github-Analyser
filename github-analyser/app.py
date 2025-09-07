from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Serve frontend
@app.route('/')
def home():
    return render_template('index.html')

# GitHub analyze route
@app.route('/analyze/<username>')
def analyze(username):
    url = "https://api.github.com/users/" + username
    r = requests.get(url)
    if r.status_code != 200:
        return jsonify({"error": "User not found"}), 404

    user = r.json()

    r2 = requests.get(user['repos_url'])
    if r2.status_code != 200:
        repos = []
    else:
        repos = r2.json()

    stars = 0
    langs = {}
    for repo in repos:
        stars += repo.get('stargazers_count',0)
        lang = repo.get('language')
        if lang:
            if lang in langs:
                langs[lang] += 1
            else:
                langs[lang] = 1

    data = {
        "username": user['login'],
        "name": user['name'],
        "avatar": user['avatar_url'],
        "bio": user['bio'],
        "followers": user['followers'],
        "following": user['following'],
        "repos": user['public_repos'],
        "stars": stars,
        "languages": langs
    }

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
