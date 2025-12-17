# NBA API Example

This project demonstrates a minimal `nba_api` usage.

Setup (WSL):

```bash
# Activate the venv
source ~/myproject/venv/bin/activate

# (Optional) Install dependencies
pip install -r requirements.txt

# Run the example
cd ~/myproject
python example.py
```

Without activating the venv (explicit interpreter):

```bash
~/myproject/venv/bin/python ~/myproject/example.py
```

Using VS Code:
- Open the folder `~/myproject`.
- Select interpreter: `~/myproject/venv/bin/python` (Command Palette → "Python: Select Interpreter").
- Run `example.py` from the integrated terminal or the Run view.

Notes:
- `requirements.txt` was generated from the venv (`pip freeze`).
