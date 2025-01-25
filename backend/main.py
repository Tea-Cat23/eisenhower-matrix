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

app = FastAPI()

# Define allowed CORS origins (Frontend URLs)
origins = [
    "https://eisenhower-matrix-git-main-tea-cats-projects.vercel.app",
    "https://eisenhower-matrix-backend-production-2c44.up.railway.app",
    "*",  # Allow all origins for testing, remove in production
]

# Enable CORS to allow frontend communication
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

# Function to determine quadrant manually (fallback if OpenAI fails)
def determine_quadrant(urgency: int, importance: int) -> str:
    if urgency >= 7 and importance >= 7:
        return "Do Now"
    elif urgency < 7 and importance >= 7:
        return "Schedule"
    elif urgency >= 7 and importance < 7:
        return "Delegate"
    else:
        return "Eliminate"

# Function to rank tasks dynamically using OpenAI
def ai_rank_tasks(task_list):
    prompt = f"""
    Analyze the following list of tasks and categorize them based on:
    - Urgency (1-10 scale)
    - Importance (1-10 scale)
    - Best quadrant: "Do Now", "Schedule", "Delegate", or "Eliminate"

    Tasks:
    {json.dumps([task.text for task in task_list], indent=2)}

    Respond ONLY in valid JSON format like this:
    [
        {{"text": "task 1", "urgency": 9, "importance": 10, "quadrant": "Do Now"}},
        {{"text": "task 2", "urgency": 5, "importance": 6, "quadrant": "Schedule"}}
    ]
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant that categorizes tasks based on urgency and importance."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )

        response_text = response["choices"][0]["message"]["content"]

        # Ensure response is valid JSON
        ranked_tasks = json.loads(response_text)
        if not isinstance(ranked_tasks, list):
            raise ValueError("Invalid response format from OpenAI")

        print("✅ AI Response:", ranked_tasks)
        return ranked_tasks

    except Exception as e:
        print("❌ OpenAI API Error:", str(e))
        return None  # Return None if OpenAI call fails

# Endpoint to rank tasks
@app.post("/rank-tasks")
def rank_tasks(task_list: list[Task]):
    try:
        print("📡 Received Tasks:", [task.dict() for task in task_list])
        
        # Get AI-ranked tasks
        ai_result = ai_rank_tasks(task_list)

        if ai_result:
            for task in task_list:
                for ranked_task in ai_result:
                    if task.text.strip().lower() == ranked_task["text"].strip().lower():
                        task.urgency = ranked_task.get("urgency", 5)
                        task.importance = ranked_task.get("importance", 5)
                        task.quadrant = ranked_task.get("quadrant", determine_quadrant(task.urgency, task.importance))
        else:
            # If AI fails, assign quadrants manually
            for task in task_list:
                task.quadrant = determine_quadrant(task.urgency, task.importance)

        print("🚀 Final Ranked Tasks:", [task.dict() for task in task_list])
        return task_list

    except Exception as e:
        print("❌ Error processing tasks:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Run the FastAPI app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Backend running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)