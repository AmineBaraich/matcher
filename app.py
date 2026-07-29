import gradio as gr
import os
import google.generativeai as genai
from utils import extract_text_from_pdf, mock_cv_analysis, search_real_jobs, format_comprehensive_results
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

def analyze_cv_with_gemini(cv_text: str) -> dict:
    if not GEMINI_API_KEY:
        return mock_cv_analysis(cv_text)
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""\n        As a professional career advisor, analyze this CV and provide detailed insights.\n        CV TEXT:\n        {cv_text}\n        \n        Please provide your response in this exact JSON format:\n        {{\n            "candidate_profile": {{\n                "name": "Extracted name or 'Not found'",\n                "email": "Extracted email or 'Not found'",\n                "phone": "Extracted phone or 'Not found'",\n                "summary": "2-3 sentence professional summary of the candidate"\n            }},\n            "skills_analysis": {{\n                "technical_skills": ["skill1", "skill2", "skill3"],\n                "soft_skills": ["skill1", "skill2"],\n                "certifications": ["cert1", "cert2"] or [],\n                "tools_technologies": ["tool1", "tool2"]\n            }},\n            "experience_analysis": {{\n                "total_years_experience": "X years",\n                "current_level": "Junior/Mid-level/Senior/Lead/Executive",\n                "career_progression": "Brief description of career growth",\n                "key_achievements": ["achievement1", "achievement2"]\n            }},\n            "job_recommendations": [\n                {{\n                    "role": "Job title",\n                    "match_score": 95,\n                    "reasoning": "Why this role matches the candidate",\n                    "required_skills": ["skill1", "skill2"],\n                    "salary_range": "$X - $Y",\n                    "growth_potential": "High/Medium/Low"\n                }}\n            ],\n            "cv_improvement_suggestions": [\n                {{\n                    "area": "Section name",\n                    "issue": "What needs improvement",\n                    "suggestion": "Specific improvement suggestion",\n                    "priority": "High/Medium/Low"\n                }}\n            ],\n            "market_insights": {{\n                "industry_trends": "Current trends in candidate's field",\n                "salary_benchmark": "Average salary for similar profiles",\n                "demand_outlook": "Job market demand - High/Medium/Low"\n            }}\n        }}\n        \n        Be extremely detailed and professional. Only return valid JSON, nothing else.\n        """
        response = model.generate_content(prompt, generation_config=genai.GenerationConfig(max_output_tokens=4000))
        content = response.text.strip()
        import json
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_content = content[json_start:json_end]
            return json.loads(json_content)
        else:
            return mock_cv_analysis(cv_text)
    except Exception as e:
        print(f'Gemini API error: {str(e)}')
        return mock_cv_analysis(cv_text)

def analyze_cv_and_search_jobs(pdf_file, country, api_key=''):
    global GEMINI_API_KEY
    if api_key:
        GEMINI_API_KEY = api_key
    try:
        cv_text = extract_text_from_pdf(pdf_file)
        if GEMINI_API_KEY:
            analysis_result = analyze_cv_with_gemini(cv_text)
        else:
            analysis_result = mock_cv_analysis(cv_text)
        skills = analysis_result.get('skills_analysis', {}).get('technical_skills', [])
        titles = analysis_result.get('job_recommendations', [])
        search_terms = []
        if skills:
            search_terms.extend(skills[:5])
        if titles:
            search_terms.extend([t.get('role', '') for t in titles[:3]])
        search_query = ' '.join(search_terms) if search_terms else 'software developer'
        jobs = search_real_jobs(search_query, country)
        formatted_results = format_comprehensive_results(analysis_result, jobs, country)
        return formatted_results
    except Exception as e:
        return f'Error: {str(e)}'
with gr.Blocks(title='CV Job Matcher') as app:
    with gr.Row():
        with gr.Column(scale=1):
            pdf_input = gr.File(label='CV (PDF)', file_types=['.pdf'], type='filepath')
            api_key_input = gr.Textbox(label='Gemini API Key (Optional)', placeholder='Get free key: https://ai.google.dev/', type='password')
            country_input = gr.Dropdown(choices=['', 'Remote', 'USA', 'UK', 'Canada', 'Germany', 'France', 'Australia', 'India', 'Brazil'], value='', label='Location (Optional)')
            search_button = gr.Button('Find Jobs', variant='primary')
            clear_button = gr.Button('Clear')
        with gr.Column(scale=2):
            output = gr.Markdown(label='Results', value="Upload your CV and click 'Find Jobs'")

    def process_location(country):
        return country if country else ''
    search_button.click(fn=lambda pdf, api_key, country: analyze_cv_and_search_jobs(pdf, process_location(country), api_key), inputs=[pdf_input, api_key_input, country_input], outputs=output)
    clear_button.click(fn=lambda: [None, '', '', "Upload your CV and click 'Find Jobs'"], inputs=[], outputs=[pdf_input, api_key_input, country_input, output])
if __name__ == '__main__':
    app.launch(share=True, inline=False)