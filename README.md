# SensAI - AI-Powered Learning Platform

A comprehensive learning platform built with Next.js frontend and FastAPI backend, featuring AI-powered forums, dynamic content management, and Google OAuth authentication.

## 🚀 Features

### Frontend (Next.js)
- **Modern UI**: Built with Next.js 15, TypeScript, and Tailwind CSS
- **Authentication**: Google OAuth integration with NextAuth.js
- **Dynamic Learning Hubs**: Interactive forum-style learning spaces
- **Real-time Features**: Live updates and notifications
- **Responsive Design**: Mobile-first approach with modern animations

### Backend (FastAPI)
- **AI Moderation**: OpenAI-powered content moderation and enhancement
- **Forum System**: Enhanced Q&A, discussions, polls, and notes
- **User Management**: Comprehensive user profiles and authentication
- **Database**: SQLite with comprehensive schema
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## 📋 Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Git
- Google Cloud Console account (for OAuth)
- OpenAI API key (for AI features)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

### 2. Frontend Setup

```bash
cd sensai-frontend
npm install
```

Copy the environment template:
```bash
cp .env.example .env
```

Update `.env` with your configuration:
- Google OAuth credentials
- Backend URL
- NextAuth secret

### 3. Backend Setup

```bash
cd ../sensai-ai
pip install -r requirements.txt
```

Copy the environment template:
```bash
cp .env.example .env
```

Update `.env` with your configuration:
- OpenAI API key
- Google OAuth credentials
- Database URL

## 🚀 Running the Application

### Start the Backend
```bash
cd sensai-ai
python src/api/main.py
# Backend runs on http://localhost:8003
```

### Start the Frontend
```bash
cd sensai-frontend
npm run dev
# Frontend runs on http://localhost:3002
```

## 📁 Project Structure

```
├── sensai-frontend/          # Next.js frontend application
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # Reusable React components
│   │   └── lib/            # Utility functions
│   ├── package.json
│   └── .env.example
├── sensai-ai/               # FastAPI backend application
│   ├── src/
│   │   ├── api/            # FastAPI application
│   │   └── database.db     # SQLite database
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## 🔧 Configuration

### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `http://localhost:3002/api/auth/callback/google`
6. Copy Client ID and Client Secret to your `.env` files

### OpenAI Setup
1. Get your API key from [OpenAI](https://platform.openai.com/)
2. Add it to the backend `.env` file

## 🌟 Key Features Implemented

- **Dynamic Hub Loading**: Real-time hub content without loading states
- **Enhanced Authentication**: Robust OAuth flow with fallback mechanisms
- **AI-Powered Forums**: Automated content moderation and enhancement
- **Advanced Filtering**: Search, categorization, and tagging system
- **Responsive Design**: Mobile-optimized interface
- **Real-time Updates**: Live post updates and notifications

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Loop**: 
   - Ensure Google OAuth redirect URIs match your local URLs
   - Check that backend is running on correct port

2. **Backend Connection Issues**:
   - Verify backend is running on port 8003
   - Check CORS settings in FastAPI

3. **Build Errors**:
   - Clear Next.js cache: `rm -rf .next`
   - Reinstall dependencies: `npm install`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Frontend Documentation](./sensai-frontend/README.md)
- [Backend Documentation](./sensai-ai/README.md)
- [API Documentation](http://localhost:8003/docs) (when backend is running)

## 📞 Support

If you encounter any issues or have questions, please open an issue on GitHub.