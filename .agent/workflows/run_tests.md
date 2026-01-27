---
description: How to run tests
---

To run the full test suite:

```bash
make test
```
// turbo
Or manually:
```bash
uv run pytest tests
```

To run tests with coverage:

```bash
make coverage
```

To run all QA checks (lint, typecheck, test):

```bash
make check-all
```
