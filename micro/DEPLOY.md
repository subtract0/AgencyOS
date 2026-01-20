# Deploy Micro in 3 Steps

## Step 1: OpenAI API Key

The app automatically loads `OPENAI_API_KEY` from `/Users/am/Code/AgencyOS/.env`

If not set, add it:
```bash
# Edit the .env file
nano /Users/am/Code/AgencyOS/.env

# Add/update this line:
OPENAI_API_KEY=sk-your-actual-key-here
```

Get a key at https://platform.openai.com/api-keys if needed.

## Step 2: Deploy to Vercel

**Option A: One-Click Deploy**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/micro&env=OPENAI_API_KEY)

**Option B: Command Line**

```bash
# Install Vercel CLI (if needed)
npm install -g vercel

# Go to micro folder
cd micro

# Deploy
vercel

# When asked about environment variables:
# Name: OPENAI_API_KEY
# Value: sk-your-key-here
```

**Option C: Vercel Dashboard**

1. Push this folder to GitHub
2. Go to https://vercel.com/new
3. Import your repository
4. Add environment variable:
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI key
5. Click Deploy

## Step 3: Done!

Your app is now live at `https://your-project.vercel.app`

### Add Custom Domain (Optional)

1. In Vercel dashboard, go to your project
2. Settings → Domains
3. Add your domain (e.g., `micro.yourdomain.com`)

---

## Costs

- **Vercel**: Free tier includes 100GB bandwidth/month
- **OpenAI**: ~$0.0003 per conversation (GPT-4o-mini)
  - 1,000 users/day = ~$9/month

---

## Questions?

The app is self-contained. Everything you need is in this folder.

- To change the AI personality: Edit `lib/prompts.ts`
- To change colors: Edit `tailwind.config.js`
- To add features: The code is simple and documented
