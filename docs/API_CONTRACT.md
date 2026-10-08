# Agrova API contract

What the **frontend** sends and expects back. Any backend (Glory's, Mhimhi's, Philip's, or a merged one) only
has to match this. The frontend reads the server address from `NEXT_PUBLIC_API_URL`
(see `frontend/.env.local.example`). When it is not set, the app runs on built-in demo data and says so.

Rules for every endpoint:

- JSON in, JSON out (`Content-Type: application/json`), except the health endpoint, which is `multipart/form-data`.
- Errors: a non-2xx status and `{ "detail": "short human-readable message" }`. The message is shown to the farmer, so
  keep it plain.
- CORS must allow the frontend's origin.
- The AI key lives **only** on the server (`.env`). Never send it to the browser.
- Never invent farm data. If the records don't contain the answer, say so.

---

## 1. Chat: `POST /chat/`

Talk to Agro AI. The server remembers the conversation by `session_id`.

Request:

```json
{ "message": "I don buy 200 broiler yesterday for 300k", "session_id": "b3f1c2e0-..." }
```

Response:

```json
{
  "reply": "I understood: you bought 200 broilers yesterday for ₦300,000. Should I save this?",
  "session_id": "b3f1c2e0-...",
  "proposal": { "summary": "Purchase · 200 broilers · ₦300,000" }
}
```

- `reply` (string, required): what Agro AI says. Plain text, no markdown, short (phone screen).
- `session_id` (string, required): echo back, or issue one if the request had none.
- `proposal` (object, optional): present only when Agro AI wants a **yes/no before saving** something.
  `summary` is one line the farmer can read at a glance. The frontend shows Yes / No buttons.
- **Confirming:** the frontend sends `"Yes"` or `"No"` as a normal chat `message` in the same session. The server
  saves (or drops) the pending record and replies. (This matches how Glory's `chatbot/record_logging.py` already works.)
- Extra response fields (e.g. `history`) are fine; the frontend ignores them.

Language: if the farmer writes Pidgin, reply in Pidgin.

## 2. Health assessment: `POST /health/assess`

`multipart/form-data` fields:

| field | type | notes |
|---|---|---|
| `species` | string | `poultry` `goats` `sheep` `cattle` `pigs` `rabbits` `fish` |
| `symptoms` | string | farmer's own words |
| `affected` | integer | how many are sick |
| `total` | integer, optional | group size |
| `deaths` | integer | 0 if none |
| `onset` | string | `today` `few-days` `week-plus` |
| `drinking` | string | `normal` `less` |
| `vaccinated` | string | `yes` `no` `unsure` |
| `photo` | file, optional | JPG / PNG / WebP, up to 5 MB |

Response:

```json
{
  "risk": "HIGH",
  "observed": ["12 of 500 poultry affected", "Started: today"],
  "possible_concerns": ["Respiratory illness", "Environmental stress"],
  "next_steps": ["Separate the sick birds.", "Provide clean water."],
  "call_vet": "Call a veterinarian today.",
  "photo_note": null
}
```

- `risk`: `LOW` | `MEDIUM` | `HIGH`.
- `possible_concerns`: say "possible", never a definite diagnosis.
- No drug doses or home recipes unless they come from the knowledge base.
- Always end up recommending a vet for HIGH risk.

## 3. Dashboard: `GET /dashboard`  *(not wired yet)*

```json
{
  "farm": { "name": "Dons Farm", "location": "Ogun State, Nigeria" },
  "totals": { "livestock": 545, "revenue": 1240000, "expenses": 780000, "profit": 460000 },
  "expense_breakdown": [{ "category": "Feed", "amount": 420000 }],
  "livestock": [{ "id": "b001", "type": "Poultry", "name": "Broiler Batch 001", "qty": 500, "status": "Watch", "note": "..." }],
  "alerts": [{ "id": "a1", "severity": "WARNING", "title": "...", "detail": "..." }],
  "activity": ["Feed purchased · ₦80,000"]
}
```

`severity`: `INFO` | `LOW` | `WARNING` | `CRITICAL`. All money is whole Naira. Numbers must come from stored
records, not from the model.

## 4. Farm setup: `POST /farms`  *(not wired yet)*

Body is the onboarding form (`frontend/src/lib/farm-setup.ts` → `FarmSetup`). Returns the created farm with an `id`.
