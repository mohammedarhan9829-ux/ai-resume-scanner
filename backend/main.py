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
            prompt = f"""Generate EXACTLY 10 DIRECT, PRACTICAL, HIGHLY FIELD-SPECIFIC placement interview questions for a candidate targeting the role '{job_title}' in the domain of '{domain}'.

CRITICAL INSTRUCTIONS:
1. Do NOT use generic template questions (e.g. do NOT ask "explain architecture of {job_title}").
2. Ask DIRECT, PRACTICAL questions that directly test day-to-day concepts, tools, formulas, or syntax in '{job_title}' (e.g., if Python/Data: ask SQL joins, pandas, functions; if Finance: ask NPV/IRR, financial statements; if Healthcare: ask patient care protocols; if Marketing/HR: ask CAC/LTV, recruitment metrics; if Engineering/Design: ask stress testing, CAD, user research).
3. Include 7 direct technical/functional questions, 2 real-world scenario questions, and 1 HR/career vision question.
4. Provide concise practical hints and complete ideal model answers for each.

Return ONLY a valid JSON list of 10 objects: [{"id": 1, "category": "Technical/Scenario/HR", "question": "...", "hints": "...", "ideal_answer": "..."}]"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=1500
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

    # Domain-Aware Direct Field Fallback Question Suites
    domain_lower = (domain + " " + job_title).lower()
    
    if any(k in domain_lower for k in ["data", "analyst", "science", "python", "ai", "machine learning"]):
        fallback_10 = [
            {"id": 1, "category": "Technical Core", "question": f"What is the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN in SQL?", "hints": "Focus on matching rows vs non-matching null values.", "ideal_answer": "INNER JOIN returns only matching rows from both tables. LEFT JOIN returns all rows from left table plus matching rows from right. FULL OUTER JOIN returns all rows when there is a match in either left or right table."},
            {"id": 2, "category": "Technical Core", "question": f"How do you handle missing or NULL values in a dataset using Python Pandas?", "hints": "Mention dropna(), fillna(), and imputation methods.", "ideal_answer": "Missing values are handled by dropping rows (dropna()), imputing with mean/median/mode (fillna()), or using forward/backward fill algorithms depending on distribution."},
            {"id": 3, "category": "Technical Core", "question": f"Explain overfitting vs underfitting in machine learning models and how to prevent them.", "hints": "Discuss model complexity, bias-variance tradeoff, cross-validation.", "ideal_answer": "Overfitting happens when a model learns noise in training data (high variance, low bias). Underfitting happens when a model is too simple (high bias). Prevent overfitting using regularization (L1/L2), cross-validation, and pruning."},
            {"id": 4, "category": "Technical Core", "question": f"What is the difference between SQL GROUP BY and HAVING clauses?", "hints": "WHERE filters before grouping, HAVING filters after grouping.", "ideal_answer": "WHERE filters individual rows before aggregation occurs. HAVING filters aggregated group results after GROUP BY is applied."},
            {"id": 5, "category": "Technical Core", "question": f"What is the difference between supervised and unsupervised machine learning?", "hints": "Labeled target variables vs unlabeled cluster patterns.", "ideal_answer": "Supervised learning uses labeled target data to train classification/regression models. Unsupervised learning finds hidden patterns/clusters in unlabeled data without target outputs."},
            {"id": 6, "category": "Technical Core", "question": f"How do you calculate metrics like Precision, Recall, and F1-Score?", "hints": "True Positives, False Positives, False Negatives formulas.", "ideal_answer": "Precision = TP / (TP + FP) measures accuracy of positive predictions. Recall = TP / (TP + FN) measures proportion of actual positives captured. F1-Score is the harmonic mean of Precision and Recall."},
            {"id": 7, "category": "Technical Core", "question": f"Which Python libraries do you use for data analysis and visualization?", "hints": "Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn.", "ideal_answer": "NumPy for numerical arrays, Pandas for DataFrame manipulation, Matplotlib/Seaborn for charts, and Scikit-learn for machine learning modeling."},
            {"id": 8, "category": "Scenario", "question": f"Scenario: Your production dashboard metrics dropped by 20% overnight. How do you investigate?", "hints": "Check data pipeline health, source APIs, outliers, and system logs.", "ideal_answer": "First verify data pipeline ingestion logs to check for failed ETL jobs. Then inspect null counts, check for schema changes in upstream APIs, and segment data by region/device to isolate the anomaly."},
            {"id": 9, "category": "Scenario", "question": f"Scenario: A stakeholder requests insights from noisy data with conflicting formats. How do you clean it?", "hints": "Data profiling, normalization, Regex parsing, data validation.", "ideal_answer": "Profile the dataset to audit inconsistencies, apply Regex for string cleaning, standardize date formats, handle duplicate records, and document transformations in a reproducible script."},
            {"id": 10, "category": "HR & Career", "question": f"Why do you want to specialize as a {job_title} and how do you stay updated with industry developments?", "hints": "Continuous learning, tech blogs, Kaggle, GitHub projects.", "ideal_answer": "I am passionate about solving real business problems with data-driven insights. I stay updated by analyzing Kaggle datasets, reading tech research, and building open-source projects."}
        ]
    elif any(k in domain_lower for k in ["finan", "account", "tax", "audit", "banking", "commerce"]):
        fallback_10 = [
            {"id": 1, "category": "Technical Core", "question": f"What are the 3 main financial statements and how do they link together?", "hints": "Income Statement, Balance Sheet, Cash Flow Statement.", "ideal_answer": "Net Income from Income Statement flows into Retained Earnings on the Balance Sheet and starts the Cash Flow Statement. Cash balance from Cash Flow updates Cash on the Balance Sheet."},
            {"id": 2, "category": "Technical Core", "question": f"What is the difference between Net Present Value (NPV) and Internal Rate of Return (IRR)?", "hints": "Time value of money, discount rates, capital budgeting.", "ideal_answer": "NPV is the total present value of future cash flows minus initial investment. IRR is the discount rate that makes NPV equal to zero."},
            {"id": 3, "category": "Technical Core", "question": f"How do you calculate Working Capital, and why is it critical for liquidity?", "hints": "Current Assets minus Current Liabilities.", "ideal_answer": "Working Capital = Current Assets - Current Liabilities. It measures short-term financial health and operational efficiency to meet immediate debt obligations."},
            {"id": 4, "category": "Technical Core", "question": f"What is the difference between EBITDA and Net Income?", "hints": "Operating performance before interest, tax, depreciation, amortization.", "ideal_answer": "EBITDA measures pure operational profitability before non-operating expenses (interest, taxes, depreciation, amortization). Net Income is final profit after all expenses."},
            {"id": 5, "category": "Technical Core", "question": f"Explain Variance Analysis in financial budgeting.", "hints": "Comparing actual revenue/expenses vs budgeted estimates.", "ideal_answer": "Variance Analysis evaluates differences between planned financial budget figures and actual accounting figures to identify operational efficiencies or cost overruns."},
            {"id": 6, "category": "Technical Core", "question": f"What Excel functions do you master for financial modeling?", "hints": "VLOOKUP/XLOOKUP, INDEX/MATCH, NPV, IRR, PMT, Pivot Tables.", "ideal_answer": "Advanced modeling utilizes XLOOKUP and INDEX/MATCH for dynamic data retrieval, Pivot Tables for aggregation, and financial functions like NPV, IRR, and PMT for valuation."},
            {"id": 7, "category": "Technical Core", "question": f"How do you calculate Break-Even Point in units and revenue?", "hints": "Fixed Costs / (Price - Variable Cost per unit).", "ideal_answer": "Break-Even Units = Fixed Costs / (Selling Price per Unit - Variable Cost per Unit). Break-Even Revenue = Break-Even Units x Selling Price per Unit."},
            {"id": 8, "category": "Scenario", "question": f"Scenario: A company's revenue increased by 15% but net cash flow decreased. What caused this?", "hints": "Accounts receivable growth, delayed collections, inventory buildup.", "ideal_answer": "Uncollected credit sales (increased Accounts Receivable), excess inventory purchases, or debt repayments can increase top-line revenue without generating immediate cash inflows."},
            {"id": 9, "category": "Scenario", "question": f"Scenario: You spot a financial discrepancy in quarterly reporting. How do you report it?", "hints": "Audit trail, re-reconciling accounts, notifying senior finance manager.", "ideal_answer": "Re-verify primary journal entries and ledger reconciliations to trace the error source, document the variance, and report findings to the Lead Financial Controller with corrective entries."},
            {"id": 10, "category": "HR & Career", "question": f"Why are you targeting a career as a {job_title}?", "hints": "Financial acumen, analytical problem-solving, strategic planning.", "ideal_answer": "I thrive on analyzing financial metrics to guide strategic decision-making, optimizing capital allocation, and driving sustainable business growth."}
        ]
    elif any(k in domain_lower for k in ["market", "sales", "hr", "human", "recruit", "business"]):
        fallback_10 = [
            {"id": 1, "category": "Technical Core", "question": f"What is the difference between Customer Acquisition Cost (CAC) and Lifetime Value (LTV)?", "hints": "Cost to acquire a customer vs total revenue earned from customer.", "ideal_answer": "CAC is total marketing/sales spend divided by new customers acquired. LTV is total revenue a customer generates throughout their relationship. A healthy ratio is LTV >= 3x CAC."},
            {"id": 2, "category": "Technical Core", "question": f"How do you calculate Click-Through Rate (CTR) and Conversion Rate?", "hints": "Clicks/Impressions vs Conversions/Clicks formulas.", "ideal_answer": "CTR = (Total Clicks / Total Impressions) x 100%. Conversion Rate = (Total Conversions / Total Clicks) x 100%."},
            {"id": 3, "category": "Technical Core", "question": f"What are the main stages of a B2B Sales / Recruitment Funnel?", "hints": "Awareness, Interest/Sourcing, Consideration/Interview, Conversion/Offer.", "ideal_answer": "Prospecting/Sourcing -> Qualification -> Demo/Interview Evaluation -> Proposal/Offer -> Closed Won/Hired."},
            {"id": 4, "category": "Technical Core", "question": f"Explain SEO On-Page vs Off-Page optimization techniques.", "hints": "Keywords, meta tags, headers vs backlinks, domain authority.", "ideal_answer": "On-Page SEO optimizes content, meta tags, headers, and internal linking. Off-Page SEO builds domain authority via high-quality backlinks and brand mentions."},
            {"id": 5, "category": "Technical Core", "question": f"What strategies do you use for candidate sourcing or lead generation?", "hints": "LinkedIn Recruiter/Sales Navigator, outbound campaigns, content marketing.", "ideal_answer": "Multi-channel sourcing via LinkedIn, targeted cold email outreach, inbound content lead magnets, and referral networks."},
            {"id": 6, "category": "Technical Core", "question": f"What CRM or Marketing automation platforms do you use?", "hints": "HubSpot, Salesforce, Google Analytics, Mailchimp.", "ideal_answer": "Salesforce/HubSpot for pipeline tracking, Google Analytics for traffic insights, and Mailchimp for automated drip marketing."},
            {"id": 7, "category": "Technical Core", "question": f"How do you perform A/B testing on ad creatives or landing pages?", "hints": "Isolating one variable (headline, CTA, image) with equal audience split.", "ideal_answer": "Change a single variable (e.g. CTA text or hero image), split audience randomly, run until statistically significant sample size, and choose higher converting variant."},
            {"id": 8, "category": "Scenario", "question": f"Scenario: An ad campaign has high clicks but zero conversions. How do you fix it?", "hints": "Check landing page relevance, slow load speed, broken CTA form.", "ideal_answer": "Audit landing page load time, ensure offer matches ad headline, check mobile responsiveness, and test sign-up form submission to fix friction points."},
            {"id": 9, "category": "Scenario", "question": f"Scenario: How do you handle price or salary negotiation objections from clients/candidates?", "hints": "Focus on value proposition, total benefits package, ROI.", "ideal_answer": "Listen actively, reframe objections around long-term ROI and core value drivers, and present flexible structure options without compromising quality."},
            {"id": 10, "category": "HR & Career", "question": f"What drives your success in a {job_title} role?", "hints": "Relationship building, data-driven strategy, resilience.", "ideal_answer": "Combining data-driven strategy with authentic relationship building, maintaining resilience, and continuously delivering measurable growth results."}
        ]
    elif any(k in domain_lower for k in ["health", "nurse", "medical", "pharm", "clinic", "doctor"]):
        fallback_10 = [
            {"id": 1, "category": "Technical Core", "question": f"What are the 5 Rights of Medication Administration in clinical care?", "hints": "Right Patient, Right Drug, Right Dose, Right Route, Right Time.", "ideal_answer": "1. Right Patient 2. Right Medication 3. Right Dose 4. Right Route 5. Right Time."},
            {"id": 2, "category": "Technical Core", "question": f"How do you perform triage and prioritize patient care in emergency settings?", "hints": "Emergency Severity Index (ESI), Airway/Breathing/Circulation (ABCs).", "ideal_answer": "Prioritize based on life-threatening status (Airway, Breathing, Circulation) using standardized triage scales (ESI 1 to 5) to treat critical patients immediately."},
            {"id": 3, "category": "Technical Core", "question": f"What is the difference between sterile and aseptic techniques?", "hints": "Elimination of ALL microorganisms vs preventing infection transfer.", "ideal_answer": "Sterile technique eliminates ALL microorganisms from instruments/fields. Aseptic technique includes procedures used to prevent contamination and pathogen transfer."},
            {"id": 4, "category": "Technical Core", "question": f"How do you monitor vital signs and identify early signs of patient deterioration?", "hints": "BP, Heart Rate, SpO2, Resp Rate, NEWS score.", "ideal_answer": "Regular monitoring of Blood Pressure, Pulse, Oxygen Saturation, and Respiratory Rate, tracking National Early Warning Scores (NEWS) to detect sepsis or hypoxia early."},
            {"id": 5, "category": "Technical Core", "question": f"What steps ensure HIPAA compliance and patient data confidentiality?", "hints": "Secure EHR systems, no public disclosure, encrypted communications.", "ideal_answer": "Access Electronic Health Records (EHR) on encrypted terminals only, never discuss patient info in non-secure areas, and follow strict consent protocols."},
            {"id": 6, "category": "Technical Core", "question": f"What are the standard hospital infection control protocols?", "hints": "Hand hygiene, PPE, isolation precautions, biohazard disposal.", "ideal_answer": "Strict hand washing before/after contact, proper PPE donning/doffing, isolation protocols (contact/droplet/airborne), and safe disposal of sharps and biohazard waste."},
            {"id": 7, "category": "Technical Core", "question": f"How do you handle difficult patient communication or breaking bad news?", "hints": "SPIKES protocol, empathy, active listening, clear explanations.", "ideal_answer": "Use empathetic active listening (SPIKES framework), provide information clearly without medical jargon, allow space for questions, and offer support resources."},
            {"id": 8, "category": "Scenario", "question": f"Scenario: A patient exhibits signs of an anaphylactic allergic reaction. What immediate steps do you take?", "hints": "Stop causative agent, call rapid response, administer epinephrine/oxygen.", "ideal_answer": "Immediately stop offending medication/IV, assess airway/breathing, call rapid response, elevate legs, administer prescribed Epinephrine, and give high-flow oxygen."},
            {"id": 9, "category": "Scenario", "question": f"Scenario: A busy shift is understaffed. How do you maintain patient safety?", "hints": "Focus on high-risk clinical tasks, delegate appropriately, communicate with charge nurse.", "ideal_answer": "Re-prioritize critical care treatments and medication passes, delegate non-clinical tasks appropriately, inform charge nurse, and maintain open safety communication."},
            {"id": 10, "category": "HR & Career", "question": f"Why did you choose a clinical career as a {job_title}?", "hints": "Patient advocacy, clinical excellence, compassionate care.", "ideal_answer": "Dedicated to delivering high-quality, compassionate patient care, continuously updating clinical skills, and advocating for patient health outcomes."}
        ]
    else: # Software / Web / Engineering / General Default
        fallback_10 = [
            {"id": 1, "category": "Technical Core", "question": f"What is the difference between REST APIs and GraphQL APIs?", "hints": "Fixed endpoints/over-fetching vs single endpoint/flexible query schemas.", "ideal_answer": "REST relies on fixed endpoints per resource (can cause over-fetching or under-fetching). GraphQL uses a single endpoint allowing clients to request exact fields needed."},
            {"id": 2, "category": "Technical Core", "question": f"How do database indexes speed up query performance, and what is the trade-off?", "hints": "B-Tree structures speed up SELECTs but slow down INSERT/UPDATE/DELETE.", "ideal_answer": "Indexes create data lookup trees (like B-Trees) allowing logarithmic O(log N) search times instead of full table scans. Trade-off: increases disk space and slows down write operations."},
            {"id": 3, "category": "Technical Core", "question": f"Explain git rebase vs git merge, and when to use each.", "hints": "Linear commit history vs preserving actual chronological branch merges.", "ideal_answer": "Git merge creates a new merge commit combining history. Git rebase rewrites feature branch commits onto top of main for a clean linear history. Avoid rebasing public shared branches."},
            {"id": 4, "category": "Technical Core", "question": f"What is CORS (Cross-Origin Resource Sharing) and how do you resolve CORS errors?", "hints": "Browser security blocking requests across different origins/domains.", "ideal_answer": "CORS is a browser security mechanism restricting web pages from making API requests to a different domain. Resolved by configuring Access-Control-Allow-Origin headers on backend server."},
            {"id": 5, "category": "Technical Core", "question": f"Explain Docker containerization vs Virtual Machines (VMs).", "hints": "Shared host OS kernel vs full guest operating system hypervisor.", "ideal_answer": "Docker containers share the host OS kernel and package application code with dependencies (lightweight, fast start). VMs run full guest OS over hypervisors (heavier, higher overhead)."},
            {"id": 6, "category": "Technical Core", "question": f"How do you implement input validation and error handling in production code?", "hints": "Schema validation libraries, explicit try-except, HTTP status codes.", "ideal_answer": "Enforce strict schema validation (e.g. Pydantic), sanitize inputs, catch specific exceptions, log structured errors, and return clear HTTP status codes."},
            {"id": 7, "category": "Technical Core", "question": f"What is the difference between synchronous and asynchronous code execution?", "hints": "Blocking single-thread execution vs non-blocking event loops.", "ideal_answer": "Synchronous code blocks thread execution until task completes. Asynchronous code yields execution to event loop during I/O wait, allowing concurrent processing."},
            {"id": 8, "category": "Scenario", "question": f"Scenario: A web API returns 504 Gateway Timeout under heavy user traffic. How do you troubleshoot?", "hints": "Inspect database connection pools, slow queries, caching, load balancing.", "ideal_answer": "Check server CPU/memory metrics, profile slow SQL queries, add Redis caching, optimize connection pool limits, and scale worker processes behind load balancer."},
            {"id": 9, "category": "Scenario", "question": f"Scenario: A critical bug is found in production right after deployment. What is your rollback procedure?", "hints": "Roll back to previous release version tag, isolate bug in staging, hotfix.", "ideal_answer": "Immediately roll back deployment to previous stable Git tag/container image, verify system stability, isolate bug with unit tests in staging, and release tested hotfix."},
            {"id": 10, "category": "HR & Career", "question": f"Why do you want to excel as a {job_title} in our engineering team?", "hints": "Technical passion, problem solving, continuous learning.", "ideal_answer": "Driven by writing scalable code, building reliable architectures, and solving high-impact problems while continuously expanding technical expertise."}
        ]

    return {"success": True, "job_title": job_title, "questions": fallback_10}


def detect_ai_or_web_copy(text: str) -> tuple[bool, str]:
    """Detect if candidate answer is copied directly from Google AI Overview, ChatGPT, or web search URLs."""
    if not text or not text.strip():
        return False, ""

    txt = text.strip()
    txt_lower = txt.lower()

    # 1. Google AI Overview Header or Hindi/Multi-lingual Overview text
    if "ai overview" in txt_lower or "ai-generated" in txt_lower or "google search" in txt_lower:
        return True, "🚨 Plagiarism Flagged: Answer copied directly from Google AI Overview / Search engine."

    # 2. Web URLs or URL citations like [1] (https://...) or http://
    import re
    if re.search(r'\[\d+\]\s*\(\s*https?://', txt) or re.search(r'https?://[^\s]+\.(com|org|in|net|edu|io)', txt):
        return True, "🚨 Plagiarism Flagged: Web search links or URL citations detected in answer ([1] https://...)."

    # 3. Citation brackets like [1], [2], [3] (2 or more citation numbers)
    citations = re.findall(r'\[\d+\]', txt)
    if len(citations) >= 2:
        return True, "🚨 Plagiarism Flagged: External web search citation markers [1], [2] detected."

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
        return True, "🚨 Plagiarism Flagged: Copied AI generator preamble text detected."

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
