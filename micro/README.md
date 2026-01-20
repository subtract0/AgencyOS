# Micro

**The app that meets you in bed.** Gentle micro-steps for when everything feels impossible.

## What is this?

Micro is an AI companion for people struggling with depression, ADHD, or just really heavy days. Instead of telling you to "just get up and exercise," it meets you exactly where you are — even if that's frozen in bed.

**How it works:**
1. Open the app
2. Tell Micro how heavy you feel
3. It gives you ONE tiny step (like "wiggle your toes")
4. Do it (or don't — no judgment)
5. Get the next micro-step when you're ready

No streaks. No guilt. Just one tiny step at a time.

---

## Deploy in 5 Minutes

### Option 1: Vercel (Recommended - Free)

1. **Get an OpenAI API key**
   - Go to https://platform.openai.com/api-keys
   - Create a new key
   - Copy it

2. **Deploy to Vercel**
   ```bash
   # If you don't have Vercel CLI
   npm install -g vercel

   # Deploy
   cd micro
   vercel

   # When prompted for environment variables, add:
   # OPENAI_API_KEY = sk-your-key-here
   ```

   Or use the Vercel dashboard:
   - Go to https://vercel.com/new
   - Import this folder
   - Add environment variable: `OPENAI_API_KEY`
   - Deploy

3. **Done!** Your app is live.

### Option 2: Any Node.js Host

```bash
# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Edit .env and add your OpenAI key

# Build
npm run build

# Start
npm start
```

---

## Local Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Open http://localhost:3000
```

### Local Mode (Free - No API Key Needed)

If you have LM Studio running with vcoder-120b on port 1234:

```bash
# The parent .env is already configured for local mode:
# USE_LOCAL_MODEL=true
# LOCAL_API_BASE=http://localhost:1234/v1
# LOCAL_MODEL=vcoder-120b-1.0-hi-mlx

# Just run:
npm run dev
```

### Cloud Mode (OpenAI)

To use OpenAI instead:

```bash
# Edit /Users/am/Code/AgencyOS/.env
# Set: USE_LOCAL_MODEL=false
# Set: OPENAI_API_KEY=sk-your-key-here

npm run dev
```

---

## Project Structure

```
micro/
├── app/
│   ├── api/chat/route.ts   # OpenAI API proxy
│   ├── globals.css          # Tailwind styles
│   ├── layout.tsx           # App layout + PWA config
│   └── page.tsx             # Main page
├── components/
│   ├── MicroChat.tsx        # Main chat component
│   ├── ChatMessage.tsx      # Message bubbles
│   └── TypingIndicator.tsx  # "..." animation
├── lib/
│   ├── prompts.ts           # AI system prompt (the soul of the app)
│   └── storage.ts           # localStorage persistence
├── public/
│   ├── manifest.json        # PWA manifest
│   ├── icon-192.png         # App icon
│   └── icon-512.png         # App icon large
└── README.md
```

---

## Customization

### Change the AI Personality

Edit `lib/prompts.ts` — this is where Micro's personality lives. The `SYSTEM_PROMPT` controls how it responds.

### Change Colors

Edit `tailwind.config.js` — the `night` color palette defines the dark theme.

### Add Features

The app is intentionally minimal. But if you want to add:
- **Push notifications**: Add a service worker in `public/`
- **Backend storage**: Replace localStorage in `lib/storage.ts` with Supabase/Firebase
- **Analytics**: Add Plausible or PostHog in `app/layout.tsx`

---

## Cost Estimate

Using GPT-4o-mini:
- ~$0.15 per 1M input tokens
- ~$0.60 per 1M output tokens

Typical session: ~500 tokens = ~$0.0003

**1,000 daily users × 30 days = ~$9/month**

---

## Install as App (PWA)

### iPhone/iPad
1. Open in Safari
2. Tap Share button
3. Tap "Add to Home Screen"
4. Tap "Add"

### Android
1. Open in Chrome
2. Tap menu (three dots)
3. Tap "Add to Home screen"
4. Tap "Add"

---

## Privacy

- All conversation history stays on the user's device (localStorage)
- Messages are sent to OpenAI for processing (see their privacy policy)
- No analytics, no tracking, no accounts required
- Users can clear all data by clearing browser storage

---

## License

MIT — Do whatever you want with it. Help people.

---

## Support

If this helps someone get out of bed, that's all that matters.

Built with care for the 6,589 people who said they couldn't get out of bed.
