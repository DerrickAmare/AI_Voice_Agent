# Voice AI Resume Builder

A sophisticated AI-powered resume building application that combines voice interaction with intelligent multi-agent systems to create professional, ATS-optimized resumes.

## 🚀 Features

### Core Functionality
- **Voice Interaction**: Natural conversation through speech recognition and text-to-speech
- **Multi-Agent System**: Specialized AI agents for different aspects of resume building
- **Real-time Processing**: Live conversation and resume generation
- **Multiple Output Formats**: HTML, PDF, Word, Text, and JSON formats
- **ATS Optimization**: Ensures resumes pass Applicant Tracking Systems

### AI Agents
1. **ConversationAgent**: Career counselor that guides users through natural conversation
2. **ResumeAnalyzerAgent**: Analyzes resume content for gaps and improvements
3. **ContentOptimizerAgent**: Optimizes content for maximum impact
4. **FormattingAgent**: Handles professional formatting and structure

## 🏗️ Architecture

```
demo-va/
├── src/
│   ├── agents/              # AI Agent System
│   │   ├── base_agent.py    # Base agent class
│   │   ├── conversation_agent.py
│   │   ├── resume_analyzer_agent.py
│   │   ├── content_optimizer_agent.py
│   │   ├── formatting_agent.py
│   │   └── agent_coordinator.py
│   ├── services/            # Core Services
│   │   ├── voice_service.py
│   │   ├── conversation_engine.py
│   │   ├── resume_parser.py
│   │   ├── resume_builder.py
│   │   └── agent_service.py
│   ├── models/              # Data Models
│   │   └── resume_models.py
│   └── utils/               # Utilities
├── examples/                # Example files
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
└── .env.example            # Environment configuration
```

## 🤖 AI Agent System

### Agent Architecture

#### 🤖 **ConversationAgent**
- **Role**: Career Counselor & Resume Expert
- **Purpose**: Guides users through natural conversation to gather resume information
- **Features**:
  - Warm, encouraging conversation style
  - One focused question at a time
  - Digs deeper to uncover hidden achievements
  - Helps users articulate quantifiable results
  - Identifies transferable skills

#### �� **ResumeAnalyzerAgent**
- **Role**: Resume Analysis Expert
- **Purpose**: Analyzes resume content for gaps and improvements
- **Features**:
  - ATS optimization analysis
  - Industry-specific keyword suggestions
  - Content gap identification
  - Achievement quantification opportunities
  - Competitive positioning analysis

#### ✨ **ContentOptimizerAgent**
- **Role**: Resume Content Strategist
- **Purpose**: Optimizes resume content for maximum impact
- **Features**:
  - Action verb optimization
  - Quantifiable achievement enhancement
  - ATS keyword integration
  - Impact statement creation
  - Industry-specific language adaptation

#### 📄 **FormattingAgent**
- **Role**: Resume Formatting Specialist
- **Purpose**: Handles resume formatting and structure optimization
- **Features**:
  - ATS-compatible formatting
  - Multiple output formats (HTML, PDF, Word, Text, JSON)
  - Visual hierarchy optimization
  - Print and digital optimization

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- macOS (for voice features)
- OpenAI API key (for AI agents)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd demo-va
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Install audio dependencies (macOS)**
   ```bash
   # Install Homebrew if not already installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install PortAudio
   brew install portaudio
   
   # Reinstall PyAudio
   pip uninstall pyaudio
   pip install pyaudio
   ```

## 🚀 Usage

### Start the Application
```bash
source venv/bin/activate
python main.py
```

The application will be available at `http://localhost:8000`

### API Endpoints

#### Traditional Resume Building
- `POST /api/conversation` - Start/continue conversation
- `POST /api/resume/generate` - Generate resume
- `GET /api/resume/{session_id}` - Get resume data

#### AI Agent System
- `POST /api/agents/start` - Start agent conversation
- `POST /api/agents/continue` - Continue agent conversation
- `POST /api/agents/format` - Format resume with agents
- `GET /api/agents/status/{session_id}` - Get session status
- `GET /api/agents/info` - Get agent information

#### Voice Features
- `POST /api/voice/speak` - Text-to-speech
- `POST /api/voice/start-listening` - Start voice recognition
- `POST /api/voice/stop-listening` - Stop voice recognition

### Example Usage

#### Using the Agent System
```python
import requests

# Start agent conversation
response = requests.post('http://localhost:8000/api/agents/start', json={
    'session_id': 'user_123',
    'target_role': 'Data Scientist',
    'industry': 'Technology'
})

# Continue conversation
response = requests.post('http://localhost:8000/api/agents/continue', json={
    'session_id': 'user_123',
    'user_input': 'I have 5 years of experience in machine learning'
})

# Format resume
response = requests.post('http://localhost:8000/api/agents/format', json={
    'session_id': 'user_123',
    'format': 'html'
})
```

## 🔧 Configuration

### Environment Variables
```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=1000
AGENT_MODEL=gpt-4
```

### Agent Customization
Each agent can be customized by modifying their system prompts in the respective agent files:
- `src/agents/conversation_agent.py`
- `src/agents/resume_analyzer_agent.py`
- `src/agents/content_optimizer_agent.py`
- `src/agents/formatting_agent.py`

## 🧪 Testing

```bash
# Run basic health check
curl http://localhost:8000/api/health

# Test agent system
curl http://localhost:8000/api/agents/info

# Test voice service
curl http://localhost:8000/api/voice/status
```

## 🐛 Troubleshooting

### Common Issues

1. **Python command not found**
   - Use `python3` instead of `python` on macOS

2. **Audio dependencies missing**
   - Install PortAudio: `brew install portaudio`
   - Reinstall PyAudio: `pip uninstall pyaudio && pip install pyaudio`

3. **OpenAI API errors**
   - Ensure API key is set in `.env` file
   - Check API quota and rate limits

4. **Agent endpoints not found**
   - Restart the application
   - Check that agent endpoints are properly registered

### Debug Mode
```bash
# Enable debug logging
export PYTHONPATH=.
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python main.py
```

## 🚀 Deployment

### Production Setup
1. Set up proper environment variables
2. Configure reverse proxy (nginx)
3. Use production ASGI server (gunicorn)
4. Set up monitoring and logging

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- FastAPI for the web framework
- SpeechRecognition and pyttsx3 for voice features
- All contributors and users

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting section

---

**Note**: This application requires an OpenAI API key for full functionality. Without it, the agents will operate in demo mode with limited capabilities.
