import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

from app.graphs.state import InterviewState
from app.services.groq_client import GroqService
from app.models import db
from app.models.interview import InterviewKit

def prepare_context_node(state: InterviewState) -> Dict[str, Any]:
    """
    Step 1: Format candidate profile details and missing skills for targeted question synthesis.
    """
    return {}


def generate_questions_node(state: InterviewState) -> Dict[str, Any]:
    """
    Step 2: Generate categorized interview questions (Technical, Resume-based, Gap Probes, Behavioral) via Groq.
    """
    job_title = state.get("job_title", "Software Engineer")
    candidate_name = state.get("candidate_name", "Candidate")
    candidate_skills = state.get("candidate_skills", [])
    projects = state.get("candidate_projects", [])
    missing_skills = state.get("missing_skills", [])
    experience = state.get("candidate_experience", [])

    system_prompt = (
        "You are a Principal Technical Recruiter and Hiring Manager. "
        "Generate a rigorous, tailored, role-specific interview question kit. "
        "Questions must test genuine depth, challenge specific resume claims, and uncover skill gaps. "
        "Return ONLY a valid JSON object matching the requested schema."
    )

    projects_summary = "\n".join([
        f"- {p.get('title', 'Project')}: {p.get('description', '')} (Tech: {', '.join(p.get('tech_stack', []))})"
        for p in projects[:3]
    ]) if projects else "General software development projects."

    exp_summary = "\n".join([
        f"- {e.get('role', 'Role')} at {e.get('company', 'Company')}: {e.get('description', '')}"
        for e in experience[:2]
    ]) if experience else "Software engineering background."

    user_prompt = f"""
Job Role: {job_title}
Job Description Overview: {state.get('job_description', '')[:1000]}

Candidate Name: {candidate_name}
Candidate Skills: {', '.join(candidate_skills[:15])}
Identified Skill Gaps: {', '.join(missing_skills) if missing_skills else 'None identified'}

Candidate Projects:
{projects_summary}

Candidate Experience:
{exp_summary}

Generate an interview kit in JSON format with EXACTLY these four categories:
{{
  "technical_questions": [
    {{
      "question": "Deep technical question on core JD technologies",
      "topic": "Technology/Concept",
      "expected_answer": "Key concepts and depth expected in candidate's response",
      "red_flags": "Superficial knowledge, incorrect assumptions"
    }},
    {{
      "question": "Second technical question",
      "topic": "Architecture/Performance",
      "expected_answer": "Good answer indicators",
      "red_flags": "Red flags"
    }},
    {{
      "question": "Third technical question",
      "topic": "Debugging/Optimization",
      "expected_answer": "Good answer indicators",
      "red_flags": "Red flags"
    }}
  ],
  "resume_questions": [
    {{
      "question": "Question specifically challenging candidate's claimed project or achievement",
      "reference_claim": "Referenced project or company experience",
      "expected_answer": "Concrete architectural explanation, metrics, or personal ownership",
      "red_flags": "Vague contributions, unable to explain design choices"
    }},
    {{
      "question": "Second resume-based probe",
      "reference_claim": "Referenced skill or milestone",
      "expected_answer": "Clear rationale for technology tradeoffs",
      "red_flags": "Took credit for team's work, cannot explain internals"
    }},
    {{
      "question": "Third resume-based probe",
      "reference_claim": "Production issue or scaling claim",
      "expected_answer": "Root-cause analysis and mitigation strategies",
      "red_flags": "Blames others, lacks accountability"
    }}
  ],
  "gap_questions": [
    {{
      "question": "Question probing candidate's adaptability to an unverified or missing required skill",
      "skill_gap": "Targeted missing skill",
      "expected_answer": "Demonstrated fundamentals and fast learning ability",
      "red_flags": "Dismissive attitude towards missing tools"
    }},
    {{
      "question": "Second gap probe question",
      "skill_gap": "Targeted secondary skill",
      "expected_answer": "Analogous technology comparisons",
      "red_flags": "Pretending to know without hands-on depth"
    }}
  ],
  "behavioral_questions": [
    {{
      "question": "STAR question on engineering conflict, deadline pressure, or ambiguity",
      "situation_type": "Conflict / Ownership",
      "star_guidelines": "Situation: context, Task: objective, Action: specific proactive steps, Result: measurable outcome"
    }},
    {{
      "question": "STAR question on technical failure or difficult bug resolution",
      "situation_type": "Resilience / Continuous Improvement",
      "star_guidelines": "Humility, accountability, learning loop"
    }}
  ]
}}
"""

    ai_kit = GroqService.call_structured_json(user_prompt, system_prompt)

    if not ai_kit or "technical_questions" not in ai_kit:
        # High quality fallback tailored to candidate skills
        top_skill_1 = candidate_skills[0] if len(candidate_skills) > 0 else "Python"
        top_skill_2 = candidate_skills[1] if len(candidate_skills) > 1 else "SQL"
        gap_skill = missing_skills[0] if missing_skills else "Cloud Architecture"

        ai_kit = {
            "technical_questions": [
                {
                    "question": f"In {top_skill_1}, how do you approach memory management, concurrency, and thread safety in high-throughput applications?",
                    "topic": top_skill_1,
                    "expected_answer": "Mentions GIL/thread pools, synchronization primitives, immutable data structures, or event-loop mechanics.",
                    "red_flags": "Confusing multi-threading with asynchronous I/O, unaware of concurrency pitfalls."
                },
                {
                    "question": f"When designing RESTful APIs or services with {top_skill_2}, how do you structure query optimization and connection pooling?",
                    "topic": top_skill_2,
                    "expected_answer": "Explains indexing strategies, EXPLAIN query plans, avoiding N+1 queries, and connection pool sizing.",
                    "red_flags": "Suggests full table scans or unbounded joins, ignores indexing overhead."
                },
                {
                    "question": "Describe your strategy for graceful error handling, structured logging, and observability in production distributed systems.",
                    "topic": "System Reliability",
                    "expected_answer": "Mentions centralized logging, correlation IDs, circuit breakers, and semantic HTTP error codes.",
                    "red_flags": "Catch-all silent try-except blocks, lack of error tracking."
                }
            ],
            "resume_questions": [
                {
                    "question": f"In your recent projects, what was the most complex technical trade-off you had to make, and what would you do differently today?",
                    "reference_claim": "Recent project implementation",
                    "expected_answer": "Articulates pros/cons considered (e.g. latency vs consistency, build vs buy) with clear technical justification.",
                    "red_flags": "Claiming there were no trade-offs or unable to recall design details."
                },
                {
                    "question": "Walk me through how you benchmarked and tested the performance claims mentioned on your resume.",
                    "reference_claim": "Performance and scalability statements",
                    "expected_answer": "Details load testing tools, baseline metrics, p99 latency tracking, and profiling tools.",
                    "red_flags": "Pure guesswork, fabricated percentage improvements without measurement methodology."
                },
                {
                    "question": "Describe a production incident or severe bug that slipped past QA in a system you contributed to. How did you diagnose and resolve it?",
                    "reference_claim": "Production development & maintenance",
                    "expected_answer": "Clear root cause analysis, immediate remediation, and post-mortem preventative safeguards.",
                    "red_flags": "Defensiveness, blaming QA or product team."
                }
            ],
            "gap_questions": [
                {
                    "question": f"Our role emphasizes {gap_skill}, which is not prominent in your background. How would you transfer your existing expertise to master this quickly?",
                    "skill_gap": gap_skill,
                    "expected_answer": "Draws parallels from similar tools, outlines a concrete 30-day learning plan, and demonstrates curiosity.",
                    "red_flags": "Dismisses the importance of the requirement or claims mastery without evidence."
                },
                {
                    "question": f"Can you describe an instance where you had to ship code using an unfamiliar technology or framework like {gap_skill} within a tight deadline?",
                    "skill_gap": "Adaptability",
                    "expected_answer": "Systematic approach: documentation review, prototyping, code reviews, and incremental verification.",
                    "red_flags": "Paralysis by analysis or reckless copy-pasting without understanding."
                }
            ],
            "behavioral_questions": [
                {
                    "question": "Tell me about a time when you disagreed with an architectural or technical decision proposed by a lead or peer. How did you handle it?",
                    "situation_type": "Technical Disagreement",
                    "star_guidelines": "Evaluates data-driven persuasion, professional respect, and ability to commit once a decision is made."
                },
                {
                    "question": "Describe a situation where project specifications changed drastically mid-sprint. How did you adapt your deliverables?",
                    "situation_type": "Agility & Deadline Pressure",
                    "star_guidelines": "Evaluates prioritization, communication with stakeholders, and composure under pressure."
                }
            ]
        }

    return {
        "technical_questions": ai_kit.get("technical_questions", []),
        "resume_questions": ai_kit.get("resume_questions", []),
        "gap_questions": ai_kit.get("gap_questions", []),
        "behavioral_questions": ai_kit.get("behavioral_questions", [])
    }


def rubrics_and_guidance_node(state: InterviewState) -> Dict[str, Any]:
    """
    Step 3: Add recruiter scoring rubrics and rating scale.
    """
    rubrics = {
        "scoring_scale": {
            "1": "Unsatisfactory - Poor fundamental understanding, unable to answer core questions, red flags observed.",
            "2": "Below Average - Surface level familiarity, struggles with practical tradeoffs or design nuances.",
            "3": "Competent - Solid grasp of primary concepts, meets standard expectations for the level.",
            "4": "Strong - Deep technical fluency, clear architectural vision, strong problem-solving and communication.",
            "5": "Exceptional - Domain expert, teaches interviewer new insights, proactive systems-level thinking."
        },
        "evaluation_criteria": [
            "Technical Mastery & Depth (40%)",
            "Resume Authenticity & Ownership (25%)",
            "Learning Agility & Gap Adaptability (20%)",
            "Communication & Culture Alignment (15%)"
        ],
        "hiring_recommendation_guidelines": "Score 4.0+ to recommend for on-site / final offer."
    }
    return {"rubrics": rubrics}


def save_kit_node(state: InterviewState) -> Dict[str, Any]:
    """
    Step 4: Persist interview kit to database.
    """
    try:
        job_id = state["job_id"]
        candidate_id = state["candidate_id"]

        kit = InterviewKit.query.filter_by(job_id=job_id, candidate_id=candidate_id).first()
        if not kit:
            kit = InterviewKit(job_id=job_id, candidate_id=candidate_id)
            db.session.add(kit)

        kit.technical_questions = state.get("technical_questions", [])
        kit.resume_questions = state.get("resume_questions", [])
        kit.gap_questions = state.get("gap_questions", [])
        kit.behavioral_questions = state.get("behavioral_questions", [])
        kit.rubrics = state.get("rubrics", {})

        db.session.commit()
        return {}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Failed to save interview kit: {str(e)}"}


def build_interview_graph():
    """
    Constructs the LangGraph workflow for AI interview question generation.
    """
    workflow = StateGraph(InterviewState)

    workflow.add_node("prepare_context", prepare_context_node)
    workflow.add_node("generate_questions", generate_questions_node)
    workflow.add_node("rubrics_and_guidance", rubrics_and_guidance_node)
    workflow.add_node("save_kit", save_kit_node)

    workflow.set_entry_point("prepare_context")

    workflow.add_edge("prepare_context", "generate_questions")
    workflow.add_edge("generate_questions", "rubrics_and_guidance")
    workflow.add_edge("rubrics_and_guidance", "save_kit")
    workflow.add_edge("save_kit", END)

    return workflow.compile()

