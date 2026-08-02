from typing import Dict, List, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Comprehensive Knowledge Base for Missing Skills
SKILL_KNOWLEDGE_BASE = {
    "PyTorch": {
        "video_url": "https://www.youtube.com/results?search_query=pytorch+full+course+for+beginners",
        "video_title": "PyTorch Deep Learning Masterclass (Full Course)",
        "notes_title": "PyTorch Tensor Operations & Neural Networks Cheat Sheet",
        "notes_summary": "Complete guide on torch.Tensor, Autograd, nn.Module, Optimizer loops, and CUDA GPU acceleration.",
        "project_idea": "Build an Image Classification model using PyTorch ResNet transfer learning."
    },
    "TensorFlow": {
        "video_url": "https://www.youtube.com/results?search_query=tensorflow+2.0+complete+course",
        "video_title": "TensorFlow & Keras Neural Network Tutorial",
        "notes_title": "TensorFlow Keras Sequential & Functional API Notes",
        "notes_summary": "Covers Keras layers, callbacks, model saving, and TensorBoard visualization.",
        "project_idea": "Train a Sentiment Analysis Neural Network with TensorFlow Keras."
    },
    "Docker": {
        "video_url": "https://www.youtube.com/results?search_query=docker+for+beginners+full+course",
        "video_title": "Docker & Containerization Crash Course",
        "notes_title": "Docker Commands & Dockerfile Best Practices Cheat Sheet",
        "notes_summary": "Covers docker build, run, compose, volumes, multi-stage builds, and networking.",
        "project_idea": "Containerize a Python FastAPI server and publish image to Docker Hub."
    },
    "FastAPI": {
        "video_url": "https://www.youtube.com/results?search_query=fastapi+full+course",
        "video_title": "FastAPI RESTful API Backend Masterclass",
        "notes_title": "FastAPI Pydantic Schemas & Async Endpoints Notes",
        "notes_summary": "Covers path parameters, dependency injection, Pydantic validation, and OAuth2 security.",
        "project_idea": "Build an asynchronous REST API serving ML predictions."
    },
    "SQL": {
        "video_url": "https://www.youtube.com/results?search_query=advanced+sql+for+data+analysis",
        "video_title": "Advanced SQL & Database Analytics Masterclass",
        "notes_title": "Advanced SQL Queries & Window Functions Cheat Sheet",
        "notes_summary": "Covers ROW_NUMBER(), DENSE_RANK(), CTEs, INNER/LEFT JOINs, subqueries, and indexing.",
        "project_idea": "Analyze e-commerce transaction logs using SQL Window functions."
    }
}


# Multi-Stream Benchmark Job Profiles with Feature 3: Placement Salary & Market Demand Analytics
JOB_PROFILES = {
    "Demo Specialist / Sales Representative": {
        "title": "Demo Specialist / Sales Representative",
        "domain": "Sales, Retail & Product Promotion",
        "stream": "Sales & Business",
        "fresher_salary": "₹4.0 LPA – ₹8.5 LPA",
        "experienced_salary": "₹9.0 LPA – ₹18.0 LPA",
        "hiring_companies": ["Samsung", "Apple", "Maple Leaf", "Reliance Retail", "Unilever", "Summit Peak"],
        "market_demand": "📈 Rapidly Growing (Retail & Consumer Tech)",
        "description": "Engages customers, delivers compelling live product demonstrations, drives retail sales, and manages promotional events and brand experiences.",
        "full_text": "Demo Specialist Sales Representative Product Demonstration Customer Engagement Sales Techniques Product Knowledge Presentation Skills Retail Sales Customer Experience Event Planning Promotional Materials Merchandising Inventory Management Sales Promotion Customer Service Lead Generation Negotiation Sales Reporting Key Account Management Direct Sales",
        "core_skills": ["Product Demonstration", "Customer Engagement", "Sales Techniques", "Product Knowledge", "Presentation Skills", "Communication"],
        "preferred_skills": ["Event Planning", "Promotional Materials", "Logistics", "Marketing", "Retail Sales", "Sales Reporting", "Customer Service"],
        "learning_resources": {
            "Sales Analytics": "Master CRM software (Salesforce, HubSpot) and retail sales tracking analytics.",
            "Digital Marketing": "Learn social media product promotion and digital lead generation techniques."
        }
    },
    "AI / Machine Learning Engineer": {
        "title": "AI / Machine Learning Engineer",
        "domain": "Artificial Intelligence & Data Science",
        "stream": "Tech & Engineering",
        "fresher_salary": "₹8.0 LPA – ₹22.0 LPA",
        "experienced_salary": "₹22.0 LPA – ₹45.0+ LPA",
        "hiring_companies": ["Google", "Amazon", "Microsoft", "NVIDIA", "TCS AI Lab", "High-Growth AI Startups"],
        "market_demand": "🔥 Extremely High Demand (Hot Tech Role)",
        "description": "Designs, builds, and deploys machine learning and deep learning models for predictive automation and artificial intelligence applications.",
        "full_text": "AI Machine Learning Engineer Artificial Intelligence Data Science Python Machine Learning Deep Learning TensorFlow PyTorch Scikit-Learn Pandas NumPy Git NLP Computer Vision Docker FastAPI SQL Transformers AWS MLOps Neural Networks Fine-tuning RAG LLM",
        "core_skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-Learn", "Pandas", "NumPy", "Git"],
        "preferred_skills": ["NLP", "Computer Vision", "Docker", "FastAPI", "SQL", "Transformers", "AWS", "MLOps"],
        "learning_resources": {
            "Deep Learning": "Master PyTorch/TensorFlow & Neural Network architectures (CNN, RNN, Transformers).",
            "MLOps": "Learn Docker containerization and FastAPI model deployment."
        }
    },
    "Data Scientist": {
        "title": "Data Scientist",
        "domain": "Artificial Intelligence & Data Science",
        "stream": "Tech & Engineering",
        "fresher_salary": "₹7.5 LPA – ₹18.0 LPA",
        "experienced_salary": "₹18.0 LPA – ₹38.0 LPA",
        "hiring_companies": ["Walmart Labs", "Flipkart", "Fractal Analytics", "Mu Sigma", "Deloitte", "Accenture"],
        "market_demand": "🔥 High Demand",
        "description": "Analyzes complex datasets to extract actionable business insights, statistical models, and predictive algorithms.",
        "full_text": "Data Scientist Artificial Intelligence Data Science Python SQL Statistics Machine Learning Pandas NumPy Matplotlib Seaborn Scikit-Learn R Tableau Power BI Spark BigQuery AB Testing Feature Engineering Data Analytics Predictive Modeling",
        "core_skills": ["Python", "SQL", "Statistics", "Machine Learning", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Scikit-Learn"],
        "preferred_skills": ["R", "Tableau", "Power BI", "Spark", "BigQuery", "A/B Testing", "Feature Engineering"],
        "learning_resources": {
            "SQL": "Practice advanced SQL queries (Window functions, CTEs, Aggregations).",
            "Visualization": "Build interactive dashboards using Tableau or Power BI."
        }
    },
    "Data Analyst": {
        "title": "Data Analyst",
        "domain": "Business Intelligence & Data Analytics",
        "stream": "Tech & Analytics",
        "fresher_salary": "₹5.0 LPA – ₹12.0 LPA",
        "experienced_salary": "₹12.0 LPA – ₹24.0 LPA",
        "hiring_companies": ["EY", "PwC", "KPMG", "McKinsey", "Swiggy", "Zomato", "Capgemini"],
        "market_demand": "📈 High Placement Volume",
        "description": "Transforms raw business data into executive insights using SQL, statistical modeling, and interactive BI visual dashboards.",
        "full_text": "Data Analyst Business Intelligence Data Analytics SQL Excel Python Power BI Tableau Pandas Statistics Data Visualization R BigQuery Snowflake ETL Communication Problem Solving Reporting KPI Metrics",
        "core_skills": ["SQL", "Excel", "Python", "Power BI", "Tableau", "Pandas", "Statistics", "Data Visualization"],
        "preferred_skills": ["R", "BigQuery", "Snowflake", "ETL", "Communication", "Problem Solving"],
        "learning_resources": {
            "Power BI": "Learn DAX functions and report dashboard publishing.",
            "Advanced Excel": "Master Pivot tables, VLOOKUP/XLOOKUP, and dynamic charting."
        }
    },
    "Full-Stack Web Developer": {
        "title": "Full-Stack Web Developer",
        "domain": "Software Development",
        "stream": "Tech & Engineering",
        "fresher_salary": "₹6.0 LPA – ₹16.0 LPA",
        "experienced_salary": "₹16.0 LPA – ₹32.0 LPA",
        "hiring_companies": ["Meta", "Uber", "Zoho", "Freshworks", "Infosys", "Wipro", "Product Startups"],
        "market_demand": "🔥 High Global Demand",
        "description": "Develops end-to-end web applications, handling front-end user experience and back-end server microservices.",
        "full_text": "Full-Stack Web Developer Software Development JavaScript HTML CSS React Node.js Express REST API SQL Git TypeScript Next.js MongoDB FastAPI Docker Tailwind PostgreSQL Microservices Serverless Frontend Backend",
        "core_skills": ["JavaScript", "HTML", "CSS", "React", "Node.js", "Express", "REST API", "SQL", "Git"],
        "preferred_skills": ["TypeScript", "Next.js", "MongoDB", "FastAPI", "Docker", "Tailwind", "PostgreSQL"],
        "learning_resources": {
            "React": "Master React state management, hooks, and modern UI components."
        }
    },
    "Financial Analyst": {
        "title": "Financial Analyst",
        "domain": "Finance, Banking & Investments",
        "stream": "Finance & Commerce",
        "fresher_salary": "₹6.5 LPA – ₹15.0 LPA",
        "experienced_salary": "₹15.0 LPA – ₹30.0 LPA",
        "hiring_companies": ["Goldman Sachs", "J.P. Morgan", "Morgan Stanley", "HDFC Bank", "ICICI Securities"],
        "market_demand": "🎯 High Value Finance Role",
        "description": "Evaluates financial data, builds financial models, prepares valuation reports, and guides corporate investment decisions.",
        "full_text": "Financial Analyst Corporate Finance Financial Modeling Valuation Accounting Excel Financial Reporting Tally SAP SQL Power BI Statistics Risk Analysis Taxation Financial Statement Balance Sheet Cash Flow",
        "core_skills": ["Financial Analysis", "Financial Modeling", "Excel", "Accounting", "Valuation", "Corporate Finance", "Financial Reporting"],
        "preferred_skills": ["Tally", "SAP", "SQL", "Power BI", "Statistics", "Risk Analysis", "Taxation"],
        "learning_resources": {
            "Financial Modeling": "Practice 3-statement financial modeling and discounted cash flow (DCF) valuation."
        }
    }
}


class JobMatcher:
    """
    Hybrid AI Job Matching Engine with Placement Market Analytics.
    """

    @classmethod
    def calculate_sentence_embedding_similarity(cls, resume_raw_text: str, job_full_text: str) -> float:
        if not resume_raw_text or not job_full_text:
            return 0.0
        try:
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform([resume_raw_text, job_full_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return round(float(similarity) * 100, 1)
        except Exception:
            return 0.0

    @classmethod
    def calculate_match(cls, candidate_skills: List[str], target_job_key: str = None, raw_resume_text: str = "") -> Dict[str, Any]:
        cand_skills_lower = set([s.lower() for s in candidate_skills])
        results = []
        target_analysis = None

        for key, profile in JOB_PROFILES.items():
            core_set = set([s.lower() for s in profile["core_skills"]])
            pref_set = set([s.lower() for s in profile["preferred_skills"]])
            all_req_set = core_set.union(pref_set)

            matched_core = cand_skills_lower.intersection(core_set)
            matched_pref = cand_skills_lower.intersection(pref_set)
            matched_all = cand_skills_lower.intersection(all_req_set)

            missing_core = core_set - cand_skills_lower
            missing_pref = pref_set - cand_skills_lower

            core_score = (len(matched_core) / len(core_set) * 70) if core_set else 0
            pref_score = (len(matched_pref) / len(pref_set) * 30) if pref_set else 0
            keyword_score = round(core_score + pref_score, 1)

            job_full_text = profile.get("full_text", " ".join(profile["core_skills"] + profile["preferred_skills"]))
            if raw_resume_text:
                embedding_score = cls.calculate_sentence_embedding_similarity(raw_resume_text, job_full_text)
            else:
                embedding_score = keyword_score

            if keyword_score > 0 and embedding_score > 0:
                hybrid_score = round((keyword_score * 0.6) + (embedding_score * 0.4), 1)
            elif keyword_score > 0:
                hybrid_score = keyword_score
            else:
                hybrid_score = round(embedding_score * 0.5, 1)

            matched_skills_formatted = [cls.format_skill_name(s) for s in matched_all]
            missing_high_priority = [cls.format_skill_name(s) for s in missing_core]
            missing_medium_priority = [cls.format_skill_name(s) for s in missing_pref]

            upskill_tips = []
            for missing in missing_high_priority:
                kb_resource = SKILL_KNOWLEDGE_BASE.get(missing, None)
                if kb_resource:
                    upskill_tips.append({
                        "skill": missing,
                        "suggestion": profile.get("learning_resources", {}).get(missing, f"Master core principles of {missing}."),
                        "video_url": kb_resource["video_url"],
                        "video_title": kb_resource["video_title"],
                        "notes_title": kb_resource["notes_title"],
                        "notes_summary": kb_resource["notes_summary"],
                        "project_idea": kb_resource["project_idea"]
                    })
                else:
                    upskill_tips.append({
                        "skill": missing,
                        "suggestion": profile.get("learning_resources", {}).get(missing, f"Build a practical project or course certification demonstrating competency in {missing}."),
                        "video_url": f"https://www.youtube.com/results?search_query={missing.lower()}+tutorial+full+course",
                        "video_title": f"{missing} Full Course & Masterclass",
                        "notes_title": f"{missing} Core Cheat Sheet & Notes",
                        "notes_summary": f"Comprehensive reference notes and code snippets for {missing}.",
                        "project_idea": f"Build a portfolio project demonstrating hands-on proficiency in {missing}."
                    })

            analysis = {
                "job_key": key,
                "title": profile["title"],
                "domain": profile["domain"],
                "stream": profile["stream"],
                "fresher_salary": profile.get("fresher_salary", "₹5.0 LPA – ₹12.0 LPA"),
                "experienced_salary": profile.get("experienced_salary", "₹12.0 LPA – ₹28.0 LPA"),
                "hiring_companies": profile.get("hiring_companies", ["TCS", "Infosys", "Wipro", "Accenture", "Startups"]),
                "market_demand": profile.get("market_demand", "🔥 High Demand"),
                "description": profile["description"],
                "match_percentage": hybrid_score,
                "keyword_match_score": keyword_score,
                "semantic_embedding_score": embedding_score,
                "matched_skills": matched_skills_formatted,
                "matched_count": len(matched_skills_formatted),
                "missing_skills": {
                    "high_priority": missing_high_priority,
                    "medium_priority": missing_medium_priority,
                    "total_missing": len(missing_high_priority) + len(missing_medium_priority)
                },
                "total_required_skills": len(all_req_set),
                "upskill_recommendations": upskill_tips
            }

            results.append(analysis)

            if target_job_key and (key.lower() == target_job_key.lower() or profile["title"].lower() == target_job_key.lower()):
                target_analysis = analysis

        results.sort(key=lambda x: x["match_percentage"], reverse=True)

        if not target_analysis and results:
            target_analysis = results[0]

        return {
            "top_matching_job": results[0]["title"],
            "top_match_percentage": results[0]["match_percentage"],
            "target_job_analysis": target_analysis,
            "all_job_recommendations": results
        }

    @staticmethod
    def format_skill_name(skill: str) -> str:
        upper_skills = {
            "sql", "nosql", "nlp", "ai", "ml", "cv", "api", "rest api", "html", "css", "aws", "gcp",
            "etl", "llm", "rag", "cnn", "rnn", "lstm", "bert", "gpt", "oop", "sdlc", "ci/cd",
            "seo", "sem", "crm", "gst", "sap", "hris", "pmp", "ui/ux", "pos", "b2b", "b2c"
        }
        if skill.lower() in upper_skills:
            return skill.upper()
        return skill.title()
