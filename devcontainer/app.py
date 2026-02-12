from flask import Flask, request, render_template_string, jsonify
import requests
import base64
import json
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Auto Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }
        h1 { color: #2d3748; margin-bottom: 10px; }
        .form-group { margin-bottom: 25px; }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #4a5568;
        }
        input, textarea {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f7fafc;
            border-radius: 10px;
            display: none;
        }
        .error {
            background: #fed7d7;
            color: #c53030;
        }
        small {
            display: block;
            margin-top: 5px;
            color: #718096;
            font-size: 0.85em;
        }
        a { color: #667eea; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI Auto Panel</h1>
        <p style="margin-bottom: 30px; color: #718096;">Создай репозиторий с кодом за 10 секунд</p>
        
        <form id="generator-form">
            <div class="form-group">
                <label>🔑 OpenRouter API Key</label>
                <input type="password" id="openrouter" placeholder="sk-or-v1-..." required>
                <small>Получить: <a href="https://openrouter.ai/keys" target="_blank">openrouter.ai/keys</a></small>
            </div>

            <div class="form-group">
                <label>🔐 GitHub Token</label>
                <input type="password" id="github" placeholder="github_pat_..." required>
                <small>Нужны права: repo, workflow</small>
            </div>

            <div class="form-group">
                <label>👤 GitHub Username</label>
                <input type="text" id="username" placeholder="your-username" required>
            </div>

            <div class="form-group">
                <label>🧠 Что нужно создать?</label>
                <textarea id="prompt" placeholder="Например: личный сайт с портфолио, тёмная тема, три секции: о себе, проекты, контакты" rows="5" required></textarea>
            </div>

            <button type="submit" id="submit-btn">
                <span>✨ Создать проект</span>
                <span class="loader" style="display: none;"> ⏳</span>
            </button>
        </form>

        <div id="result" class="result">
            <h3 style="color: #2f855a; margin-bottom: 15px;">✅ Проект создан!</h3>
            <p style="margin-bottom: 10px;"><strong>📦 GitHub:</strong><br><a id="github-link" target="_blank"></a></p>
            <p style="margin-bottom: 20px;"><strong>🌐 GitHub Pages:</strong><br><a id="site-link" target="_blank"></a></p>
            <button onclick="location.reload()" style="background: #4a5568;">Создать ещё</button>
        </div>

        <div id="error" class="result error">
            <h3 style="color: #c53030; margin-bottom: 15px;">❌ Ошибка</h3>
            <p id="error-message"></p>
        </div>
    </div>

    <script>
        document.getElementById('generator-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btn = document.getElementById('submit-btn');
            const btnText = btn.querySelector('span:first-child');
            const loader = btn.querySelector('.loader');
            const resultDiv = document.getElementById('result');
            const errorDiv = document.getElementById('error');

            btnText.style.display = 'none';
            loader.style.display = 'inline';
            resultDiv.style.display = 'none';
            errorDiv.style.display = 'none';

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        openrouter: document.getElementById('openrouter').value,
                        github: document.getElementById('github').value,
                        username: document.getElementById('username').value,
                        prompt: document.getElementById('prompt').value
                    })
                });

                const data = await response.json();

                if (data.success) {
                    document.getElementById('github-link').href = data.github_url;
                    document.getElementById('github-link').textContent = data.github_url;
                    document.getElementById('site-link').href = data.url;
                    document.getElementById('site-link').textContent = data.url;
                    resultDiv.style.display = 'block';
                } else {
                    document.getElementById('error-message').textContent = data.error || 'Неизвестная ошибка';
                    errorDiv.style.display = 'block';
                }
            } catch (err) {
                document.getElementById('error-message').textContent = err.message;
                errorDiv.style.display = 'block';
            } finally {
                btnText.style.display = 'inline';
                loader.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

def gh_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

def generate_project(prompt, key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    system = """Ты — генератор проектов. Ответь только JSON:
{
  "repo_name": "короткое-название-проекта",
  "files": {
    "index.html": "<html>...</html>",
    "style.css": "body { ... }",
    "README.md": "# Название\\n\\nОписание"
  }
}"""

    data = {
        "model": "deepseek/deepseek-r1-0528:free",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        key = data["openrouter"]
        gh = data["github"]
        user = data["username"]
        prompt = data["prompt"]

        project = generate_project(prompt, key)
        
        if "error" in project:
            return jsonify({"error": project["error"]}), 400

        repo = project["repo_name"]
        repo = repo.lower().replace(" ", "-").replace("_", "-")

        # Создаём репозиторий
        create_repo = requests.post(
            "https://api.github.com/user/repos",
            headers=gh_headers(gh),
            json={"name": repo, "private": False, "auto_init": True}
        )
        
        if create_repo.status_code not in [201, 422]:
            return jsonify({"error": f"GitHub error: {create_repo.status_code}"}), 400

        # Загружаем файлы
        for path, content in project["files"].items():
            encoded = base64.b64encode(content.encode()).decode()
            requests.put(
                f"https://api.github.com/repos/{user}/{repo}/contents/{path}",
                headers=gh_headers(gh),
                json={
                    "message": f"Add {path}",
                    "content": encoded,
                    "branch": "main"
                }
            )

        # Включаем GitHub Pages
        requests.post(
            f"https://api.github.com/repos/{user}/{repo}/pages",
            headers=gh_headers(gh),
            json={"source": {"branch": "main", "path": "/"}}
        )

        return jsonify({
            "success": True,
            "repo": repo,
            "url": f"https://{user}.github.io/{repo}",
            "github_url": f"https://github.com/{user}/{repo}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
