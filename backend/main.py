from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import openai
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure OpenAI API Key is loaded
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("⚠️ OPENAI_API_KEY is missing. Set it in Railway environment variables or .env file.")

openai.api_key = openai_api_key

# Initialize FastAPI app
app = FastAPI()

allow_origins = ["https://eisenhower-matrix-git-main-tea-cats-projects.vercel.app"]
# Allow CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Explicitly define allowed methods
    allow_headers=["Content-Type", "Authorization"],  # Allow specific headers
)

# Root endpoint to check if the server is running
@app.get("/")
async def root():
    return {"message": "🚀 Eisenhower Matrix Backend is running!"}

# Define Task model
class Task(BaseModel):
    id: str
    text: str
    urgency: int = 5
    importance: int = 5
    quadrant: str = ""

# Function to determine quadrant manually (fallback if OpenAI fails)
def determine_quadrant(urgency: int, importance: int) -> str:
    if urgency >= 7 and importance >= 7:
        return "Do Now"  # High urgency & high importance
    elif urgency < 7 and importance >= 7:
        return "Schedule"  # Low urgency & high importance
    elif urgency >= 7 and importance < 7:
        return "Delegate"  # High urgency & low importance
    else:
        return "Eliminate"  # Low urgency & low importance

# Function to rank tasks using GPT-4
def ai_rank_tasks(task_list):
    task_texts = [task.text for task in task_list]

    prompt = f"""
You are an AI that classifies tasks using the Eisenhower Matrix.
- Assign each task an urgency score (1-10).
- Assign each task an importance score (1-10).
- Categorize them into one of four quadrants:
    "Do Now" (High Urgency, High Importance)
    "Schedule" (Low Urgency, High Importance)
    "Delegate" (High Urgency, Low Importance)
    "Eliminate" (Low Urgency, Low Importance)

Tasks:
{json.dumps(task_texts)}

Respond ONLY in valid JSON format:
[
    {{"text": "Example Task", "urgency": 8, "importance": 6, "quadrant": "Delegate"}}
]
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an intelligent productivity assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        response_text = response["choices"][0]["message"]["content"]
        print("📥 OpenAI Raw Response:", response_text)  # Debugging

        ranked_tasks = json.loads(response_text)
        if not isinstance(ranked_tasks, list):
            raise ValueError("Invalid OpenAI response format. Expected a list.")

        print("✅ AI Parsed Tasks:", ranked_tasks)  # Log the parsed result
        return ranked_tasks
    except Exception as e:
        print("❌ OpenAI Error:", str(e))
        return None  # Return None if OpenAI fails

@app.options("/rank-tasks")
async def preflight():
    return {"message": "CORS preflight successful"}

@app.post("/rank-tasks")
async def rank_tasks(task_list: list[Task]):
    try:
        ai_result = ai_rank_tasks(task_list)

        if ai_result:
            for task in task_list:
                for ranked_task in ai_result:
                    if task.text.strip().lower() == ranked_task["text"].strip().lower():
                        task.urgency = ranked_task.get("urgency", 5)
                        task.importance = ranked_task.get("importance", 5)
                        task.quadrant = ranked_task.get("quadrant", determine_quadrant(task.urgency, task.importance))
        else:
            for task in task_list:
                task.quadrant = determine_quadrant(task.urgency, task.importance)

        print("🚀 Final Ranked Tasks:", [task.dict() for task in task_list])
        return task_list

    except Exception as e:
        print("❌ Error processing tasks:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Backend running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)