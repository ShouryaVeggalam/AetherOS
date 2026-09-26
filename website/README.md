# AetherOS flagship website

Next.js marketing site for [aetheros-pied.vercel.app](https://aetheros-pied.vercel.app/).

## GitHub links

All public GitHub CTAs resolve through [`lib/site.ts`](lib/site.ts):

| Constant | Value |
|----------|-------|
| Owner | [Celestra](https://github.com/Celestra) |
| Repo | [Celestra/AetherOS](https://github.com/Celestra/AetherOS) |

CTAs must open the **repository** (`/Celestra/AetherOS`), not the org home alone — so visitors never land on an empty org page.

## Local

```bash
cd website
npm install
npm run dev
```

## Vercel

1. Project **Root Directory** = `website`
2. Framework = Next.js
3. Redeploy after merge so `/open-source` GitHub buttons hit `Celestra/AetherOS`
