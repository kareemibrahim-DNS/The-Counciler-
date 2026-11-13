# Local smoke evidence

Date: 2026-11-13 (UTC) / 14 Nov 2026 Asia/Riyadh

## Passed

| Check | Result |
| --- | --- |
| `npm run feed` | 9 partners, 4 line items, 2 prices |
| `npm run check` | pass |
| `agent-sdk validate` | ok |
| `tool call list_partners` country=SA | Ballurh + pipeline partners |
| `tool call get_line_item_price` Ballurh base SA | SAR 900 |
| `tool call get_quote_structure` Ballurh SA | Commercial + Operational from email |
| `tool call get_line_item_price` Ballurh base AE | refused (no cross-country reuse) |
| `agent-sdk dev` | playground http://127.0.0.1:3000/reseller-programs/playground |

## Blocked here (needs your login)

| Check | Result |
| --- | --- |
| `agent-sdk run` model turn | needs `agent-sdk login` / `CURSOR_API_KEY` |
| Off-topic refuse (model) | same — verify in playground after login |

```bash
cd reseller-programs
npx --yes "@grok/agent-sdk@0.6.0" login
npx --yes "@grok/agent-sdk@0.6.0" run --dir . --message "Which partners work in SA?"
npx --yes "@grok/agent-sdk@0.6.0" run --dir . --message "Write me a poem about coffee."
```
