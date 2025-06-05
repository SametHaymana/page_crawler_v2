# 🚀 Deployment Guide - Genetic Page Crawler Service

## Option 1: Streamlit Community Cloud (RECOMMENDED - FREE)

### Prerequisites
1. GitHub account
2. Your Azure OpenAI credentials

### Steps

#### 1. Prepare Your Repository
```bash
# Create a GitHub repository and push your code
git init
git add .
git commit -m "Initial commit - Genetic Page Crawler Service"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/genetic-page-crawler.git
git push -u origin main
```

#### 2. Create Secrets File
Create `.streamlit/secrets.toml` in your repo:
```toml
# .streamlit/secrets.toml
AZURE_OPENAI_API_KEY = "your-azure-openai-api-key"
AZURE_OPENAI_ENDPOINT = "https://your-endpoint.openai.azure.com"
AZURE_OPENAI_DEPLOYMENT_NAME = "your-deployment-name"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
```

#### 3. Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file path: `streamlit_app.py`
6. Click "Deploy"

Your app will be live at: `https://your-app-name.streamlit.app`

---

## Option 2: Railway (Easy with Database Support)

### Prerequisites
- GitHub account
- Railway account (free tier available)

### Steps

#### 1. Create railway.json
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0"
  }
}
```

#### 2. Deploy
1. Go to [railway.app](https://railway.app)
2. Connect GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy automatically

---

## Option 3: Render (Free Tier Available)

### Prerequisites
- GitHub account
- Render account

### Steps

#### 1. Create render.yaml
```yaml
services:
  - type: web
    name: genetic-page-crawler
    env: python
    buildCommand: "pip install -r requirements_deploy.txt"
    startCommand: "streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0"
    envVars:
      - key: AZURE_OPENAI_API_KEY
        sync: false
      - key: AZURE_OPENAI_ENDPOINT
        sync: false
      - key: AZURE_OPENAI_DEPLOYMENT_NAME
        sync: false
      - key: AZURE_OPENAI_API_VERSION
        value: "2024-02-15-preview"
```

#### 2. Deploy
1. Go to [render.com](https://render.com)
2. Connect GitHub repository
3. Select "Web Service"
4. Configure environment variables
5. Deploy

---

## Option 4: Google Cloud Run (Scalable)

### Prerequisites
- Google Cloud account
- Docker installed

#### 1. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements_deploy.txt .
RUN pip install -r requirements_deploy.txt

COPY . .

EXPOSE 8080

CMD streamlit run streamlit_app.py --server.port 8080 --server.address 0.0.0.0
```

#### 2. Deploy
```bash
# Build and deploy
gcloud run deploy genetic-page-crawler \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Option 5: Heroku (Classic Option)

### Prerequisites
- Heroku account
- Heroku CLI

#### 1. Create Procfile
```
web: streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

#### 2. Create runtime.txt
```
python-3.11.6
```

#### 3. Deploy
```bash
heroku create your-app-name
heroku config:set AZURE_OPENAI_API_KEY=your-key
heroku config:set AZURE_OPENAI_ENDPOINT=your-endpoint
heroku config:set AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment
heroku config:set AZURE_OPENAI_API_VERSION=2024-02-15-preview
git push heroku main
```

---

## 🔧 Configuration for Deployment

### Environment Variables Needed
```bash
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Security Considerations
1. **Never commit `.env` files** - use platform-specific secret management
2. **Use HTTPS** - all mentioned platforms provide SSL certificates
3. **Limit API usage** - set usage limits in Azure OpenAI
4. **Monitor costs** - track API calls and usage

### Performance Optimization
1. **Use caching** - Streamlit's `@st.cache_data` for expensive operations
2. **Limit concurrent users** - consider rate limiting
3. **Optimize page crawling** - reduce max pages for production
4. **Use CDN** - for static assets if needed

---

## 📊 Comparison of Deployment Options

| Platform | Cost | Ease | Scalability | Custom Domain | Database |
|----------|------|------|-------------|---------------|----------|
| Streamlit Cloud | Free | ⭐⭐⭐⭐⭐ | Medium | ✅ | ❌ |
| Railway | Free tier | ⭐⭐⭐⭐ | High | ✅ | ✅ |
| Render | Free tier | ⭐⭐⭐⭐ | High | ✅ | ✅ |
| Google Cloud Run | Pay-per-use | ⭐⭐⭐ | Very High | ✅ | ✅ |
| Heroku | $7/month | ⭐⭐⭐ | High | ✅ | ✅ |

---

## 🎯 Recommended Approach

**For Quick Start**: Use **Streamlit Community Cloud**
- Completely free
- Easiest setup
- Perfect for demos and small-scale usage

**For Production**: Use **Railway** or **Google Cloud Run**
- Better performance
- More configuration options
- Scalable based on demand

---

## 🔍 Post-Deployment Testing

After deployment, test these features:
1. ✅ Single website analysis
2. ✅ Batch processing
3. ✅ Sector validation
4. ✅ Export functionality
5. ✅ Error handling

---

## 🆘 Troubleshooting

### Common Issues:
1. **API Key not working**: Check environment variables
2. **Slow performance**: Reduce max pages per website
3. **Memory issues**: Use smaller batch sizes
4. **Timeout errors**: Add request timeouts

### Getting Help:
- Check platform-specific logs
- Verify environment variables
- Test locally first
- Check Azure OpenAI quota limits 