# AI Resume Scanner, Skill Gap Analyzer & Career Matcher

> **4th Year B.Tech Capstone Project — AI & Data Science (AI&DS)**

An end-to-end artificial intelligence application that scans resumes in **PDF, JPG, JPEG, and PNG** formats, extracts candidate skills using Natural Language Processing (NLP) and Optical Character Recognition (OCR), identifies critical **missing skills** against target job roles, computes **match percentage scores**, recommends optimal career paths, and deploys across local networks (LAN) for cross-device access.

---

## 🌟 Key Features

1. **Multi-Format Document Ingestion**:
   - Native text extraction for digital PDF files (`pypdf` / `pdfplumber`).
   - Image OCR processing for scanned paper resumes and image formats (`pytesseract` + Pillow contrast enhancement).

2. **NLP Skill Extraction Engine**:
   - Comprehensive taxonomy covering **Programming Languages, AI/ML, Data Science, Data Engineering, Web Development, Cloud & MLOps, Databases, and Soft Skills**.
   - Automatic contact detail parsing (email, phone number) and timeline/experience level detection.

3. **Skill Gap Analysis & Job Recommendation**:
   - Cosine Similarity & TF-IDF vectorization against industry benchmark job profiles (AI Engineer, Data Scientist, Data Analyst, Full-Stack Developer, MLOps Engineer, Data Engineer).
   - Priority categorization of **Missing Skills**:
     - 🔥 **High Priority**: Core required skills missing from candidate profile.
     - 🌟 **Medium Priority**: Preferred / optional competencies.
   - Customized upskilling roadmap with learning suggestions for each missing skill.

4. **Network Deployment (LAN Sharing)**:
   - Server runs on `0.0.0.0:8000`, enabling access across all phones, laptops, and devices on the same Wi-Fi network.
   - Built-in automatic IP detection and quick link sharing.

5. **Glassmorphic Interactive Web Dashboard**:
   - Dark mode modern UI with responsive cards, drag-and-drop file uploader, live score gauge, category tag badges, and PDF summary report download.

---

## 🏗 System Architecture

```
                               ┌───────────────────────────┐
                               │  User Upload (PDF/JPG)    │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │ Document Parsing Engine   │
                               │ (pdfplumber / PyTesseract)│
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   NLP Skill Analyzer      │
                               │ (Taxonomy & Regex Patterns│
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │  Job Gap & Match Engine   │
                               │ (Cosine Similarity & Gap) │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │ Glassmorphic Web Dashboard│
                               │ (FastAPI + LAN 0.0.0.0)   │
                               └───────────────────────────┘
```

---

## 🚀 How to Run the Project

### Prerequisites
- Python 3.9+
- Tesseract OCR (Optional, for scanned image files. Download from: https://github.com/UB-Mannheim/tesseract/wiki)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Launch Network Deployment Server
```bash
python run_app.py
```
or double-click `start.bat` on Windows.

### Step 3: Access Web Application
- **On Local PC**: `http://localhost:8000`
- **On Mobile / Devices on same Wi-Fi**: `http://<YOUR_LOCAL_IP>:8000` (Displayed in terminal output)

---

## 🎓 4th Year B.Tech Presentation & Viva Q&A Guide

### Q1: What machine learning / NLP techniques are used in this project?
- **Answer**: The project uses **Rule-based NLP Named Entity Extraction**, **Regex Pattern Matching**, **TF-IDF (Term Frequency-Inverse Document Frequency) Vectorization**, and **Cosine Similarity metrics** to calculate candidate fit scores against high-dimensional job requirement matrices.

### Q2: How does it handle image resumes (JPG/JPEG)?
- **Answer**: Image resumes are pre-processed using `Pillow` (grayscale conversion, contrast & sharpness enhancement) and then parsed using `Tesseract OCR` engine to extract textual data before running through the NLP analyzer.

### Q3: How is the application deployed on a network?
- **Answer**: The backend is powered by **FastAPI** listening on host `0.0.0.0`. This allows any client connected to the same local area network (Wi-Fi/LAN) to make API calls to the server via the host machine's IPv4 address.
