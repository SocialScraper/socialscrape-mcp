# socialscrape-mcp

The SocialScrape MCP server: social media data (profiles, posts, comments, search, ads,
transcripts) for Claude, Cursor and any other MCP client that starts a local server.

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

The server runs on your own machine. Your MCP client (Claude Desktop, Claude Code, Cursor) starts it as a
subprocess over stdio. SocialScrape does not run a hosted MCP server, so there is no MCP URL to connect to.

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

**Serve it over HTTP yourself.** For a client that can only reach a URL, install the extra and run the
server on a host you control: `pip install 'socialscrape-mcp[http]'`, then `socialscrape-mcp http --host
127.0.0.1 --port 8080`. Each request carries its own key in the `x-api-key` header (or
`Authorization: Bearer ...`), and `?platforms=` and `?toolsets=` narrow the tools. This is yours to run and
secure; SocialScrape does not offer it as a service.

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
