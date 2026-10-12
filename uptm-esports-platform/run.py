import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    print(f"\n=======================================================")
    print(f"  UPTM ESPORTS PLATFORM (FLASK + BOOTSTRAP 5) RUNNING  ")
    print(f"  Access local server at: http://127.0.0.1:{port}      ")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=debug)
