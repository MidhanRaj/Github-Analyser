from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
GITHUB_API = "https://api.github.com/users/"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
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

    # Generate AI Analysis
    ai_analysis = "AI analysis not available."
    if OPENAI_API_KEY:
        try:
            # Prepare per-repo summary text
            repo_summaries = []
            for repo in repos_data:
                repo_name = repo.get("name")
                description = repo.get("description", "No description provided")
                stars_count = repo.get("stargazers_count", 0)
                forks_count = repo.get("forks_count", 0)
                lang = repo.get("language", "Unknown")
                repo_summaries.append(f"""
Repository: {repo_name}
Description: {description}
Stars: {stars_count}, Forks: {forks_count}, Language: {lang}
""")

            all_repos_text = "\n".join(repo_summaries)

            # Build AI prompt
            prompt = f"""
You are a **critical GitHub profile analyzer**. Perform these tasks:

### Part 1: Profile Summary
- Analyze overall GitHub activity for the user.
- Identify strengths and weaknesses in their projects.

### Part 2: Repository Analysis
For EACH repository provided below:
- Give scores (0-10) for **Code Quality**, **Documentation**, **Testing**, **Security**, **Maintainability**.
- Identify at least 2 **critical issues** with severity levels ([CRITICAL], [MAJOR], [MINOR]).
- Suggest at least 2 **improvements** with actionable advice.
- Mention **main strengths** of the repo.
- Provide an **overall verdict in one sentence**.

### Part 3: Language Recommendations
The user primarily uses these languages: {', '.join(languages.keys())}.

Compare these with modern trends and best practices. For any outdated or less trending language:
- Suggest a modern alternative or complementary technology (example: HTML → React with TypeScript, JavaScript → TypeScript, Python → FastAPI, PHP → Laravel, etc.).
- Justify why it's better and how it improves performance, security, or scalability.

### Part 4: Final Summary
- Top 3 strengths overall.
- Top 3 weaknesses overall.
- Overall skill level (Beginner / Intermediate / Advanced) with justification.

### Repositories:
{all_repos_text}

Output in **Markdown** format with clear headings and bullet points.
"""

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI that performs critical GitHub analysis and recommends modern technologies."},
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

