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

# Initialize FastAPI
app = FastAPI()

# CORS settings - Ensure correct frontend URLs
origins = [
    "https://eisenhower-matrix.vercel.app",  # Your Vercel frontend
    "http://localhost:3000",  # Local testing
    "*"  # Allow all (for debugging)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Task model
class Task(BaseModel):
    id: str
    text: str
    urgency: int = 5
    importance: int = 5
    quadrant: str = ""

# **Manual Quadrant Determination (Backup)**
def determine_quadrant(urgency: int, importance: int) -> str:
    if urgency >= 7 and importance >= 7:
        return "Do Now"
    elif urgency < 7 and importance >= 7:
        return "Schedule"
    elif urgency >= 7 and importance < 7:
        return "Delegate"
    else:
        return "Eliminate"

# **AI-Powered Task Ranking**
def ai_rank_tasks(task_list):
    prompt = f"""
    You are an intelligent productivity assistant. 
    Analyze and rank these tasks based on:
    - Urgency (1-10 scale)
    - Importance (1-10 scale)
    - Best quadrant: "Do Now", "Schedule", "Delegate", or "Eliminate"
    
    Tasks:
    {json.dumps([task.text for task in task_list], indent=2)}

    Return a JSON array where each task has urgency, importance, and a quadrant. 
    Example:
    [
        {{"text": "Task 1", "urgency": 8, "importance": 9, "quadrant": "Do Now"}},
        {{"text": "Task 2", "urgency": 5, "importance": 6, "quadrant": "Schedule"}}
    ]
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an intelligent productivity assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )

        # Parse AI response
        response_content = response["choices"][0]["message"]["content"]
        ranked_tasks = json.loads(response_content)

        print("✅ AI Response:", ranked_tasks)  # Debugging log
        return ranked_tasks

    except Exception as e:
        print("❌ Error calling OpenAI:", str(e))
        return None  # Return None if AI call fails

# **API Endpoint: Rank Tasks**
@app.post("/rank-tasks")
def rank_tasks(task_list: list[Task]):
    try:
        # Retrieve all tasks (existing + new)
        all_tasks = task_list  # Modify this if storing tasks persistently

        # AI ranks all tasks
        ai_result = ai_rank_tasks(all_tasks)

        if ai_result:
            for task in all_tasks:
                for ranked_task in ai_result:
                    if task.text == ranked_task["text"]:
                        task.urgency = ranked_task.get("urgency", 5)  # Default urgency
                        task.importance = ranked_task.get("importance", 5)  # Default importance
                        task.quadrant = ranked_task.get("quadrant", determine_quadrant(task.urgency, task.importance))

        else:
            # AI failed → Assign quadrants manually
            for task in all_tasks:
                task.quadrant = determine_quadrant(task.urgency, task.importance)

        print("🚀 Ranked Tasks:", [task.dict() for task in all_tasks])
        return all_tasks

    except Exception as e:
        print("❌ Error processing tasks:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# **Run the server**
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Backend running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)