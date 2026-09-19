import re

with open('app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the old recommend code. It starts from class RecommendRequest and goes to the end of the file.
start_idx = content.find('class RecommendRequest(BaseModel):')

new_code = '''class RecommendRequest(BaseModel):
    mapped_categories: Dict[str, Any]
    profile: Dict[str, Any]

def _score_programs(programs_df, req, relax_district=False, relax_age=False):
    primary_cat = req.mapped_categories.get("primary_category", "")
    secondary_cat = req.mapped_categories.get("secondary_category", "")
    profile = req.profile

    user_age_str = str(profile.get("age", ""))
    user_age = int(user_age_str) if user_age_str.isdigit() else None
    
    user_district = str(profile.get("district", "")).lower()
    user_education = str(profile.get("education", "")).lower()
    
    user_wage_goal_str = str(profile.get("wage_goal", "")).replace(',', '').replace(' ', '')
    wage_digits = "".join(c for c in user_wage_goal_str if c.isdigit() or c == '.')
    user_wage_goal = float(wage_digits) if wage_digits.replace('.','',1).isdigit() else 0.0

    scored_programs = []
    
    for _, row in programs_df.iterrows():
        # FILTERING
        # Age
        if not relax_age and user_age is not None:
            min_age_str = str(row.get('min_age', ''))
            max_age_str = str(row.get('max_age', ''))
            if min_age_str.isdigit() and user_age < int(min_age_str):
                continue
            if max_age_str.isdigit() and user_age > int(max_age_str):
                continue
                
        # District availability
        if not relax_district:
            row_district = str(row.get('district_availability', '')).lower()
            if user_district and row_district and user_district not in row_district:
                continue
            
        row_edu = str(row.get('min_education', '')).lower()
        if user_education and row_edu and row_edu not in user_education:
            pass
            
        # SCORING
        cat_match = 0.0
        row_sector = str(row.get('sector', '')).lower()
        row_name = str(row.get('name', '')).lower()
        p_cat_l = primary_cat.lower()
        s_cat_l = secondary_cat.lower()
        
        if p_cat_l and (p_cat_l in row_sector or p_cat_l in row_name):
            cat_match = 1.0
        elif s_cat_l and (s_cat_l in row_sector or s_cat_l in row_name):
            cat_match = 0.8

        eligibility_fit = 0.5
        row_district = str(row.get('district_availability', '')).lower()
        if row_district and user_district and user_district in row_district:
            eligibility_fit += 0.25
        if row_edu and user_education and row_edu in user_education:
            eligibility_fit += 0.25
            
        wage_goal_fit = 0.0
        row_wage_str = str(row.get('wage_outcome', ''))
        row_wage_digits = "".join(c for c in row_wage_str if c.isdigit() or c == '.')
        row_wage = float(row_wage_digits) if row_wage_digits.replace('.','',1).isdigit() else 0.0
        
        if user_wage_goal > 0 and row_wage > 0:
            if row_wage >= user_wage_goal:
                wage_goal_fit = 1.0
            else:
                wage_goal_fit = row_wage / user_wage_goal
        elif user_wage_goal == 0:
            wage_goal_fit = 1.0
            
        total_score = (cat_match * 0.5) + (eligibility_fit * 0.3) + (wage_goal_fit * 0.2)
        
        program_dict = row.to_dict()
        program_dict['score'] = total_score
        scored_programs.append(program_dict)
        
    scored_programs.sort(key=lambda x: x['score'], reverse=True)
    return scored_programs

@app.post("/recommend")
async def recommend(req: RecommendRequest) -> JSONResponse:
    if PROGRAMS_DF.empty:
        return JSONResponse(status_code=500, content={"error": "Skilling programs data not loaded."})

    relaxed_filters = []
    
    # Try strict
    scored = _score_programs(PROGRAMS_DF, req, relax_district=False, relax_age=False)
    
    # Relax district
    if not scored:
        scored = _score_programs(PROGRAMS_DF, req, relax_district=True, relax_age=False)
        if scored:
            relaxed_filters.append("district_availability")
            
    # Relax age
    if not scored:
        scored = _score_programs(PROGRAMS_DF, req, relax_district=True, relax_age=True)
        if scored:
            relaxed_filters = ["district_availability", "age_range"]

    top_3 = scored[:3]
    client = genai.Client(api_key=settings.llm_api_key)
    
    for prog in top_3:
        prompt = f"""Generate a 1-sentence reasoning for why this program is recommended for the user.
Do not invent information. Reference the program details below.

User Profile:
{json.dumps(req.profile)}

Program Details:
{json.dumps(prog)}
"""
        try:
            response = client.models.generate_content(
                model=settings.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "text/plain",
                },
            )
            prog["reasoning"] = response.text.strip()
        except Exception:
            name = prog.get("name", "This")
            duration = prog.get("duration", "")
            scheme = prog.get("scheme", "")
            sector = req.profile.get("sector", prog.get("sector", ""))
            prog["reasoning"] = f"{name} is a {duration} {scheme} program matching your {sector} experience."

    response_data = {
        "results": top_3
    }
    if relaxed_filters:
        response_data["relaxed_filters"] = relaxed_filters
        
    return JSONResponse(status_code=200, content=response_data)
'''

content = content[:start_idx] + new_code

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
