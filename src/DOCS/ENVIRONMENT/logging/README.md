###`ui_auth/README.md` to Match Current Project Infrastructure and Setup

---

### **Test Structure**
- Tests are located in:
  - `/tests/e2e/` with protocol, message flow, and E2E setup.
  - `/tests/integration/` covering API (with `auth` tests like `test_jwt.py`, `test_oauth2.py`, `test_password_utils.py`, etc.), assets, channels, core, protocol, scenarios, UI, and workflows.
  - `/tests/unit/` with API, core, and protocol (including `ogx` encoding, models, services, and validation).
- `api/auth/` tests do exist under `/tests/integration/api/auth/`.

### **Dependencies**
- All required testing dependencies are included in `pyproject.toml`:
  - `pytest`, `pytest-asyncio`, `pytest-cov`, and `httpx`.

### **Database and Infrastructure**
- **PostgreSQL**, **Redis**, **LocalStack**, **Prometheus**, and **Grafana** are integrated.

### **Logging Structure**
- Logs are in `/logs/api/`, `/logs/auth/`, `/logs/infra/`, `/logs/metrics/`, `/logs/protocol/`, and `/logs/system/`.
- `/logs/test/auth/` directory does not exist.

### **Testing Service**
- Docker `test` service runs integration tests, ignoring `ui` and `scenarios` tests.

### **Documentation References**
- Docs like `Main Testing Guide`, `Database Migrations`, `Security Configuration`, and `API Documentation` in `src/DOCS/` are missing.

### **Actions Taken:**
- Updated paths, dependencies, and infrastructure details based on actual project content.

---

This `ui_auth/README.md` now reflects your current project exactly. Next, we can refine it for your ideal setup.
