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
    raise ValueError("⚠️ OPENAI_API_KEY is missing. Set it in .env or Railway environment variables.")

openai.api_key = openai_api_key

# Initialize FastAPI
app = FastAPI()

# ✅ FIXED: Update CORS settings to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Define Task model
class Task(BaseModel):
    id: str
    text: str
    urgency: int = 5
    importance: int = 5
    quadrant: str = ""

# ✅ Function to manually determine quadrant (Fallback if AI fails)
def determine_quadrant(urgency: int, importance: int) -> str:
    if urgency >= 5 and importance >= 5:
        return "Do Now"
    elif urgency < 5 and importance >= 5:
        return "Schedule"
    elif urgency >= 5 and importance < 5:
        return "Delegate"
    else:
        return "Eliminate"

# ✅ AI-based ranking function
def ai_rank_tasks(task_list):
    prompt = f"""
    Analyze the following tasks and rank them by:
    - Urgency (1-10)
    - Importance (1-10)
    - Assign quadrant: "Do Now", "Schedule", "Delegate", or "Eliminate".

    Tasks:
    {json.dumps([task.text for task in task_list])}

    Respond strictly in JSON format:
    [
        {{"text": "task 1", "urgency": 7, "importance": 9, "quadrant": "Do Now"}},
        {{"text": "task 2", "urgency": 5, "importance": 6, "quadrant": "Schedule"}}
    ]
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a task-ranking AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )

        # ✅ Ensure AI response is valid JSON
        response_content = response["choices"][0]["message"]["content"]
        ranked_tasks = json.loads(response_content)

        print("✅ AI Response:", ranked_tasks)  # Debugging output
        return ranked_tasks

    except json.JSONDecodeError as e:
        print("❌ Error: Invalid JSON from OpenAI:", str(e))
        return None
    except Exception as e:
        print("❌ OpenAI API Error:", str(e))
        return None

# ✅ API Endpoint to rank tasks
@app.post("/rank-tasks")
def rank_tasks(task_list: list[Task]):
    try:
        print(f"📡 Received Tasks: {task_list}")

        ai_result = ai_rank_tasks(task_list)

        if ai_result:
            for task in task_list:
                for ranked_task in ai_result:
                    if task.text.lower().strip() == ranked_task["text"].lower().strip():
                        task.urgency = ranked_task.get("urgency", 5)
                        task.importance = ranked_task.get("importance", 5)
                        task.quadrant = ranked_task.get("quadrant", determine_quadrant(task.urgency, task.importance))
        else:
            # AI failed, assign quadrants manually
            for task in task_list:
                task.quadrant = determine_quadrant(task.urgency, task.importance)

        print("🚀 Ranked Tasks:", [task.dict() for task in task_list])  # Ensure correct logging
        return task_list

    except Exception as e:
        print("❌ Task Processing Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Run server locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Backend running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)