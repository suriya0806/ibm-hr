import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"==================================================")
    print(f"🚀 HireMind AI — Intelligent HR Recruitment Assistant")
    print(f"🌐 Server running at: http://localhost:{port}")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=True)

