from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
GITHUB_API = "https://api.github.com/users/"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    username = data.get("username")

    if not username:
        return jsonify({"error": "No username provided"}), 400

    # Fetch GitHub profile data
    user_url = f"{GITHUB_API}{username}"
    repos_url = f"{GITHUB_API}{username}/repos"

    user_res = requests.get(user_url)
    repos_res = requests.get(repos_url)

    if user_res.status_code != 200 or repos_res.status_code != 200:
        return jsonify({"error": "User not found"}), 404

    user_data = user_res.json()
    repos_data = repos_res.json()

    # Calculate stats
    stars = 0
    languages = {}
    for repo in repos_data:
        stars += repo.get("stargazers_count", 0)
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1

    profile_info = {
        "username": username,
        "name": user_data.get("name"),
        "avatar": user_data.get("avatar_url"),
        "bio": user_data.get("bio"),
        "followers": user_data.get("followers"),
        "following": user_data.get("following"),
        "repos": len(repos_data),
        "stars": stars,
        "languages": languages
    }

    # AI Analysis using OpenAI
    ai_analysis = "AI analysis not available."
    if OPENAI_API_KEY:
        try:
            prompt = f"""
            Analyze this GitHub profile:
            Name: {profile_info['name']}
            Followers: {profile_info['followers']}
            Repos: {profile_info['repos']}
            Stars: {profile_info['stars']}
            Languages: {', '.join(languages.keys())}

            Give a short summary of strengths, weaknesses, and main language proficiency.
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI that analyzes GitHub profiles."},
                    {"role": "user", "content": prompt}
                ]
            )
            ai_analysis = response.choices[0].message.content
        except Exception as e:
            ai_analysis = f"AI analysis error: {e}"

    profile_info["ai_analysis"] = ai_analysis
    return jsonify(profile_info)

if __name__ == "__main__":
    app.run(debug=True)

