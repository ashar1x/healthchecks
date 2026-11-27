# Access decisions (Playwright)

| Role | Surface | Action | Expected | Observed | Result |
|---|---|---|---|---|---|
| owner (rw) | dashboard | open Add Check | allowed | allowed | PASS |
| read-only member | dashboard | open Add Check | denied | denied | PASS |
| rw API key | API | pause check | 200 | 200 | PASS |
| ro API key | API | pause check | 401 | 401 | PASS |
| read-only member | dashboard | pause check button | denied | denied | PASS |
