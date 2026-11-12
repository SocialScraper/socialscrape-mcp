# socialscrape-mcp

The SocialScrape MCP server: social media data (profiles, posts, comments, search, ads,
transcripts) for Claude, ChatGPT, Cursor and any other MCP client. SocialScrape hosts this server at `https://api.socialscrape.dev/mcp`; this package is the same server to run on your own machine.

It is **generated from SocialScrape's endpoint registry** and grouped so an agent sees a usable number of tools instead of one per endpoint:

| Tools | What |
|---|---|
| `get_transcript`, `search`, `get_profile`, `get_post`, `get_comments` | The jobs agents do most, across platforms. The platform is an argument. |
| one per platform (`github`, `facebook`, `twitter`, ...) | `resource` picks the data (`user`, `profile.posts`, ...); parameters follow. |
| `describe` | Exact parameters, allowed values, price, example arguments. Free, no API call. |
| `call_endpoint`, `batch`, `get_job`, `monitors`, `get_credits` | Any endpoint by id, up to 100 requests in one call, async jobs, webhooks, balance. |

Only built endpoints appear as tools. A platform shows up in the next release after its endpoints are built.

Every result starts with `ok | credits charged: 1 | credits remaining: 4999` (and the structured
copy carries the numbers as fields). Failures are free and come back as `isError` with the API's
error code, a `retryable` flag and what to do next.

## Use it

**Hosted (the main way).** SocialScrape runs this server at `https://api.socialscrape.dev/mcp` (streamable HTTP). There are two ways to sign in.

1. Sign in, with no key to copy. Add the URL as a connector, then sign in with your SocialScrape account and approve the connection.
   - Claude: Settings, Connectors, Add custom connector, paste the URL.
   - ChatGPT: add a connector with the URL and choose OAuth.
   - Cursor: add a server with the URL and sign in when asked.
   - Claude Code: `claude mcp add --transport http socialscrape https://api.socialscrape.dev/mcp`, then `/mcp` to sign in.
2. An API key in a header, `x-api-key: ss_live_...`.
   - Claude Code: `claude mcp add --transport http socialscrape https://api.socialscrape.dev/mcp --header "x-api-key: ss_live_..."`
   - Cursor, in `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "socialscrape": {
    "url": "https://api.socialscrape.dev/mcp",
    "headers": { "x-api-key": "ss_live_..." } } } }
```

Each signed-in connection shows in the dashboard as a key named "MCP connector". Calls are charged to the team like any key, and revoking that key disconnects that connector. The tools are the same as this package's. Add `?platforms=github,threads` or `?toolsets=core` to the URL to narrow the list.

**Local (this package).** For offline clients, or if you want the server on your own machine, your MCP client starts it as a subprocess over stdio:

```json
{ "mcpServers": { "socialscrape": {
    "command": "uvx", "args": ["socialscrape-mcp"],
    "env": { "SOCIALSCRAPE_API_KEY": "ss_live_..." } } } }
```

Get a key at <https://socialscrape.dev/sign-up?utm_source=github&utm_medium=repo&utm_campaign=socialscrape-mcp>. Tool discovery works without a key; a tool call without one
explains how to add it.

**Fewer tools.** Some clients cap the number of tools (Cursor warns past 40). Narrow the list in the `env`
block:

| | Setting |
|---|---|
| only some platforms | `SOCIALSCRAPE_PLATFORMS=github,threads` |
| only the cross-platform and account tools | `SOCIALSCRAPE_TOOLSETS=core` |
| only the platform tools | `SOCIALSCRAPE_TOOLSETS=platforms` |

With `core` alone an agent still reaches every endpoint through `describe` and `call_endpoint`.

**Serve it over HTTP yourself.** To run your own copy of the hosted server on a host you control, install the extra: `pip install 'socialscrape-mcp[http]'`, then `socialscrape-mcp http --host
127.0.0.1 --port 8080`. Each request carries its own key in the `x-api-key` header (or
`Authorization: Bearer ...`), and `?platforms=` and `?toolsets=` narrow the tools. This copy is yours to run and
secure.

## Settings (environment)

| Variable | Default | |
|---|---|---|
| `SOCIALSCRAPE_API_KEY` | none | stdio only; the HTTP mode reads each request's key |
| `SOCIALSCRAPE_API_URL` | `https://api.socialscrape.dev` | |
| `SOCIALSCRAPE_MCP_TRIM` | `1` | ask for `trim=true` (no null fields, no `extra`) unless a call says otherwise; saves context |
| `SOCIALSCRAPE_MCP_MAX_CHARS` | `100000` | longest answer; longer lists are cut to whole items, transcripts come in windows (`offset`) |
| `SOCIALSCRAPE_MCP_TIMEOUT` | `70` | seconds to wait for the API |
| `SOCIALSCRAPE_MCP_ALLOWED_ORIGINS` | any | HTTP mode only; comma list, set it to refuse browser calls from other origins |
| `SOCIALSCRAPE_PLATFORMS`, `SOCIALSCRAPE_TOOLSETS` | all | see above |

<!-- mcp-name: dev.socialscrape/socialscrape -->
