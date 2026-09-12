import os
import socket
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Header, Depends, Response, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from backend.parser import ResumeParser
from backend.analyzer import SkillAnalyzer
from backend.matcher import JobMatcher, JOB_PROFILES
from backend.database import UserManager
from backend.pdf_generator import generate_notes_pdf
from backend.openai_service import OpenAIService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResumeScannerAPI")

app = FastAPI(
    title="Universal AI Resume Scanner & Career Engine",
    description="Multi-Stream Resume Parser, ATS Audit, Bullet Rewriter & Timed AI Mock Interview",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterSchema(BaseModel):
    name: str
    email: str
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str

class ForgotUsernameSchema(BaseModel):
    gmail: str

class ForgotPasswordSchema(BaseModel):
    gmail: str
    new_password: str

class SendOtpSchema(BaseModel):
    gmail: str

class ResetPasswordOtpSchema(BaseModel):
    gmail: str
    otp_code: str
    new_password: str

class UpgradeSchema(BaseModel):
    plan: str = "pro"
    payment_ref: Optional[str] = "UPI_SUCCESS_150"

class BulletRewriteSchema(BaseModel):
    original_bullet: str
    target_role: Optional[str] = "Software / Tech Role"

class MockInterviewSchema(BaseModel):
    job_title: str
    missing_skills: Optional[List[str]] = []

class LiveInterviewGenSchema(BaseModel):
    job_title: str
    domain: Optional[str] = "General"
    extracted_skills: Optional[List[str]] = []

class AnswerEvalItem(BaseModel):
    question: str
    user_answer: str

class LiveInterviewEvalSchema(BaseModel):
    job_title: str
    answers: List[AnswerEvalItem]


def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    return UserManager.get_user_by_token(token)


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# --- FEATURE: 10-QUESTION TIMED LIVE MOCK INTERVIEW & AI ANSWER MATCH ENGINE ---

@app.post("/api/ai/live-interview/questions")
def generate_10_interview_questions(data: LiveInterviewGenSchema, authorization: Optional[str] = Header(None)):
    """Generate 10 random field-specific Technical & HR interview questions based directly on candidate extracted resume skills."""
    import random
    job_title = data.job_title
    domain = data.domain or "General Field"
    user_skills = [s.strip() for s in data.extracted_skills if s and len(s.strip()) > 1] if data.extracted_skills else []

    client = OpenAIService.get_client()
    if client:
        try:
            skills_str = ", ".join(user_skills[:12]) if user_skills else domain
            prompt = f"""Generate EXACTLY 10 RANDOM, DIRECT, PRACTICAL placement interview questions for a candidate targeting the role '{job_title}'.

EXTRACTED RESUME SKILLS TO TEST: [{skills_str}]

CRITICAL INSTRUCTIONS:
1. Generate RANDOM, UNIQUE questions tailored directly to testing the candidate's extracted resume skills ({skills_str}).
2. Ask DIRECT, PRACTICAL questions that test real day-to-day tools, syntax, formulas, or methods for those exact skills (e.g. if Python: ask Pandas/lists; if SQL: ask JOINs/GROUP BY; if Finance: ask NPV/IRR; if Healthcare: ask clinical protocols).
3. Randomize the questions across different skills so the test is dynamic every time.
4. Include 7 direct technical questions, 2 real-world scenario questions, and 1 HR/career vision question.
5. Provide concise practical hints and complete ideal model answers for each.

Return ONLY a valid JSON list of 10 objects: [{"id": 1, "category": "Technical/Scenario/HR", "question": "...", "hints": "...", "ideal_answer": "..."}]"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )

            content_text = response.choices[0].message.content.strip()
            if content_text.startswith("```json"):
                content_text = content_text.replace("```json", "").replace("```", "").strip()
            elif content_text.startswith("```"):
                content_text = content_text.replace("```", "").strip()
            import json
            questions = json.loads(content_text)
            random.shuffle(questions)
            for idx, q in enumerate(questions, 1):
                q["id"] = idx
            return {"success": True, "job_title": job_title, "questions": questions}
        except Exception as e:
            logger.warning(f"OpenAI interview generation error: {e}")

    # Skill-Aware Dynamic Fallback Suite
    generated_questions = []

    # Map specific extracted skills to direct technical questions
    skill_question_bank = {
        "python": [
            ("Technical Core", "How do list comprehensions work in Python? Write an example to filter even numbers from a list.", "Syntax: [x for x in list if x % 2 == 0].", "List comprehensions provide a concise syntax to create lists: `[x for x in lst if x % 2 == 0]`."),
            ("Technical Core", "What is the difference between mutable and immutable data types in Python?", "Lists/Dicts are mutable, Tuples/Strings are immutable.", "Mutable objects (lists, dicts) can be changed in place. Immutable objects (tuples, strings, ints) cannot be altered after creation.")
        ],
        "sql": [
            ("Technical Core", "What is the difference between WHERE and HAVING clauses in SQL?", "WHERE filters rows before aggregation; HAVING filters after GROUP BY.", "WHERE filters individual rows before grouping. HAVING filters aggregated results after GROUP BY."),
            ("Technical Core", "Explain INNER JOIN vs LEFT JOIN with a database table example.", "INNER returns matching rows only; LEFT returns all left rows plus matching right rows.", "INNER JOIN returns matching rows across both tables. LEFT JOIN retains all rows from the left table and appends matching right table columns.")
        ],
        "pandas": [
            ("Technical Core", "How do you handle missing NaN values in Pandas using dropna() vs fillna()?", "dropna() removes missing rows; fillna() replaces them with mean/median.", "dropna() removes rows containing null values. fillna() imputes missing values with specified scalars, mean, or median.")
        ],
        "excel": [
            ("Technical Core", "What is the difference between VLOOKUP and XLOOKUP in Microsoft Excel?", "XLOOKUP searches left or right without column index limitations.", "XLOOKUP replaces VLOOKUP by searching in any direction without needing static column index numbers.")
        ],
        "financial": [
            ("Technical Core", "What is Net Present Value (NPV) vs Internal Rate of Return (IRR)?", "Discounted future cash flows minus initial investment.", "NPV calculates the present value of future cash flows minus initial cost. IRR is the discount rate that sets NPV to zero.")
        ],
        "machine learning": [
            ("Technical Core", "Explain overfitting vs underfitting in machine learning models and how to fix them.", "High variance vs high bias; fix with regularization and cross-validation.", "Overfitting happens when a model learns training noise (high variance). Fix using L1/L2 regularization, cross-validation, and pruning.")
        ],
        "docker": [
            ("Technical Core", "What is the difference between a Docker image and a Docker container?", "Blueprint template vs running container instance.", "A Docker image is a read-only blueprint template. A Docker container is a runnable isolated instance of that image.")
        ],
        "tableau": [
            ("Technical Core", "How do calculated fields and dynamic parameters work in Tableau dashboards?", "Creating custom metrics and interactive user filters.", "Calculated fields create custom formulas. Parameters allow users to dynamically swap metrics and filters across worksheets.")
        ]
    }

    # Match candidate's extracted skills
    matched_qs = []
    if user_skills:
        for skill in user_skills:
            sk_lower = skill.lower()
            for key, q_list in skill_question_bank.items():
                if key in sk_lower:
                    for item in q_list:
                        matched_qs.append({
                            "category": item[0],
                            "question": item[1],
                            "hints": item[2],
                            "ideal_answer": item[3]
                        })

    # Domain-Aware Base Pool
    domain_lower = (domain + " " + job_title).lower()
    base_pool = [
        {"category": "Technical Core", "question": f"What are the most critical tools, libraries, or methodologies you use for {job_title}?", "hints": f"Mention industry tools and core frameworks for {job_title}.", "ideal_answer": f"Core execution relies on industry-standard tools, robust validation, and scalable pipelines tailored for {job_title}."},
        {"category": "Technical Core", "question": f"How do you validate data integrity and handle unexpected edge cases in {job_title} workflows?", "hints": "Mention schema validation, error handling, and logging.", "ideal_answer": "Data integrity is maintained using input sanitization, schema boundary checks, structured exception handling, and error telemetry."},
        {"category": "Scenario", "question": f"Scenario: A critical project task in {job_title} encounters unexpected failure 1 hour before a deadline. How do you resolve it?", "hints": "Isolate root cause, communicate with team, deploy fallback.", "ideal_answer": "Isolate root cause using log traces, communicate status transparently to stakeholders, and deploy verified fallback path."},
        {"category": "HR & Career", "question": f"Why do you want to excel in a {job_title} role, and how do you continuously upgrade your technical skills?", "hints": "Continuous learning, real-world projects, industry certifications.", "ideal_answer": "Driven by technical mastery, building high-impact solutions, and staying updated via hands-on projects and continuous research."}
    ]

    all_questions = matched_qs + base_pool
    random.shuffle(all_questions)

    # Pick 10 unique questions
    unique_qs = []
    seen = set()
    for q in all_questions:
        if q["question"] not in seen:
            seen.add(q["question"])
            unique_qs.append(q)
            if len(unique_qs) >= 10:
                break

    # If fewer than 10, fill up with generic domain prompts
    while len(unique_qs) < 10:
        idx_num = len(unique_qs) + 1
        unique_qs.append({
            "category": "Technical Core",
            "question": f"Question #{idx_num}: Describe a practical project where you applied {user_skills[idx_num % len(user_skills)] if user_skills else job_title} to solve a real-world problem.",
            "hints": "Mention problem statement, technical tools used, and measurable results.",
            "ideal_answer": "A strong answer highlights the core objective, technical steps taken, and quantitative metrics achieved."
        })

    for idx, q in enumerate(unique_qs, 1):
        q["id"] = idx

    return {"success": True, "job_title": job_title, "questions": unique_qs}


def detect_ai_or_web_copy(text: str) -> tuple[bool, str]:
    """Detect if candidate answer is copied directly from Google AI Overview, ChatGPT, or web search URLs."""
    if not text or not text.strip():
        return False, ""

    txt = text.strip()
    txt_lower = txt.lower()

    # 1. Google AI Overview Header or Hindi/Multi-lingual Overview text
    if "ai overview" in txt_lower or "ai-generated" in txt_lower or "google search" in txt_lower:
        return True, "[PLAGIARISM FLAGGED] Answer copied directly from Google AI Overview / Search engine."

    # 2. Web URLs or URL citations like [1] (https://...) or http://
    import re
    if re.search(r'\[\d+\]\s*\(\s*https?://', txt) or re.search(r'https?://[^\s]+\.(com|org|in|net|edu|io)', txt):
        return True, "[PLAGIARISM FLAGGED] Web search links or URL citations detected in answer ([1] https://...)."

    # 3. Citation brackets like [1], [2], [3] (2 or more citation numbers)
    citations = re.findall(r'\[\d+\]', txt)
    if len(citations) >= 2:
        return True, "[PLAGIARISM FLAGGED] External web search citation markers [1], [2] detected."

    # 4. Copy-pasted AI preamble phrases
    ai_phrases = [
        "as an ai language model",
        "as an ai,",
        "here is the direct breakdown",
        "certainly! here is",
        "sure! here is the difference",
        "i am an ai"
    ]
    if any(p in txt_lower for p in ai_phrases):
        return True, "[PLAGIARISM FLAGGED] Copied AI generator preamble text detected."

    return False, ""


@app.post("/api/ai/live-interview/evaluate")
def evaluate_10_interview_answers(data: LiveInterviewEvalSchema, authorization: Optional[str] = Header(None)):
    """Evaluate candidate answers against AI model answers and calculate exact match percentage with plagiarism detection."""
    import re
    total_q = len(data.answers)
    if total_q == 0:
        raise HTTPException(status_code=400, detail="No answers submitted for evaluation.")

    evaluations = []
    total_score_sum = 0

    client = OpenAIService.get_client()
    if client:
        try:
            for idx, ans in enumerate(data.answers, 1):
                if not ans.user_answer.strip():
                    evaluations.append({
                        "question_num": idx,
                        "question": ans.question,
                        "user_answer": "No answer provided.",
                        "match_percentage": 0,
                        "feedback": "⚠️ No answer provided. Practice explaining core technical mechanisms.",
                        "ideal_answer": "A complete response should explain technical principles and concrete tools."
                    })
                    continue

                # 1. Anti-Plagiarism / AI & Web Copy Check
                is_copy, copy_reason = detect_ai_or_web_copy(ans.user_answer)
                if is_copy:
                    evaluations.append({
                        "question_num": idx,
                        "question": ans.question,
                        "user_answer": ans.user_answer,
                        "match_percentage": 0,
                        "feedback": f"{copy_reason} Please write candidate responses in your own original words rather than copy-pasting from Google AI Overview or web search.",
                        "ideal_answer": "Answers must be written directly by candidate without web/AI copy-pasting."
                    })
                    continue

                prompt = f"""Compare the candidate's answer with the ideal technical model answer for '{data.job_title}':

Question: "{ans.question}"
Candidate Answer: "{ans.user_answer}"

CRITICAL ANTI-PLAGIARISM REQUIREMENT:
If the candidate answer appears to be copy-pasted directly from Google AI Overview or a website (e.g. contains URL links like 'https://...', 'AI Overview', or citation numbers '[1]'), flag it as plagiarized by setting match_percentage to 0 and providing feedback starting with '🚨 Plagiarism Flagged:'.

Return ONLY a JSON object:
{{
  "match_percentage": 85,
  "ideal_answer": "Concise model answer demonstrating full proficiency...",
  "feedback": "Detailed constructive evaluation highlighting strengths and missing points..."
}}"""

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=300
                )

                content_text = response.choices[0].message.content.strip()
                if content_text.startswith("```json"):
                    content_text = content_text.replace("```json", "").replace("```", "").strip()
                import json
                res = json.loads(content_text)
                score = res.get("match_percentage", 70)
                total_score_sum += score

                evaluations.append({
                    "question_num": idx,
                    "question": ans.question,
                    "user_answer": ans.user_answer,
                    "match_percentage": score,
                    "feedback": res.get("feedback", "Good technical alignment."),
                    "ideal_answer": res.get("ideal_answer", "Includes core frameworks and metrics.")
                })

            final_percentage = round(total_score_sum / total_q, 1)
            return {
                "success": True,
                "overall_score": final_percentage,
                "total_questions": total_q,
                "evaluations": evaluations
            }
        except Exception as e:
            logger.warning(f"OpenAI evaluation error: {e}")

    # Fallback Evaluation Engine with Plagiarism Detection & Keyword Matching
    for idx, ans in enumerate(data.answers, 1):
        if not ans.user_answer.strip():
            evaluations.append({
                "question_num": idx,
                "question": ans.question,
                "user_answer": "No answer provided.",
                "match_percentage": 0,
                "feedback": "⚠️ No answer provided. Practice explaining core technical mechanisms.",
                "ideal_answer": "A complete response should explain technical principles and concrete tools."
            })
            continue

        # Check Plagiarism / Web Copy-Paste
        is_copy, copy_reason = detect_ai_or_web_copy(ans.user_answer)
        if is_copy:
            evaluations.append({
                "question_num": idx,
                "question": ans.question,
                "user_answer": ans.user_answer,
                "match_percentage": 0,
                "feedback": f"{copy_reason} Please write candidate responses in your own original words rather than copy-pasting from Google AI Overview or web search.",
                "ideal_answer": "Answers must be written directly by candidate without web/AI copy-pasting."
            })
            continue

        # Evaluate Technical Keyword Overlap
        q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', ans.question.lower()))
        user_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', ans.user_answer.lower()))
        common_words = q_words.intersection(user_words)
        word_count = len(user_words)

        if word_count < 4:
            score = 15
            fb = "Answer is too brief. Please provide a detailed technical response."
        elif len(common_words) >= 1 or word_count >= 8:
            score = min(85, 40 + len(common_words) * 10 + min(30, word_count * 2))
            fb = "Strong technical answer alignment!" if score >= 70 else "Good attempt. Include more domain-specific tools and metrics."
        else:
            score = 30
            fb = "Answer lacks specific technical keywords related to the question."

        total_score_sum += score
        evaluations.append({
            "question_num": idx,
            "question": ans.question,
            "user_answer": ans.user_answer,
            "match_percentage": score,
            "feedback": fb,
            "ideal_answer": f"Ideal response for {ans.question[:40]}... includes core data structures and frameworks."
        })

    final_percentage = round(total_score_sum / total_q, 1)
    return {
        "success": True,
        "overall_score": final_percentage,
        "total_questions": total_q,
        "evaluations": evaluations
    }


# --- OTHER ENDPOINTS ---

@app.post("/api/ai/rewrite-bullet")
def rewrite_bullet_point(data: BulletRewriteSchema, authorization: Optional[str] = Header(None)):
    if not data.original_bullet or len(data.original_bullet.strip()) < 5:
        raise HTTPException(status_code=400, detail="Please enter a valid bullet point to rewrite.")

    client = OpenAIService.get_client()
    if client:
        try:
            prompt = f"""Rewrite the following resume bullet point into 3 professional, metric-driven, ATS-optimized bullet points for a candidate targeting '{data.target_role}':

Original Bullet Point: "{data.original_bullet}"

Return ONLY a JSON list of 3 strings: ["bullet 1", "bullet 2", "bullet 3"]."""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )

            content_text = response.choices[0].message.content.strip()
            if content_text.startswith("```json"):
                content_text = content_text.replace("```json", "").replace("```", "").strip()
            elif content_text.startswith("```"):
                content_text = content_text.replace("```", "").strip()
            import json
            rewritten_list = json.loads(content_text)
            return {"success": True, "original": data.original_bullet, "rewritten_bullets": rewritten_list}
        except Exception as e:
            logger.warning(f"OpenAI rewrite error: {e}")

    orig = data.original_bullet.strip().rstrip('.')
    fallback_bullets = [
        f"Engineered and deployed {orig}, increasing operational efficiency and team throughput by 32%.",
        f"Architected modular solutions for {orig}, reducing latency and execution error rates by 40%.",
        f"Spearheaded cross-functional delivery of {orig}, driving customer engagement and metric performance."
    ]
    return {"success": True, "original": data.original_bullet, "rewritten_bullets": fallback_bullets}


@app.post("/api/ai/interview-prep")
def generate_mock_interview(data: MockInterviewSchema, authorization: Optional[str] = Header(None)):
    job_title = data.job_title
    skills_str = ", ".join(data.missing_skills) if data.missing_skills else "General Core Skills"

    client = OpenAIService.get_client()
    if client:
        try:
            prompt = f"""Generate 5 Placement Technical & HR Interview Questions with detailed model answers for a candidate applying for '{job_title}' with focus on skills: [{skills_str}].

Return ONLY a JSON list of objects: [{"question": "...", "ideal_answer": "...", "category": "Technical/HR"}]"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )

            content_text = response.choices[0].message.content.strip()
            if content_text.startswith("```json"):
                content_text = content_text.replace("```json", "").replace("```", "").strip()
            import json
            qa_list = json.loads(content_text)
            return {"success": True, "job_title": job_title, "interview_questions": qa_list}
        except Exception as e:
            logger.warning(f"OpenAI interview prep error: {e}")

    fallback_qa = [
        {
            "question": f"Walk me through a complex project where you demonstrated proficiency in {job_title} skills.",
            "ideal_answer": f"In my recent project, I designed an end-to-end pipeline addressing real-world requirements. I structured the architecture using modular components, benchmarked performance, and optimized pipeline latency by 35%.",
            "category": "Technical Architecture"
        },
        {
            "question": f"How do you handle technical edge cases or unexpected system errors during production deployment?",
            "ideal_answer": "I implement robust input validation, boundary checks, structured error logging, and graceful fallback mechanisms to ensure 99.9% uptime without breaking client interfaces.",
            "category": "Problem Solving"
        },
        {
            "question": f"Why are you interested in a {job_title} role at our organization?",
            "ideal_answer": "I am passionate about building scalable, high-impact solutions. Your team's work in innovation aligns perfectly with my domain experience and technical continuous learning mindset.",
            "category": "HR & Fit"
        }
    ]
    return {"success": True, "job_title": job_title, "interview_questions": fallback_qa}


@app.post("/api/auth/register")
def register(data: RegisterSchema):
    try:
        if "@" not in data.email or "." not in data.email:
            raise HTTPException(status_code=400, detail="Invalid email address format.")
        if len(data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
        result = UserManager.register_user(data.name, data.email, data.password)
        return {"success": True, "message": "Account created successfully!", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
def login(data: LoginSchema):
    try:
        result = UserManager.login_user(data.email, data.password)
        return {"success": True, "message": "Login successful!", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/forgot-username")
def forgot_username(data: ForgotUsernameSchema):
    try:
        result = UserManager.find_username_by_gmail(data.gmail)
        return {
            "success": True, 
            "message": f"Account Found! Registered Candidate Name: '{result['name']}'", 
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/forgot-password")
def forgot_password(data: ForgotPasswordSchema):
    try:
        result = UserManager.reset_password_by_gmail(data.gmail, data.new_password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/send-otp")
def send_otp(data: SendOtpSchema):
    try:
        result = UserManager.request_password_otp(data.gmail)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/verify-otp-reset")
def verify_otp_reset(data: ResetPasswordOtpSchema):
    try:
        result = UserManager.verify_otp_and_reset_password(data.gmail, data.otp_code, data.new_password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/auth/me")
def get_profile(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return {"user": user}


@app.post("/api/subscription/upgrade")
def upgrade_plan(data: UpgradeSchema, authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in or create an account to upgrade to Pro Plan.")

    updated_user = UserManager.upgrade_subscription(user["id"], plan="pro")
    return {
        "success": True,
        "message": "🎉 Congratulations! You have successfully upgraded to Pro Plan (₹150/month). Enjoy UNLIMITED AI Scans & All Features!",
        "user": updated_user
    }


@app.get("/api/user/history")
def get_history(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    if not user:
        return {"history": []}
    history = UserManager.get_user_scan_history(user["id"])
    return {"history": history}





@app.get("/api/health")
def health_check():
    openai_key_present = bool(os.environ.get("OPENAI_API_KEY"))
    return {
        "status": "online", 
        "message": "Universal AI Resume Scanner API is running.",
        "openai_configured": openai_key_present
    }


@app.get("/api/network-info")
def get_network_info():
    local_ip = get_local_ip()
    port = 8000
    return {
        "local_ip": local_ip,
        "port": port,
        "local_url": f"http://localhost:{port}",
        "network_url": f"http://{local_ip}:{port}",
        "message": f"Share http://{local_ip}:{port} with devices on the same Wi-Fi network!"
    }


@app.get("/api/jobs")
def get_job_profiles():
    profiles = []
    for key, item in JOB_PROFILES.items():
        profiles.append({
            "key": key,
            "title": item["title"],
            "domain": item["domain"],
            "stream": item["stream"],
            "description": item["description"],
            "core_skills": item["core_skills"]
        })
    return {"jobs": profiles}


# --- SCAN ENDPOINT ---

@app.post("/api/scan")
async def scan_resume(
    file: UploadFile = File(...),
    target_job: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided.")

    user = get_current_user(authorization)
    user_id = user["id"] if user else None

    UserManager.check_and_increment_scan(user_id)

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".pdf", ".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: PDF, JPG, JPEG, PNG."
        )

    try:
        contents = await file.read()

        # Step 1: Document Extraction
        parser_result = ResumeParser.parse_file(filename, contents)
        raw_text = parser_result["raw_text"]

        if not raw_text or len(raw_text.strip()) < 15:
            raw_text += "\n[Note: File contained minimal extractable text]."

        # Step 2: Information Extraction, Skill Parsing & ATS Audit
        resume_analysis = SkillAnalyzer.analyze_resume(raw_text)

        # Step 3: Hybrid AI Engine & Market Analytics
        job_match = JobMatcher.calculate_match(
            candidate_skills=resume_analysis["all_skills_list"],
            target_job_key=target_job,
            raw_resume_text=raw_text
        )

        if user_id:
            UserManager.log_scan_history(
                user_id=user_id,
                filename=filename,
                job_title=job_match["target_job_analysis"]["title"],
                match_percentage=job_match["target_job_analysis"]["match_percentage"]
            )

        updated_user = UserManager.get_user_by_id(user_id) if user_id else None

        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "file_type": parser_result["file_type"],
            "ocr_used": parser_result["ocr_used"],
            "char_count": parser_result["char_count"],
            "word_count": parser_result["word_count"],
            "user": updated_user,
            "contact_info": resume_analysis["contact_info"],
            "experience_level": resume_analysis["experience_level"],
            "ats_audit": resume_analysis["ats_audit"],
            "categorized_skills": resume_analysis["skills"],
            "extracted_skills_list": resume_analysis["all_skills_list"],
            "total_skills_count": resume_analysis["total_skills_detected"],
            "target_job_analysis": job_match["target_job_analysis"],
            "top_matching_job": job_match["top_matching_job"],
            "top_match_percentage": job_match["top_match_percentage"],
            "all_job_recommendations": job_match["all_job_recommendations"],
            "extracted_text_preview": raw_text[:600] + ("..." if len(raw_text) > 600 else "")
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error scanning resume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")


static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(static_dir, "index.html"))
