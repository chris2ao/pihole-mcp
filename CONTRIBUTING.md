# Contributing to pihole-mcp

Thanks for the interest. This project welcomes bug reports, tool additions, and documentation improvements.

## Scope

This server wraps the Pi-hole v6 REST API as MCP tools. In scope:

- Adding tools that map to v6 REST endpoints
- Improving error handling, session auth, or test coverage
- Filling the gap list in `README.md` (adlist CRUD, groups, DHCP, Teleporter, regex filters, per-client policy)
- Documentation and examples

Out of scope:

- Pi-hole v5 API support (v5 is deprecated)
- Non-MCP transports (HTTP, SSE are not planned here)

## Development setup

```bash
git clone https://github.com/chris2ao/pihole-mcp.git
cd pihole-mcp
uv sync --extra dev
uv run pytest -q
```

Tests must pass before a PR is considered. `uv run pytest --cov --cov-report=term` gives coverage; the target is 80%+.

## Running against a real Pi-hole

Set `PIHOLE_URL` and `PIHOLE_PASSWORD` env vars. The password is an **app password** (Pi-hole Web UI → Settings → Web Interface → Application password), not the admin login.

```bash
export PIHOLE_URL=http://pihole.lan
export PIHOLE_PASSWORD=<app-password>
uv run python -m pihole_mcp
```

## Adding a tool

1. Pick the right module under `src/pihole_mcp/tools/` (or create one if the capability is new).
2. Define the tool function inside the module's `register(mcp, client)` function, decorated with `@mcp.tool()`.
3. Return the count increment from `register`.
4. Add the tool to `docs/plans/consolidated-tool-map.md`.
5. Add at least one test in `tests/test_tools.py` using `respx` to mock the Pi-hole API.
6. Update `README.md` tool list if it's user-facing.

## Pull request process

1. Branch from `main`.
2. Keep PRs focused. One feature or fix per PR.
3. Update tests and docs alongside the code change.
4. CI must pass before review.
5. Squash-and-merge is the default merge strategy.

## Commit messages

Conventional Commits format: `<type>: <description>` where type is one of `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.

## Reporting issues

Use the issue templates in `.github/ISSUE_TEMPLATE/`:

- **Bug report** for broken behavior
- **Feature request** for new capability
- **Missing tool** for a specific Pi-hole API endpoint that isn't wrapped yet

## Code of conduct

This project follows the [Contributor Covenant](./CODE_OF_CONDUCT.md). Be respectful.
