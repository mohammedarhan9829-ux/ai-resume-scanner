import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger("SkillAnalyzer")

# Strong Action Verbs List for ATS Auditing
STRONG_ACTION_VERBS = {
    "engineered", "architected", "developed", "built", "designed", "implemented",
    "accelerated", "boosted", "maximized", "optimized", "spearheaded", "executed",
    "analyzed", "collaborated", "managed", "delivered", "increased", "reduced",
    "automated", "transformed", "directed", "formulated", "launched", "orchestrated"
}

# Universal Multi-Stream Skill Taxonomy
SKILL_TAXONOMY = {
    "Sales, Retail & Product Demonstration": [
        "product demonstration", "product demo", "customer engagement", "sales techniques",
        "product knowledge", "presentation skills", "retail sales", "customer experience",
        "event planning", "promotional materials", "merchandising", "inventory management",
        "sales promotion", "customer service", "lead generation", "negotiation", "sales reporting",
        "key account management", "direct sales", "b2b sales", "b2c sales"
    ],
    "Marketing, Content & Brand Strategy": [
        "marketing", "digital marketing", "seo", "sem", "search engine optimization",
        "social media marketing", "content marketing", "copywriting", "google analytics",
        "meta ads", "facebook ads", "email marketing", "salesforce", "hubspot", "crm",
        "brand strategy", "market research", "public relations", "brand standards"
    ],
    "Programming & Data Science": [
        "python", "r", "c", "c++", "java", "javascript", "typescript", "html", "css", 
        "sql", "nosql", "bash", "shell", "scala", "go", "rust", "php", "ruby", "kotlin", "swift",
        "machine learning", "deep learning", "artificial intelligence", "data science",
        "nlp", "natural language processing", "computer vision", "tensorflow",
        "pytorch", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "matplotlib", "seaborn",
        "power bi", "tableau", "excel", "advanced excel", "spark", "hadoop", "etl"
    ],
    "Web, Cloud & Software Engineering": [
        "react", "react.js", "next.js", "vue", "angular", "node.js", "express",
        "fastapi", "flask", "django", "rest api", "graphql", "tailwind", "bootstrap",
        "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "git", "github", "linux", "jira"
    ],
    "Business & Operations Management": [
        "project management", "agile", "scrum", "business analysis", "strategic planning",
        "risk management", "change management", "operations management", "stakeholder management",
        "vendor management", "budgeting", "cost optimization", "process improvement",
        "logistics", "supply chain", "event coordination"
    ],
    "Finance, Accounting & Banking": [
        "financial analysis", "financial modeling", "accounting", "bookkeeping", "auditing",
        "taxation", "gst", "tally", "sap", "quickbooks", "corporate finance", "valuation",
        "portfolio management", "risk analysis", "financial reporting", "cost accounting"
    ],
    "Human Resources (HR) & Administration": [
        "talent acquisition", "recruitment", "employee engagement", "payroll", "performance management",
        "hr policies", "labor laws", "onboarding", "training & development", "conflict resolution",
        "workforce planning", "hris", "workday", "employee relations"
    ],
    "Design, UI/UX & Creative Arts": [
        "ui/ux design", "graphic design", "figma", "adobe photoshop", "illustrator",
        "indesign", "wireframing", "prototyping", "user research", "video editing",
        "premiere pro", "after effects", "canva", "motion graphics", "3d modeling", "blender"
    ],
    "Healthcare & Life Sciences": [
        "clinical research", "patient care", "healthcare management", "pharmacology",
        "laboratory analysis", "medical writing", "biostatistics", "epidemiology",
        "public health", "diagnostic testing", "gcp guidelines"
    ],
    "Soft Skills & Professional Attributes": [
        "problem solving", "critical thinking", "communication", "teamwork", "leadership",
        "time management", "adaptability", "collaboration", "analytical thinking",
        "interpersonal skills", "service oriented", "sincerity", "stability", "stewardship"
    ]
}


class SkillAnalyzer:
    """Analyze resume text for multi-stream skills, ATS audit scores, contact info, and structural metrics."""

    @classmethod
    def extract_contact_info(cls, text: str) -> Dict[str, Any]:
        """Extract email, phone, and social links."""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'\(?\+?\d{1,3}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}[-.\s]?\d{0,4}'
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+'
        github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+'

        emails = list(set(re.findall(email_pattern, text)))
        phones = list(set(re.findall(phone_pattern, text)))
        valid_phones = [p for p in phones if len(re.sub(r'\D', '', p)) >= 10]

        linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
        github = re.findall(github_pattern, text, re.IGNORECASE)

        return {
            "email": emails[0] if emails else "Not specified",
            "phone": valid_phones[0] if valid_phones else "Not specified",
            "linkedin": linkedin[0] if linkedin else None,
            "github": github[0] if github else None,
        }

    @classmethod
    def extract_skills(cls, text: str) -> Dict[str, Any]:
        """Extract skills across all streams."""
        text_lower = text.lower()
        extracted_by_cat = {}
        all_found_skills = set()

        for category, skills_list in SKILL_TAXONOMY.items():
            category_found = []
            for skill in skills_list:
                escaped_skill = re.escape(skill)
                pattern = r'(?:\b|_)' + escaped_skill + r'(?:\b|_)'
                if re.search(pattern, text_lower):
                    formatted_name = cls.format_skill_name(skill)
                    category_found.append(formatted_name)
                    all_found_skills.add(formatted_name)
            
            if category_found:
                extracted_by_cat[category] = list(set(category_found))

        return {
            "categorized_skills": extracted_by_cat,
            "all_skills": list(all_found_skills),
            "skill_count": len(all_found_skills)
        }

    @classmethod
    def audit_ats_compliance(cls, text: str, contact_info: dict, total_skills: int) -> Dict[str, Any]:
        """Feature 4: Perform ATS Compliance & Health Audit (0-100 Score)."""
        warnings = []
        recommendations = []

        # 1. Contact Score (Max 25)
        contact_score = 0
        if contact_info.get("email") != "Not specified": contact_score += 8
        else: warnings.append("Missing professional email address.")
        
        if contact_info.get("phone") != "Not specified": contact_score += 7
        else: warnings.append("Missing phone contact number.")
        
        if contact_info.get("linkedin"): contact_score += 5
        else: recommendations.append("Add your LinkedIn profile URL to boost ATS trust.")
        
        if contact_info.get("github"): contact_score += 5
        else: recommendations.append("Add GitHub / Portfolio URL to showcase proof of work.")

        # 2. Action Verb Score (Max 25)
        words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
        matched_verbs = words.intersection(STRONG_ACTION_VERBS)
        verb_score = min(25, len(matched_verbs) * 5)
        if len(matched_verbs) < 3:
            warnings.append(f"Only found {len(matched_verbs)} strong action verbs. Use verbs like 'Engineered', 'Optimized', 'Spearheaded'.")

        # 3. Keyword Density Score (Max 25)
        keyword_score = min(25, total_skills * 2.5)
        if total_skills < 6:
            warnings.append(f"Low keyword density ({total_skills} skills detected). Add standard industry skill terms.")

        # 4. Structural Score (Max 25)
        structural_score = 0
        text_lower = text.lower()
        if "education" in text_lower or "academic" in text_lower: structural_score += 7
        else: warnings.append("Missing explicit 'Education' section header.")
        
        if "experience" in text_lower or "work" in text_lower or "project" in text_lower: structural_score += 7
        else: warnings.append("Missing 'Experience' or 'Projects' section header.")
        
        if "skill" in text_lower: structural_score += 6
        if len(text.split()) >= 100: structural_score += 5
        else: warnings.append("Resume text is very short (< 100 words).")

        overall_ats_score = min(100, int(contact_score + verb_score + keyword_score + structural_score))

        return {
            "overall_ats_score": overall_ats_score,
            "contact_score": contact_score,
            "verb_score": verb_score,
            "keyword_score": keyword_score,
            "structural_score": structural_score,
            "action_verbs_count": len(matched_verbs),
            "action_verbs_found": list(matched_verbs),
            "warnings": warnings,
            "recommendations": recommendations
        }

    @staticmethod
    def format_skill_name(skill: str) -> str:
        """Capitalize skill names properly."""
        upper_skills = {
            "sql", "nosql", "nlp", "ai", "ml", "cv", "api", "rest api", "html", "css", "aws", "gcp",
            "etl", "llm", "rag", "cnn", "rnn", "lstm", "bert", "gpt", "oop", "sdlc", "ci/cd",
            "seo", "sem", "crm", "gst", "sap", "hris", "pmp", "ui/ux", "pos", "b2b", "b2c"
        }
        if skill.lower() in upper_skills:
            return skill.upper()
        return skill.title()

    @classmethod
    def detect_experience_years(cls, text: str) -> str:
        """Estimate experience level."""
        exp_pattern = r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)'
        matches = re.findall(exp_pattern, text, re.IGNORECASE)
        if matches:
            years = [int(m) for m in matches if int(m) < 40]
            if years:
                return f"{max(years)}+ Years"

        years_found = [int(y) for y in re.findall(r'\b(20[0-2][0-9])\b', text)]
        if len(years_found) >= 2:
            min_y, max_y = min(years_found), max(years_found)
            diff = max_y - min_y
            if 0 < diff <= 15:
                return f"~{diff} Years (Based on timeline)"

        return "Fresher / Entry-Level (< 1 Year)"

    @classmethod
    def analyze_resume(cls, text: str) -> Dict[str, Any]:
        """Complete resume analysis including Feature 4 ATS Audit."""
        contact_info = cls.extract_contact_info(text)
        skill_res = cls.extract_skills(text)
        exp_level = cls.detect_experience_years(text)
        ats_audit = cls.audit_ats_compliance(text, contact_info, skill_res["skill_count"])

        return {
            "contact_info": contact_info,
            "skills": skill_res["categorized_skills"],
            "all_skills_list": skill_res["all_skills"],
            "total_skills_detected": skill_res["skill_count"],
            "experience_level": exp_level,
            "ats_audit": ats_audit
        }
