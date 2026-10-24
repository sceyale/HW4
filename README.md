# Hw4: Campus Customs Shop

A shopping site for **Campus Customs**, a family-run Yale apparel shop founded in New Haven in 1975.

- **Frontend:** React + Vite + TypeScript.
- **Backend:** Python FastAPI with a **PydanticAI shop assistant**.

Shoppers can:

- browse the products and open a page for each item
- search with suggestions as they type
- create an account and log in
- chat with the assistant about products, sizes, stock and prices, and see the matching items appear on the page

The assistant remembers logged-in shoppers between visits. Every agent run is recorded in an append-only audit trail.

## What's in this folder

```
Hw4/
├── backend/                  FastAPI app + PydanticAI agent
│   ├── main.py               API app (run with Uvicorn): products, search, accounts, chat
│   ├── prompts/prompt.md   ┐
│   ├── agent.py            │ The agent (4 files):
│   ├── tools.py            │   system prompt · entry point/wiring · tools · structured types
│   ├── models.py           ┘
│   ├── db.py                 SQLite access (catalogue read-only, chat history)
│   ├── auth.py               Accounts, PBKDF2 password hashing, sessions, lockout
│   ├── audit.py              Append-only audit trail with redaction
│   ├── test_*.py             Offline tests (no API key needed)
│   ├── verify_shop.py        Live end-to-end check
│   └── requirements.txt
├── frontend/                 React + Vite + TypeScript
│   ├── src/                  pages, components, AuthContext, ChatContext, api.ts, types.ts
│   └── public/campus/        drop-in folder for campus/student photos (see its README)
├── data/                     ← place the data pack here (git-ignored)
├── scripts/                  capture_app_check.py (automated screenshots)
├── output/                   harness.md · usability.md · design.md · app_check.html
├── AI_prompts.md             every prompt used to build the project
└── .env.example              placeholder settings; copy to .env
```

### The agent: 4 files in `backend/`

| File | Role |
|---|---|
| `prompts/prompt.md` | System prompt: Campus Customs voice, tool guide, stock rules, search display, customer memory, usability adjustments, password safety, safety basics |
| `agent.py` | Entry point and wiring: loads `.env`, builds the OpenAI model and the PydanticAI `Agent`, adds the "who is chatting / what's on screen" context, runs each turn (max 6 model requests), checks the output and writes the audit trail |
| `tools.py` | 8 tools the agent can call: `search_products`, `get_product_details`, `check_stock`, `price_summary`, `list_categories`, `get_shopper_profile`, `recall_chat_history`, `log_usability_feedback` |
| `models.py` | Pydantic types: API requests and responses, `ShopDeps`, tool results (`StockCheck`, `SearchResult`…), and the agent output `ShopReply` |

The full reference (architecture, every model field and why it was chosen, safety rules, limits) is in [`output/harness.md`](output/harness.md).

## Quick start

### 1. Place the data pack

The database and product photos are **not in the repo**: the database holds user accounts, and the photos are not ours to publish. Put them in `data/` like this:

```
data/
├── campus_customs.db
└── products/
    ├── 2025-yale-vs-harvard-t-shirt.jpg
    ├── basic-hoodie-big-yale.jpg
    └── … (102 photos, named <product_id>.jpg)
```

### 2. Add your API key

```bash
cp .env.example .env
# open .env and set OPENAI_API_KEY=<your key>
```

`.env` is git-ignored. Never commit real keys.

### 3. Run the backend (terminal 1)

Requires Python 3.11 or newer. Start it **from inside `backend/`**:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Check it works: http://localhost:8000/api/health should return `{"status":"ok"}`. The interactive API docs are at http://localhost:8000/docs.

### 4. Run the frontend (terminal 2)

Requires Node 20 or newer.

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Vite forwards `/api` and `/media` to the backend on port 8000.

### 5. Try it

- **Log in** with the seeded test account from the course data pack, or **create an account**.
- **Search:** type "hoo" or "bulldog" in the top search bar.
- **Chat (bottom right):**
  - "What hoodies do you have?" The Products page fills with hoodie cards.
  - On an item page: "Do you have this in medium?" The assistant gives the real stock and clearly says if that size is sold out.
  - "What's your cheapest fleece?"

## Run it in the cloud (GitHub Codespaces), with nothing to install locally

1. On the repo page, choose **Settings → Secrets and variables → Codespaces → New repository secret** and add `OPENAI_API_KEY`.
2. Choose **Code → Codespaces → Create codespace on main**. Python, Node and all packages install automatically (a few minutes).
3. Drag the data pack (`campus_customs.db` and `products/`) into the `data/` folder in the Codespace file explorer, then run `bash .devcontainer/start.sh` in the terminal.
4. Open the **Ports** tab and click the globe next to **5173**. That's the live site.
5. Optional checks in the Codespace terminal:
   ```bash
   cd backend && python verify_shop.py && cd ..
   python -m playwright install --with-deps chromium && python scripts/capture_app_check.py
   ```
   The screenshots land in `output/app_check_images/`. Right-click → **Download**, or commit them.

## Tests

From `backend/`:

```bash
python test_auth.py      # 10 checks: password hashing spec, login, lockout, sessions
python test_tools.py     # 25 checks: database-grounded tools, stock, prices, search, suggestions
python test_memory.py    # 18 checks: chat history, customer fields, privacy, page context
python test_audit.py     # 11 checks: append-only audit file, redaction, loop events

# With both servers running (chat checks use the API key):
python verify_shop.py              # full end-to-end check
python verify_shop.py --no-chat    # skip the paid chatbot checks
```

## Screenshots for `output/app_check.html`

With both servers running, one command captures all three checks in your installed Chrome. No browser extension is needed.

```bash
pip install playwright                 # once
python scripts/capture_app_check.py    # add --show to watch it
```

It saves `inventory.png`, `search_cards.png` and `usability_search.png` to `output/app_check_images/`, then opens `app_check.html`. If Google Chrome isn't installed, run `python -m playwright install chromium` first.

## Key specs

| | |
|---|---|
| Model | `gpt-5.6-luna` via OpenAI (`CHAT_MODEL`), reasoning `low` |
| Agent loop limit | 6 model requests per turn, 2 output retries |
| Result caps | 12 summaries to the model, 30 cards for a search on the page, 8 picked cards |
| Passwords | PBKDF2-HMAC-SHA256, 120,000 rounds, random salt, constant-time compare; 5 failed logins → 15-minute lockout |
| Sessions | HttpOnly SameSite cookie, only the SHA-256 of the token stored, 7 days |
| Audit trail | `output/audit_trail.json`, append-only, never wiped, secrets redacted (git-ignored) |

## Documentation

- [`output/harness.md`](output/harness.md): how the whole system works
- [`output/usability.md`](output/usability.md): usability improvements, before and after
- [`output/design.md`](output/design.md): the refined design and why it helps shoppers stay and buy
- [`output/app_check.html`](output/app_check.html): screenshot checks (open by double-clicking)
- [`AI_prompts.md`](AI_prompts.md): the prompts used to build the project

## Notes

- **Photos:** campus and student photos are slots. Add licensed `.jpg` files to `frontend/public/campus/` using the names in its `README.md`. Until then, the site shows original illustrated Gothic scenes.
- **Not affiliated with Yale:** Campus Customs is an independent retailer, and the crest is an original design, not the Yale shield.
