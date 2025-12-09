# Resume Ranker Pro 🚀

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An AI-powered resume ranking system that uses semantic similarity matching to automatically rank resumes against job descriptions. Built with state-of-the-art NLP techniques including Sentence-Transformers and FAISS for efficient vector search.

## ✨ Features

- 🤖 **AI-Powered Ranking**: Uses S-BERT (Sentence-BERT) for semantic similarity matching
- 📄 **PDF Resume Processing**: Automatically extracts text from PDF resumes
- 🔍 **Skill Extraction**: Intelligent skill detection using NLP
- ⚡ **Fast Vector Search**: FAISS-powered similarity search for quick results
- 🎨 **Modern Web UI**: Beautiful, responsive interface built with Bootstrap 5
- 📊 **Ranked Results**: Displays top matching resumes with similarity scores
- 🔄 **Real-time Processing**: Upload and rank resumes instantly

## 🛠️ Technology Stack

**Backend:**
- FastAPI - Modern, fast web framework
- Sentence-Transformers - Semantic embeddings (all-MiniLM-L6-v2)
- FAISS - Vector similarity search
- spaCy - NLP for skill extraction
- Uvicorn - ASGI server

**Frontend:**
- Bootstrap 5 - Responsive UI
- Vanilla JavaScript - No framework dependencies
- HTML5/CSS3 - Modern web standards

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## 🚀 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/kadvsk2006/Automated-Resume-Screening
cd Resume_Ranker_Pro
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

**Windows:**
```bash
# Double-click start.bat or run:
start.bat
```

**Linux/Mac:**
```bash
python run.py
```

The application will start at `http://localhost:8000`

## 📖 Usage

1. **Start the application** using the methods above
2. **Open your browser** and navigate to `http://localhost:8000`
3. **Enter a job description** in the text area
4. **Upload a resume** (PDF format) or use the existing database
5. **Click "Rank Resumes"** to get ranked results
6. **View results** with similarity scores and extracted skills

## 📁 Project Structure

```
Resume_Ranker_Pro/
├── app/                    # Application code
│   ├── main.py            # FastAPI application
│   ├── csv_loader.py      # CSV data loader
│   ├── skill_extractor.py # Skill extraction logic
│   ├── text_preprocessor.py # Text preprocessing
│   └── utils.py           # Utility functions
├── static/                # Static files (CSS, JS)
├── templates/             # HTML templates
├── uploads/               # Uploaded resume storage
├── requirements.txt       # Python dependencies
├── run.py                # Application runner
├── start.bat             # Windows startup script
└── README.md             # This file
```

## 📚 Documentation

- **Project Report**: See `PROJECT_REPORT.md` for detailed technical documentation
- **Full Report**: `GEN_AI_Final_Project_Report.docx` - Complete project report
- **Presentation**: `Resume_Ranker_Pro_Presentation.pptx` - Project presentation

## 🎯 How It Works

1. **Text Extraction**: PDF resumes are processed to extract text content
2. **Embedding Generation**: Text is converted to vector embeddings using Sentence-Transformers
3. **Similarity Matching**: Job descriptions and resumes are compared using cosine similarity
4. **Ranking**: Resumes are ranked based on semantic similarity scores
5. **Skill Extraction**: Relevant skills are identified using NLP techniques
6. **Results Display**: Top matches are displayed with scores and extracted skills

## 🔧 Configuration

The application uses default settings, but you can modify:
- **Port**: Change in `run.py` (default: 8000)
- **Model**: Modify in `app/main.py` (default: all-MiniLM-L6-v2)
- **Top Results**: Adjust in the ranking logic

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**kadvsk2006**
- GitHub: [https://github.com/kadvsk2006)

## 🙏 Acknowledgments

- Sentence-Transformers library by UKP Lab
- FAISS by Facebook AI Research
- FastAPI framework
- Bootstrap team for the UI framework

## 📞 Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

---

**Built with ❤️ using FastAPI, Sentence-Transformers, and Bootstrap 5**
