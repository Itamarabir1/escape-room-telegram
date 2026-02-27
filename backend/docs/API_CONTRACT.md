# API Contract – Game Web App

Contract between backend `app/api/games.py` (and services) and frontend `frontend/src/api/client.ts`. API layer is thin: auth via `game_auth_service`, then delegates to `game_*_service` for business logic.

---

## Base URL

- REST: `{VITE_API_URL}/api/games`
- WebSocket: `{VITE_WS_URL}/ws/games/{game_id}?init_data=...` (same host, `wss` if HTTPS)

---

## REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{game_id}` | Get game state (room, players, puzzles, solved_item_ids, started_at). Applies demo room if missing. |
| POST | `/{game_id}/start` | Record game start (started_at). Called when user clicks "התחל". |
| POST | `/{game_id}/time_up` | Timer reached 0; ends game, broadcasts game_over. |
| POST | `/{game_id}/action` | Submit unlock answer. Body: `GameActionRequest` (`item_id`, `answer`, `solver_name?`). Response: `GameActionResponse`. |
| POST | `/{game_id}/door_opened` | Door clicked (all puzzles solved); broadcasts door_opened. |
| GET | `/{game_id}/lore/audio` | Static lore audio (wav). |

**Request/Response schemas (domain/game.py):** `GameActionRequest` (Pydantic) for POST action body; `GameActionResponse` for action response; `OkResponse` for other POST responses. `GameStateResponse` (TypedDict) for GET state.

**Headers:** When opening via Telegram Web App button, frontend sends `X-Telegram-Init-Data`. Without it, access is allowed (e.g. shared link); with it, user must be in `game["players"]` (or is added as late join).

---

## GET `/{game_id}` – Response shape (GameStateResponse)

```ts
{
  game_id: string
  players: Record<string, string>   // user_id -> name
  game_active: boolean
  room_image_url?: string
  room_image_width?: number
  room_image_height?: number
  room_name?: string
  room_description?: string
  room_lore?: string
  room_items?: Array<{ id, label, x, y, action_type }>
  puzzle?: PuzzleResponse         // deprecated; use puzzles
  puzzles?: PuzzleResponse[]
  solved_item_ids?: string[]     // item_ids with SOLVED status
  started_at?: string            // ISO timestamp when first user clicked התחל
}
```

**PuzzleResponse:** `{ item_id, type: "unlock"|"examine", backstory, encoded_clue?, prompt_text? }`. `correct_answer` is never sent to client.

---

## WebSocket events (client receives)

- `puzzle_solved`: `{ event, item_id, item_label, answer, solver_name? }`
- `game_over`: `{ event: "game_over" }`
- `door_opened`: `{ event: "door_opened" }`

Client connects with `init_data` in query string; only users in `game["players"]` are accepted.
