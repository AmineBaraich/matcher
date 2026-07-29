import os
import re
import json
import fitz
import google.generativeai as genai
from duckduckgo_search import DDGS
from typing import Dict, List
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        text = ''
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        raise Exception(f'Failed to extract text from PDF: {e}')

def mock_cv_analysis(cv_text: str) -> Dict:
    skills_pattern = '\\b(Python|Java|JavaScript|React|Node\\.js|Django|Flask|SQL|MongoDB|AWS|Docker|Kubernetes|Git|Machine Learning|Data Science|Web Development|DevOps|Cloud|AI|UX|UI|Project Management)\\b'
    skills = list(set(re.findall(skills_pattern, cv_text, re.IGNORECASE)))
    title_pattern = '\\b(Developer|Engineer|Analyst|Manager|Specialist|Consultant|Architect|Scientist|Designer|Coordinator|Administrator)\\b'
    titles = list(set(re.findall(title_pattern, cv_text, re.IGNORECASE)))
    return {'candidate_profile': {'name': 'Name not found', 'email': 'Email not found', 'phone': 'Phone not found', 'summary': 'Analysis based on provided CV text.'}, 'skills_analysis': {'technical_skills': skills if skills else ['General skills identified'], 'soft_skills': ['Communication', 'Teamwork'], 'certifications': [], 'tools_technologies': skills[:5] if skills else ['Common tools']}, 'experience_analysis': {'total_years_experience': 'Years not quantified', 'current_level': 'Level not determined', 'career_progression': 'Progression identified in text', 'key_achievements': ['Achievements mentioned in CV']}, 'job_recommendations': [{'role': title if titles else 'Software Professional', 'match_score': 80, 'reasoning': 'Based on skills found in CV.', 'required_skills': skills[:3] if skills else ['Core skills'], 'salary_range': 'Not specified', 'growth_potential': 'Medium'}], 'cv_improvement_suggestions': [{'area': 'Quantify Achievements', 'issue': 'Lack of metrics', 'suggestion': 'Add numbers and results to experience.', 'priority': 'High'}], 'market_insights': {'industry_trends': 'Relevant skills are in demand.', 'salary_benchmark': 'Varies by role and location.', 'demand_outlook': 'Stable'}}

def analyze_cv_with_gemini(cv_text: str) -> Dict:
    if not GEMINI_API_KEY:
        return mock_cv_analysis(cv_text)
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""\n        As a professional career advisor, analyze this CV and provide detailed insights.\n        CV TEXT:\n        {cv_text}\n\n        Please provide your response in this EXACT JSON format:\n        {{\n            "candidate_profile": {{\n                "name": "Extracted name or 'Not found'",\n                "email": "Extracted email or 'Not found'",\n                "phone": "Extracted phone or 'Not found'",\n                "summary": "2-3 sentence professional summary of the candidate"\n            }},\n            "skills_analysis": {{\n                "technical_skills": ["skill1", "skill2", "skill3"],\n                "soft_skills": ["skill1", "skill2"],\n                "certifications": ["cert1", "cert2"] or [],\n                "tools_technologies": ["tool1", "tool2"]\n            }},\n            "experience_analysis": {{\n                "total_years_experience": "X years",\n                "current_level": "Junior/Mid-level/Senior/Lead/Executive",\n                "career_progression": "Brief description of career growth",\n                "key_achievements": ["achievement1", "achievement2"]\n            }},\n            "job_recommendations": [\n                {{\n                    "role": "Job title",\n                    "match_score": 95,\n                    "reasoning": "Why this role matches the candidate",\n                    "required_skills": ["skill1", "skill2"],\n                    "salary_range": "$X - $Y",\n                    "growth_potential": "High/Medium/Low"\n                }}\n            ],\n            "cv_improvement_suggestions": [\n                {{\n                    "area": "Section name",\n                    "issue": "What needs improvement",\n                    "suggestion": "Specific improvement suggestion",\n                    "priority": "High/Medium/Low"\n                }}\n            ],\n            "market_insights": {{\n                "industry_trends": "Current trends in candidate's field",\n                "salary_benchmark": "Average salary for similar profiles",\n                "demand_outlook": "Job market demand - High/Medium/Low"\n            }}\n        }}\n\n        Be extremely detailed and professional. Return ONLY the valid JSON, nothing else.\n        """
        response = model.generate_content(prompt, generation_config=genai.GenerationConfig(max_output_tokens=4000, temperature=0.2))
        content = response.text.strip()
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_content = content[json_start:json_end]
            json_content = json_content.replace('\n', '').replace('\r', '')
            return json.loads(json_content)
        else:
            print('Could not find valid JSON in Gemini response.')
            return mock_cv_analysis(cv_text)
    except json.JSONDecodeError as je:
        print(f'Gemini API JSON parsing error: {je}')
        return mock_cv_analysis(cv_text)
    except Exception as e:
        print(f'Gemini API general error: {e}')
        return mock_cv_analysis(cv_text)

def search_real_jobs(query: str, country: str='') -> List[Dict]:
    jobs = []
    try:
        search_query = f'job {query}'
        if country:
            search_query += f' in {country}'
        with DDGS() as ddgs:
            results = ddgs.text(search_query, max_results=10)
            for r in results:
                title_lower = r.get('title', '').lower()
                body_lower = r.get('body', '').lower()
                if any((keyword in title_lower or keyword in body_lower for keyword in ['job', 'hiring', 'position', 'opening', 'career', 'employment'])):
                    job_title = r.get('title', 'N/A')
                    job_url = r.get('href', '#')
                    description_snippet = r.get('body', 'N/A')[:200] + '...'
                    company = 'Company not specified'
                    location = country if country else 'Location not specified'
                    jobs.append({'title': job_title, 'company': company, 'location': location, 'description': description_snippet, 'url': job_url, 'salary': 'Not specified', 'posted_date': 'N/A', 'job_type': 'N/A'})
        return jobs
    except Exception as e:
        print(f'Error searching jobs with DuckDuckGo: {e}')
        return get_mock_jobs(query, country)

def get_mock_jobs(query: str, country: str='') -> List[Dict]:
    base_location = country if country else 'Remote/Global'
    jobs = [{'title': f"Relevant Role for '{query}'", 'company': 'Tech Innovations Inc', 'location': base_location, 'description': f"This is a mock job listing related to your search '{query}'. In a production environment, this would be a real job found via search.", 'url': 'https://www.linkedin.com/jobs/', 'salary': '$80,000 - $130,000', 'posted_date': 'Recently', 'job_type': 'Full-time'}, {'title': 'Another Great Opportunity', 'company': 'Data Insights Corp', 'location': base_location, 'description': 'Apply your skills in a dynamic environment. This is a placeholder job listing.', 'url': 'https://stackoverflow.com/jobs', 'salary': '$90,000 - $140,000', 'posted_date': '2 days ago', 'job_type': 'Contract'}]
    return jobs

def format_comprehensive_results(analysis_result: Dict, jobs: List[Dict], country: str) -> str:
    if not analysis_result:
        return '# Error: Could not analyze CV.'
    profile = analysis_result.get('candidate_profile', {})
    skills_analysis = analysis_result.get('skills_analysis', {})
    experience_analysis = analysis_result.get('experience_analysis', {})
    job_recommendations = analysis_result.get('job_recommendations', [])
    cv_suggestions = analysis_result.get('cv_improvement_suggestions', [])
    market_insights = analysis_result.get('market_insights', {})
    profile_section = f'\n## 👤 Candidate Profile\n**Name:** {profile.get('name', 'Not found')}  \n**Contact:** {profile.get('email', 'Not found')} | {profile.get('phone', 'Not found')}  \n**Summary:** {profile.get('summary', 'N/A')}\n---\n## 🎯 Skills & Experience Analysis\n### 💻 Technical Skills:\n{', '.join(skills_analysis.get('technical_skills', [])[:10])}\n### 🤝 Soft Skills:\n{', '.join(skills_analysis.get('soft_skills', [])[:5])}\n### 🔧 Tools & Technologies:\n{', '.join(skills_analysis.get('tools_technologies', [])[:8])}\n### 📚 Certifications:\n{', '.join(skills_analysis.get('certifications', ['None listed']))}\n### ⏱ Experience Overview:\n- **Total Experience:** {experience_analysis.get('total_years_experience', 'N/A')}\n- **Current Level:** {experience_analysis.get('current_level', 'N/A')}\n- **Career Progression:** {experience_analysis.get('career_progression', 'N/A')}\n- **Key Achievements:**\n'
    for achievement in experience_analysis.get('key_achievements', [])[:3]:
        profile_section += f'  • {achievement}\n'
    recommendations_section = '\n---\n## 🎯 Top Job Recommendations\n'
    for i, job in enumerate(job_recommendations[:5], 1):
        recommendations_section += f"\n### {i}. {job.get('role', 'N/A')}\n**Match Score:** {job.get('match_score', 0)}% | **Growth Potential:** {job.get('growth_potential', 'N/A')}  \n**Salary Range:** {job.get('salary_range', 'N/A')}  \n**Why It's a Good Fit:** {job.get('reasoning', 'N/A')}  \n**Key Requirements:** {', '.join(job.get('required_skills', [])[:5])}\n"
    cv_section = '\n---\n## 📝 CV Improvement Suggestions\n'
    for suggestion in cv_suggestions[:5]:
        priority_emoji = '🔴' if suggestion.get('priority') == 'High' else '🟡' if suggestion.get('priority') == 'Medium' else '🟢'
        cv_section += f'\n{priority_emoji} **{suggestion.get('area', 'N/A')}**\n- **Issue:** {suggestion.get('issue', 'N/A')}\n- **Suggestion:** {suggestion.get('suggestion', 'N/A')}\n- **Priority:** {suggestion.get('priority', 'N/A')}\n'
    market_section = f'\n---\n## 📈 Market Insights\n**Industry Trends:** {market_insights.get('industry_trends', 'N/A')}  \n**Salary Benchmark:** {market_insights.get('salary_benchmark', 'N/A')}  \n**Demand Outlook:** {market_insights.get('demand_outlook', 'N/A')}\n---\n## 💼 Job Opportunities Found\n**Location Filter:** {(country if country else 'Global')} | **Jobs Found:** {len(jobs)}\n'
    jobs_section = ''
    for i, job in enumerate(jobs, 1):
        jobs_section += f'\n### 📋 [{job.get('title', 'N/A')}]({job.get('url', '#')})\n🏢 **Company:** {job.get('company', 'N/A')}  \n📍 **Location:** {job.get('location', 'N/A')}  \n💰 **Salary:** {job.get('salary', 'N/A')}  \n⏰ **Posted:** {job.get('posted_date', 'N/A')}  \n🔧 **Type:** {job.get('job_type', 'N/A')}  \n📝 **Description:** {job.get('description', 'N/A')}\n[🔗 Apply Now]({job.get('url', '#')})\n---\n'
    footer = '\n*Analysis generated by AI. Verify information independently.*'
    return profile_section + recommendations_section + cv_section + market_section + jobs_section + footer