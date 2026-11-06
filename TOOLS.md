# MCP tools (generated)

38 tools by default. Generated from the endpoint registry by `sdks/mcp/generate.py`.
Narrow the list with `SOCIALSCRAPE_PLATFORMS` / `SOCIALSCRAPE_TOOLSETS`; see README.md.

## `get_transcript` (core)

Get the transcript of a video or audio post from its URL. The platform is detected from the link. Uses the platform's captions when they exist and falls back to AI transcription of the audio. Price: 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Returns text, language, source (captions | auto_captions | ai) and duration. Long transcripts come back in pieces: when `text_window.next_offset` is set, call again with that offset.

## `search` (core)

Search one platform for posts, videos, users or other items by keyword. Platforms: YouTube, TikTok, Instagram, Apple Music, Cosmos, Facebook, LinkedIn, Pinterest, Reddit, Rumble, Spotify, Threads, X (Twitter). Price: 1 credit per call (failures free, cached repeats free with max_age_days). For anything beyond this, use the platform's own tool. Kinds per platform: youtube: channel.search, search, search.typeahead; tiktok: search.keyword, search.suggestions, search.top, search.users; instagram: search.popular, search.reels; facebook: events.search, search.videos; reddit: search, subreddit.search; threads: search, search.users.

## `get_profile` (core)

Get a profile (name, bio, follower counts, links) by handle or URL. Platforms: YouTube, TikTok, Instagram, Apple Music, Bluesky, Cosmos, Facebook, GitHub, Kwai, LinkedIn, Snapchat, SoundCloud, Spotify, Threads, Truth Social, Twitch, X (Twitter). Price: 1 credit per call (failures free, cached repeats free with max_age_days). For anything beyond this, use the platform's own tool.

## `get_post` (core)

Get one post, video, tweet, pin or clip by URL: text, author, stats, media. Platforms: YouTube, TikTok, Instagram, Bluesky, Cosmos, Facebook, Kick, Kwai, LinkedIn, Pinterest, Reddit, Rumble, Snapchat, Telegram, Threads, Truth Social, Twitch, X (Twitter). Price: 1 credit per call (failures free, cached repeats free with max_age_days). For anything beyond this, use the platform's own tool.

## `get_comments` (core)

Get a page of comments on a post or video. Platforms: YouTube, TikTok, Instagram, Facebook, Reddit, Rumble, Snapchat. Price: 1 credit per call (failures free, cached repeats free with max_age_days). For anything beyond this, use the platform's own tool.

## `describe` (core)

Look up what SocialScrape can fetch, with exact parameters, allowed values, price and example arguments. Free and instant (no API call, no credits). With no arguments it lists every platform; with `platform` its resources; with `platform` and `resource` (or `endpoint`) the full parameter list.

## `call_endpoint` (core)

Run any SocialScrape data endpoint by its id (for example `youtube.channel`). Same behaviour and price as the platform tools; use it when you already know the id, or when only the core tools are enabled. 183 endpoints; call describe to list them.

## `get_credits` (core)

Show how many credits the API key's team has left. Free.

## `get_job` (core)

Fetch the result of a request that answered 'accepted' (long jobs such as AI transcription of a long video). Polling is free; the credit charge happens once, when the job finishes. If it is still running, wait a few seconds and call again.

## `batch` (core)

Run up to 100 data requests in one call (for example the profile of 30 accounts). Each item is charged like a single request and failures inside the batch are free; one failing item does not fail the others. The answer has one result per item, in order.

## `monitors` (core)

Watch a list (a profile's posts, a search) and have SocialScrape POST new items to your webhook, signed. Actions: create, list, delete, test (send a signed test event), deliveries (delivery log), events, redeliver. Each scheduled check is charged like a normal request to the watched endpoint; creating, listing and deleting are free. The first check only records a baseline. The create answer shows the webhook secret once: tell the user to store it.

## `youtube` (platforms)

Data from YouTube: profiles, posts and videos, collections, transcripts, advertisers, comments.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- channel(handle|id|url): YouTube channel details. 1 credit.
- channel.community_posts(handle|id|url): YouTube channel community posts. 1 credit. Paged.
- channel.lives(handle|id|url): YouTube channel live streams. 1 credit. Paged.
- channel.playlists(handle|id|url): YouTube channel playlists. 1 credit. Paged.
- channel.search(query, handle|id|url): Search inside a YouTube channel. 1 credit. Paged.
- channel.shorts(handle|id|url): YouTube channel Shorts. 1 credit. Paged. Optional: include_extras.
- channel.videos(handle|id|url): YouTube channel videos. 1 credit. Paged. Optional: include_extras.
- community_post(url): YouTube community post. 1 credit.
- playlist(url|id): YouTube playlist videos. 1 credit. Paged.
- search(query): YouTube search. 1 credit. Paged. Optional: type, upload_date, duration, include_extras.
- search.hashtag(hashtag): YouTube videos by hashtag. 1 credit. Paged. Optional: type.
- search.typeahead(query): YouTube search suggestions. 1 credit. Paged.
- shorts.trending(): Trending YouTube Shorts. 1 credit. Paged.
- video(url|id): YouTube video or Short details. 1 credit.
- video.comment.replies(): YouTube comment replies. 1 credit. Paged. Optional: comment_id.
- video.comments(url|id): YouTube video comments. 1 credit. Paged.
- video.sponsors(url|id): YouTube video sponsors. 1 credit. Paged.
- video.transcript(url|id): YouTube video transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: original_audio.

## `tiktok` (platforms)

Data from TikTok: profiles, posts and videos, transcripts, comments, tracks, live streams.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- collection.videos(url): TikTok collection videos. 1 credit. Paged.
- live(url|id): TikTok live room info. 1 credit. Optional: user_id.
- profile(handle|id): TikTok profile. 1 credit.
- profile.live(handle): Is a TikTok user live. 1 credit.
- profile.videos(handle|id): TikTok profile videos. 1 credit. Paged. Optional: include_pinned.
- search.hashtag(hashtag): TikTok videos by hashtag. 1 credit. Paged.
- search.keyword(query): TikTok video search. 1 credit. Paged. Optional: date_posted.
- search.suggestions(query): TikTok search suggestions. 1 credit. Paged.
- search.top(query): TikTok top search. 1 credit. Paged. Optional: publish_time.
- search.users(query): TikTok user search. 1 credit. Paged.
- song(id|url): TikTok song details. 1 credit.
- song.videos(id|url): TikTok videos using a song. 1 credit. Paged.
- trending(): TikTok trending feed. 1 credit. Paged.
- video(url|id): TikTok video details. 1 credit. Optional: get_transcript.
- video.comment.replies(comment_id, url|id): TikTok comment replies. 1 credit. Paged.
- video.comments(url|id): TikTok video comments. 1 credit. Paged.
- video.transcript(url|id): TikTok video transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: ai_fallback, allow_long_transcription.
- videos.popular(): Popular TikTok videos. 1 credit. Paged. Optional: period, category.

## `instagram` (platforms)

Data from Instagram: profiles, posts and videos, transcripts, comments, collections.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- basic_profile(id): Instagram profile by user id. 1 credit.
- highlight(id): Instagram highlight stories. 1 credit. Paged.
- post(url|id): Instagram post or reel details. 1 credit. Optional: include_play_count.
- post.comments(url|id): Instagram post comments. 1 credit. Paged. Optional: include_replies.
- post.transcript(url|id): Instagram reel transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: allow_long_transcription.
- profile(handle): Instagram profile. 1 credit.
- profile.embed(handle): Instagram profile embed HTML. 1 credit.
- profile.highlights(handle|id): Instagram story highlights. 1 credit. Paged.
- profile.post_count(handle): Instagram profile post count. 1 credit. Optional: allow_estimated.
- profile.posts(handle|id): Instagram profile posts. 1 credit. Paged. Optional: require_play_counts.
- profile.reels(handle|id): Instagram profile reels. 1 credit. Paged. Optional: require_play_counts.
- reels.trending(): Instagram trending reels. 1 credit. Paged.
- search.hashtag(hashtag): Instagram posts by hashtag. 1 credit. Paged. Optional: date_posted, media_type, enrich.
- search.popular(query): Instagram popular topic. 1 credit. Paged.
- search.reels(query): Instagram reel search. 1 credit. Paged. Optional: date_posted.
- song.reels(id): Instagram reels using a song. 1 credit. Paged.

## `ad_libraries` (platforms)

Ad libraries (Facebook/Meta, Google, LinkedIn, TikTok): search ads and advertisers, read one ad. The resource starts with the library: facebook.search, google.company.ads.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- facebook.ad(id|url): Facebook Ad Library ad details. 1 credit. Optional: get_transcript.
- facebook.ad.transcript(id|url): Facebook Ad Library ad transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: allow_long_transcription.
- facebook.company.ads(id|company_name): Facebook Ad Library ads by page. 1 credit. Paged. Optional: status, media_type, start_date, end_date.
- facebook.search(query): Facebook Ad Library search. 1 credit. Paged. Optional: match, ad_type, status, media_type, start_date, end_date.
- facebook.search.companies(query): Facebook Ad Library advertiser search. 1 credit. Paged.
- google.ad(url): Google Ads Transparency ad details. 1 credit.
- google.advertisers.search(query): Google Ads Transparency advertiser search. 1 credit. Paged.
- google.company.ads(id|domain): Google Ads Transparency ads by advertiser. 1 credit. Paged. Optional: topic, platform, format, start_date, end_date.
- linkedin.ad(url|id): LinkedIn Ad Library ad details. 1 credit.
- linkedin.search(): LinkedIn Ad Library search. 1 credit. Paged. Optional: company, company_id, countries, start_date, end_date.
- tiktok.ad(id|url): TikTok Ad Library ad details. 1 credit.
- tiktok.search(query|advertiser_name): TikTok Ad Library search. 1 credit. Paged. Optional: adv_biz_ids, start_date, end_date.

## `amazon` (platforms)

Data from Amazon: products.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- shop(url): Amazon storefront products. 1 credit. Paged.

## `apple_music` (platforms)

Data from Apple Music: profiles, albums, tracks.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- album(url|id): Apple Music album. 1 credit.
- artist(url|id): Apple Music artist. 1 credit.
- search(query): Apple Music search. 1 credit. Paged. Optional: type.
- track(url|id): Apple Music track. 1 credit.

## `bluesky` (platforms)

Data from Bluesky: profiles, posts and videos.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- post(url): Bluesky post. 1 credit.
- profile(handle): Bluesky profile. 1 credit.
- profile.posts(handle): Bluesky profile posts. 1 credit. Paged.

## `cosmos` (platforms)

Data from Cosmos: profiles, posts and videos, collections.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- collection(url): Cosmos collection. 1 credit.
- collection.posts(url): Cosmos collection posts. 1 credit. Paged.
- post(url): Cosmos post. 1 credit.
- profile(handle): Cosmos profile. 1 credit.
- profile.collections(handle): Cosmos profile collections. 1 credit. Paged.
- profile.posts(handle): Cosmos profile posts. 1 credit. Paged.
- search(query): Cosmos search. 1 credit. Paged.

## `creators` (platforms)

Find a creator's other social profiles and the contact emails they publish.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- emails(url|handle): Find a creator's public emails. 1 credit. Optional: platform.
- social_profiles(url|handle): Find a creator's other social profiles. 1 credit. Paged. Optional: platform.

## `facebook` (platforms)

Data from Facebook: profiles, posts and videos, events, transcripts, comments, communities and groups, locations, products.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- event(url|id): Facebook event details. 1 credit.
- events(url): Facebook city events. 1 credit. Paged. Optional: time.
- events.search(query): Facebook Events search. 1 credit. Paged. Optional: location.
- group(url|id): Facebook public group. 1 credit.
- group.posts(url|id): Facebook public group posts. 1 credit. Paged.
- marketplace.item(url|id): Facebook Marketplace listing. 1 credit.
- marketplace.location.search(query): Facebook Marketplace location search. 1 credit. Paged.
- marketplace.search(lat|location): Facebook Marketplace search. 1 credit. Paged. Optional: lng, category_id, radius_km, min_price, max_price, delivery_method, condition, ....
- post(url): Facebook post details. 1 credit. Optional: get_transcript.
- post.comment.replies(feedback_id|url): Facebook comment replies. 1 credit. Paged. Optional: comment_id, expansion_token.
- post.comments(feedback_id|url): Facebook post comments. 1 credit. Paged.
- post.transcript(url): Facebook video transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: allow_long_transcription.
- profile(url): Facebook profile or page. 1 credit. Optional: get_business_hours, include_gated_profile.
- profile.events(url): Facebook page events. 1 credit. Paged.
- profile.photos(url): Facebook profile photos. 1 credit. Paged.
- profile.posts(url|id): Facebook profile posts. 1 credit. Paged.
- profile.reels(url): Facebook profile reels. 1 credit. Paged.
- search.videos(query): Facebook video search. 1 credit. Paged.

## `github` (platforms)

Data from GitHub: profiles, repositories, contribution history, activity, pull requests.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- repository(url|repo): GitHub repository. 1 credit.
- trending.developers(): GitHub trending developers. 1 credit. Paged. Optional: since.
- trending.repositories(): GitHub trending repositories. 1 credit. Paged. Optional: since, spoken_language_code.
- user(handle|url): GitHub user. 1 credit.
- user.activity(handle|url): GitHub public activity. 1 credit. Paged. Optional: year.
- user.contributions(handle|url): GitHub contribution calendar. 1 credit. Optional: year.
- user.followers(handle|url): GitHub followers. 1 credit. Paged.
- user.following(handle|url): GitHub following. 1 credit. Paged.
- user.pull_requests(handle|url): GitHub pull requests by a user. 1 credit. Paged. Optional: state, since, until.
- user.repositories(handle|url): GitHub user repositories. 1 credit. Paged. Optional: type, direction.

## `kick` (platforms)

Data from Kick: transcripts, posts and videos.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- clip(url): Kick clip. 1 credit.
- clip.transcript(url): Kick clip transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: allow_long_transcription, ai_fallback.

## `kwai` (platforms)

Data from Kwai: profiles, posts and videos.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- post(url): Kwai post. 1 credit.
- profile(url|handle): Kwai profile. 1 credit.
- profile.posts(url|handle): Kwai profile posts. 1 credit. Paged.

## `link_in_bio` (platforms)

Read a creator's link-in-bio page (Linktree, Komi, Pillar, Linkbio, Linkme): the links, socials and contact buttons it lists.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- komi(url|handle): Komi page. 1 credit.
- linkbio(url|handle): Lnk.Bio page. 1 credit.
- linkme(url|handle): Linkme page. 1 credit.
- linktree(url|handle): Linktree page. 1 credit.
- pillar(url|handle): Pillar page. 1 credit.

## `linkedin` (platforms)

Data from LinkedIn: profiles, posts and videos, transcripts.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- company(url): LinkedIn company page. 1 credit.
- company.posts(url): LinkedIn company posts. 1 credit. Paged.
- post(url): LinkedIn public post. 1 credit.
- post.transcript(url): LinkedIn post video transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: allow_long_transcription.
- profile(url): LinkedIn public person profile. 1 credit.
- search.posts(query): LinkedIn post search. 1 credit. Paged. Optional: date_posted, enrich.

## `pinterest` (platforms)

Data from Pinterest: posts and videos, collections.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- board(url): Pinterest board pins. 1 credit. Paged.
- pin(url): Pinterest pin. 1 credit.
- profile.boards(handle): Pinterest user boards. 1 credit. Paged.
- search(query): Pinterest pin search. 1 credit. Paged.
- topic(url): Pinterest topic pins. 1 credit. Paged.

## `reddit` (platforms)

Data from Reddit: communities and groups, posts and videos, comments, transcripts.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- post(url): Reddit post. 1 credit.
- post.comments(url): Reddit post comments. 1 credit. Paged.
- post.transcript(url): Reddit video post transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: allow_long_transcription.
- search(query): Reddit search. 1 credit. Paged. Optional: timeframe.
- subreddit.details(subreddit|url): Subreddit details. 1 credit.
- subreddit.posts(subreddit): Subreddit posts. 1 credit. Paged. Optional: timeframe.
- subreddit.search(subreddit, query): Search within a subreddit. 1 credit. Paged. Optional: timeframe.

## `rumble` (platforms)

Data from Rumble: posts and videos, comments, transcripts.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- channel.videos(handle|url): Rumble channel videos. 1 credit. Paged.
- search(query): Rumble search. 1 credit. Paged.
- video(url): Rumble video details. 1 credit.
- video.comments(url): Rumble video comments. 1 credit. Paged.
- video.transcript(url): Rumble video transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: allow_long_transcription.

## `snapchat` (platforms)

Data from Snapchat: profiles, posts and videos, comments.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- profile(handle): Snapchat public profile. 1 credit.
- spotlight(url): Snapchat Spotlight video. 1 credit.
- spotlight.comments(url): Snapchat Spotlight comments. 1 credit. Paged.

## `soundcloud` (platforms)

Data from SoundCloud: profiles, tracks.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- artist(url|handle): SoundCloud artist. 1 credit.
- artist.tracks(url|handle): SoundCloud artist tracks. 1 credit. Paged.
- track(url): SoundCloud track. 1 credit.

## `spotify` (platforms)

Data from Spotify: profiles, albums, tracks, collections, posts and videos.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- album(url|id): Spotify album. 1 credit.
- artist(url|id): Spotify artist. 1 credit.
- playlist(url|id): Spotify playlist. 1 credit. Paged.
- podcast(url|id): Spotify podcast. 1 credit.
- podcast.episodes(url|id): Spotify podcast episodes. 1 credit. Paged.
- search(query): Spotify search. 1 credit. Paged. Optional: type.
- track(url|id): Spotify track. 1 credit.

## `telegram` (platforms)

Data from Telegram: communities and groups, posts and videos.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- channel(handle|url): Telegram public channel. 1 credit.
- channel.posts(handle|url): Telegram public channel posts. 1 credit. Paged.
- post(url): Telegram public post. 1 credit.

## `threads` (platforms)

Data from Threads: profiles, posts and videos.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- post(url): Threads post. 1 credit.
- profile(handle): Threads profile. 1 credit.
- profile.posts(handle): Threads profile posts. 1 credit. Paged.
- search(query): Threads post search. 1 credit. Paged. Optional: start_date, end_date.
- search.users(query): Threads user search. 1 credit. Paged.

## `tiktok_shop` (platforms)

TikTok Shop products, shop listings and product reviews.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- product(url|id): TikTok Shop product details. 1 credit.
- product.reviews(url|id): TikTok Shop product reviews. 1 credit. Paged.
- products(url): TikTok Shop products of a shop. 1 credit. Paged.
- search(query): TikTok Shop product search. 1 credit. Paged.

## `truthsocial` (platforms)

Data from Truth Social: profiles, posts and videos.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- post(url): Truth Social post. 1 credit.
- profile(handle): Truth Social profile. 1 credit.
- profile.posts(handle|id): Truth Social profile posts. 1 credit. Paged.

## `twitch` (platforms)

Data from Twitch: profiles, posts and videos, events, transcripts.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- clip(url): Twitch clip. 1 credit.
- clip.transcript(url): Twitch clip transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: allow_long_transcription, ai_fallback.
- profile(handle): Twitch channel. 1 credit.
- user.schedule(handle): Twitch stream schedule. 1 credit. Paged.
- user.videos(handle): Twitch user videos. 1 credit. Paged. Optional: type.

## `twitter` (platforms)

Data from X (Twitter): posts and videos, profiles, transcripts, communities and groups.

Pick a `resource`, then pass its parameters as top-level arguments (extras in `params`). Each call costs the credits shown below and the result says what was charged and what is left; failures are free. List resources return a `cursor`: pass it back unchanged for the next page. Pass max_age_days to accept a cached copy for free.

Resources:
- community(url|id): X community. 1 credit.
- community.tweets(url|id): X community posts. 1 credit. Paged.
- profile(handle): X profile. 1 credit.
- profile.tweets(handle): X profile posts. 1 credit. Paged.
- search.posts(query): X post search. 1 credit. Paged.
- tweet(url|id): X post details. 1 credit.
- tweet.transcript(url|id): X video transcript. 1 credit (captions); AI transcription 1 credit up to 2 minutes, then 5 per started minute of the whole video. Optional: allow_long_transcription.
