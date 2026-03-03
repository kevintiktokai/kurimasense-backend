# KurimaSense Deployment Guide 🚀

Follow these steps to deploy the KurimaSense platform. Each part of the system is hosted separately to ensure maximum performance and scalability.

## 1. Frontend: Vercel Setup
**Repository**: [kevintiktokai/kurima-sense](https://github.com/kevintiktokai/kurima-sense)

### Configuration
- **Framework Preset**: Next.js
- **Root Directory**: `./` (The repo root)
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

### Environment Variables
Click on "Settings" > "Environment Variables" and add:
- `NEXT_PUBLIC_API_URL`: The URL of your Render backend (e.g., `https://kurimasense-backend.onrender.com`)
- `NEXT_PUBLIC_MAPBOX_TOKEN`: (Optional) If you use Mapbox for high-res sat view.

---

## 2. Backend: Render Setup
**Repository**: [kevintiktokai/kurimasense-backend](https://github.com/kevintiktokai/kurimasense-backend)

### Configuration
1. Create a "Web Service" on Render.
2. **Runtime**: Python 3
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

### Environment Variables
Add these in the "Environment" tab:
- `OPENAI_API_KEY`: Your OpenAI API Key for the Agronomist engine.
- `DATABASE_URL`: **IMPORTANT: Use the IPv4 Pooler URL**
  > [!WARNING]
  > Render does not support IPv6. In Supabase Settings > Database, look for the **Connection Pooling** section and use the **Pooler** URL (usually port 6543 or with a hostname like `pooler.supabase.com`). 
  > DO NOT use the "Direct Connection" URL (`db.xxxx.supabase.co`) as it will result in a "Network is unreachable" error.
- `CORS_ORIGINS`: Your Vercel frontend URL (e.g., `https://kurima-sense.vercel.app`)

---

## 3. Database: Supabase
Ensure your Postgres database is running and the `init_knowledge_base.sql` has been run. 

### Troubleshooting the "Network is unreachable" Error
If you see this error in Render logs, it means your `DATABASE_URL` is pointing to an IPv6 address.
1. Go to Supabase > Settings > Database.
2. Under **Connection Pooler**, toggle it to **Enabled**.
3. Copy the **Transaction Mode** connection string.
4. Update the `DATABASE_URL` on Render.

---

## ✅ Deployment Checklist
> [!IMPORTANT]
> - Ensure `NEXT_PUBLIC_API_URL` on Vercel matches your Render URL.
> - Ensure `CORS_ORIGINS` on Render includes your Vercel URL.
> - Verify that the OpenAI API key is active.

### Root Directory Clarification
For Vercel, since the repository `kurima-sense` was created directly from the `frontend` folder, you do **not** need to change the root directory setting. It should remain as **`./`**.
