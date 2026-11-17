# 📝 ATS Resume Scanner using Gemini 1.5 Flash

An AI‑powered Applicant Tracking System (ATS) Resume Scanner that evaluates a candidate’s resume against a job description using **Gemini 1.5 Flash**. The tool simulates how a real ATS or recruiter analyses resumes, offering feedback, skill‑gap suggestions, and a match‑percentage score.

---

## 🚀 Features

- **Resume vs JD Comparison** – analyses alignment between resume and job description.  
- **Match Percentage** – returns a calculated match score with missing keywords.  
- **Skill‑Gap Suggestions** – recommends improvements to improve alignment.  
- **PDF → Image Conversion** – converts the uploaded PDF to an image for Gemini vision input.  
- **Streamlit UI** – simple web interface for uploading PDFs and pasting job descriptions.  

---

## 📌 Use Cases

| User               | Benefit                                                             |
|--------------------|---------------------------------------------------------------------|
| **Job Seekers**    | Check fit before applying and tailor resumes accordingly.           |
| **Career Coaches** | Provide data‑driven feedback to candidates.                         |
| **HR Teams**       | Pre‑screen resumes quickly with AI assistance.                      |
| **Students**       | Understand industry expectations and enhance resumes.               |

---

## ❓ Problem Statement

Recruiters use ATS systems to filter resumes based on keyword matches. Candidates rarely know how well their resumes align with a posting.  
This project automates that analysis by:

1. **Scraping** the job description text (user‑supplied).  
2. **Converting** the resume PDF to an image.  
3. **Feeding** both into Gemini 1.5 Flash for multimodal reasoning.  
4. **Returning** professional feedback, skill gaps, and a match percentage.

---

## ⚙️ Tech Stack

- **Frontend**  : Streamlit  
- **LLM API**  : Google Gemini 1.5 Flash (`google-generativeai`)  
- **Image Conversion**  : pdf2image + Pillow (Poppler backend)  
- **Env Management**  : python‑dotenv  

---

## 🛠️ Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/praphulchandra-nitdgp/ATS-Resume-Scanner.git
cd ATS-Resume-Scanner
```

### 2. Create and Activate a Virtual Env (optional)
```bash
python3 -m venv ats-venv
source ats-venv/bin/activate      # macOS / Linux
# or
ats-venv\Scripts\activate       # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
> **Poppler note (macOS):**  
> `brew install poppler`

### 4. Add Your Gemini API Key
1. Get a key from **Google AI Studio** → *API Keys*.  
2. Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_gemini_key_here
   ```

### 5. Run the App
```bash
streamlit run app.py
```

---

## 🔑 How to Generate a Gemini API Key
1. Sign in to <https://makersuite.google.com>.  
2. Go to **Settings → API Keys**.  
3. Click **“Create API key”** and copy it.  
4. Paste it into the `.env` file as shown above.

---

## 📸 Screenshot
_Add a screenshot here once you have one, e.g._

```md
![App UI](screenshots/app.png)
```

---

## 🧠 Future Ideas
- Export feedback as PDF.  
- Support multiple resume pages.  
- Integrate auto‑email functionality.  
- Add additional AI models for comparison.

---

## 📝 License
MIT

---

## 👤 Author
Made with ❤️ by [Ganapathri Praphul Chandra](https://www.linkedin.com/in/praphul-chandra-ganapathri-018a692a8/)

## Setup 

### For Windows

1. **Install Python** from [python.org](https://www.python.org/downloads/windows/).
2. **Install Poppler for Windows**:
   - Download from: https://github.com/oschwartz10612/poppler-windows/releases/
   - Extract and note the path (e.g., `C:\path\to\poppler\bin`).
   - Add the bin folder path to your System Environment Variables under `Path`.
3. Create `.env` file and follow remaining steps as mentioned above.

### For Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install poppler-utils
```

Then continue with the Python virtual environment setup.

### For macOS

```bash
brew install poppler
```

Then continue with the Python virtual environment setup.

Ensure you point `poppler_path` correctly in `pdf2image.convert_from_bytes()` if needed.
