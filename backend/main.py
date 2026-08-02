import os
import socket
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Header, Depends, Response, Query
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
    """Generate 10 field-specific Technical & HR interview questions with ideal AI model answers."""
    job_title = data.job_title
    domain = data.domain or "General Field"

    client = OpenAIService.get_client()
    if client:
        try:
            prompt = f"""Generate EXACTLY 10 technical and behavioral placement interview questions for '{job_title}' ({domain}).
Include 7 technical core, 2 scenario, and 1 HR question.

Return ONLY a JSON list of 10 objects: [{"id": 1, "category": "Technical/Scenario/HR", "question": "...", "hints": "Key concepts...", "ideal_answer": "Comprehensive model answer..."}]"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1400
            )

            content_text = response.choices[0].message.content.strip()
            if content_text.startswith("```json"):
                content_text = content_text.replace("```json", "").replace("```", "").strip()
            elif content_text.startswith("```"):
                content_text = content_text.replace("```", "").strip()
            import json
            questions = json.loads(content_text)
            return {"success": True, "job_title": job_title, "questions": questions}
        except Exception as e:
            logger.warning(f"OpenAI interview generation error: {e}")

    # Built-in Fallback 10-Question Suite
    fallback_10 = [
        {"id": 1, "category": "Technical Core", "question": f"Explain the fundamental architecture and core principles of {job_title}.", "hints": "Mention core data models, design patterns, and main frameworks.", "ideal_answer": f"Core architecture in {job_title} relies on modular data pipelines, strong separation of concerns, scalable API interfaces, and robust state management."},
        {"id": 2, "category": "Technical Core", "question": f"How do you optimize system performance and reduce execution latency in {job_title}?", "hints": "Mention caching, indexing, profiling, and memory efficiency.", "ideal_answer": "Optimization requires caching frequent queries, indexing database tables, profiling memory bottlenecks, and leveraging non-blocking asynchronous execution."},
        {"id": 3, "category": "Technical Core", "question": f"What are the most critical tools, libraries, or platforms you use in {job_title}?", "hints": "List industry-standard software, APIs, and version control.", "ideal_answer": "Standard tools include Git for version control, Docker for containerization, SQL for relational data querying, and specialized domain libraries."},
        {"id": 4, "category": "Technical Core", "question": f"Describe how you validate input data and handle unexpected runtime errors or edge cases.", "hints": "Talk about input sanitization, try-except blocks, and logging.", "ideal_answer": "Input validation is enforced using schema parsers, boundary sanitization checks, explicit exception handling, and structured error logging telemetry."},
        {"id": 5, "category": "Technical Core", "question": f"What is the difference between synchronous and asynchronous execution in {job_title} workflows?", "hints": "Explain blocking I/O vs non-blocking concurrency.", "ideal_answer": "Synchronous execution blocks thread execution until operations complete, while asynchronous execution yields control back to event loops for higher concurrency throughput."},
        {"id": 6, "category": "Technical Core", "question": f"How do you ensure data security, privacy, and access control in production systems?", "hints": "Mention encryption, authentication tokens, and compliance.", "ideal_answer": "Data security is implemented via TLS/HTTPS encryption in transit, AES-256 at rest, OAuth2/JWT token authentication, and strict RBAC permission scoping."},
        {"id": 7, "category": "Technical Core", "question": f"Explain how you conduct testing (unit, integration, or validation) before deployment.", "hints": "Talk about test suites, boundary testing, and continuous integration.", "ideal_answer": "Testing requires automated unit test suites, mock dependency injection, boundary testing, and automated CI/CD validation pipelines."},
        {"id": 8, "category": "Scenario", "question": f"Describe a situation where a production pipeline in {job_title} failed. How did you diagnose and fix it?", "hints": "Use STAR method: Situation, Task, Action, Result.", "ideal_answer": "Diagnosed failure using application log tracebacks, isolated root cause in data type parsing, patched exception handler, and deployed regression test suite."},
        {"id": 9, "category": "Scenario", "question": f"How do you prioritize competing deadlines when managing multiple client requirements?", "hints": "Mention agile methodology, stakeholder communication, and milestone tracking.", "ideal_answer": "Prioritize tasks by evaluating business impact and urgency matrix, communicating transparently with stakeholders, and managing sprint backlogs in Agile."},
        {"id": 10, "category": "HR & Cultural", "question": f"Where do you see your technical mastery in {job_title} progressing over the next 3 years?", "hints": "Highlight continuous learning, leadership, and domain expertise.", "ideal_answer": "Aim to progress from core technical execution to lead architect responsibilities, mentoring junior engineers, and driving innovative system designs."}
    ]
    return {"success": True, "job_title": job_title, "questions": fallback_10}


@app.post("/api/ai/live-interview/evaluate")
def evaluate_10_interview_answers(data: LiveInterviewEvalSchema, authorization: Optional[str] = Header(None)):
    """Evaluate candidate answers against AI model answers and calculate exact match percentage."""
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
                        "ideal_answer": "A complete response should explain architectural principles, design patterns, and concrete tools."
                    })
                    continue

                prompt = f"""Compare the candidate's answer with the ideal technical model answer for '{data.job_title}':

Question: "{ans.question}"
Candidate Answer: "{ans.user_answer}"

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

    # Fallback Evaluation Engine with Match %
    for idx, ans in enumerate(data.answers, 1):
        words = len(ans.user_answer.strip().split())
        score = min(95, max(30, words * 4)) if words > 0 else 0
        total_score_sum += score
        evaluations.append({
            "question_num": idx,
            "question": ans.question,
            "user_answer": ans.user_answer if ans.user_answer.strip() else "No answer provided.",
            "match_percentage": score,
            "feedback": "Strong answer alignment!" if words >= 15 else "Answer is somewhat brief. Expand with specific technical tools.",
            "ideal_answer": f"Ideal response for {ans.question[:40]}... includes core data structures, error handling, and performance metrics."
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


@app.get("/api/notes/download/{skill_name}")
def download_skill_notes(
    skill_name: str, 
    domain: Optional[str] = Query("General Tech & Engineering"),
    authorization: Optional[str] = Header(None)
):
    user = get_current_user(authorization)
    if not user or not user.get("is_pro", False):
        raise HTTPException(
            status_code=403, 
            detail="⚠️ OpenAI PDF Study Notes are a Pro Feature (₹150/month). Please upgrade to download!"
        )

    try:
        pdf_bytes = generate_notes_pdf(skill_name, domain=domain)
        safe_filename = skill_name.replace(" ", "_").replace("/", "_") + "_OpenAI_Study_Notes.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
        )
    except Exception as e:
        logger.error(f"Error generating PDF notes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF notes: {str(e)}")


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

    allowed = UserManager.check_and_increment_scan(user_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="⚠️ Free Tier Limit Reached (3 Scans / Day). Upgrade to Pro Plan for ₹150/month for UNLIMITED scans and AI Features!"
        )

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
