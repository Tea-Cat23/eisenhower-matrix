from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import openai
import os
import json
import warnings
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Ignore warnings
warnings.filterwarnings("ignore")

# Ensure OpenAI API Key is loaded
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("⚠️ OPENAI_API_KEY is missing. Set it in Railway environment variables or .env file.")

openai.api_key = openai_api_key

# Initialize FastAPI app
app = FastAPI()

# Define allowed frontend origins
allowed_origins = [
    "https://eisenhower-matrix-git-main-tea-cats-projects.vercel.app",
    "https://eisenhower-matrix-phi.vercel.app",
    "http://localhost:3000",  # Local testing
]

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Use specific domains instead of "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],  # Added DELETE method for task removal
    allow_headers=["Authorization", "Content-Type"],
)

# Handle OPTIONS requests (Preflight)
@app.options("/{full_path:path}")
async def preflight_handler():
    return {"message": "CORS preflight request successful"}

# Define Task model
class Task(BaseModel):
    id: str
    text: str
    urgency: int = 5
    importance: int = 5
    quadrant: str = ""

# In-memory task storage
tasks = []

# Function to rank tasks using GPT-4
def ai_rank_tasks(task_list):
    prompt = f"""
    Analyze the following list of tasks and rank them in terms of:
    - Urgency (1-10 scale)
    - Importance (1-10 scale)
    - Best quadrant: "Do Now", "Schedule", "Delegate", or "Eliminate"

    Tasks:
    {json.dumps([task.text for task in task_list])}

    Respond in JSON format like this:
    [
        {{"text": "task 1", "urgency": 7, "importance": 9, "quadrant": "Do Now"}},
        {{"text": "task 2", "urgency": 5, "importance": 6, "quadrant": "Schedule"}}
    ]
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # Use 3.5 for cost efficiency
            messages=[
                {"role": "system", "content": "You are an intelligent productivity assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )

        response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not response_content:
            raise ValueError("⚠️ Empty response from OpenAI.")

        ranked_tasks = json.loads(response_content)
        return ranked_tasks

    except Exception as e:
        print(f"❌ Error calling OpenAI: {e}")
        return None

# API Endpoint to rank tasks
@app.post("/rank-tasks")
def rank_tasks(task_list: list[Task]):
    try:
        print("🔵 Received Tasks:", task_list)  # Log the incoming tasks

        # Call OpenAI ranking function
        ai_result = ai_rank_tasks(task_list)

        if not ai_result:
            raise HTTPException(status_code=500, detail="AI failed to rank tasks.")

        print("🟢 AI Ranked Tasks:", ai_result)

        # Update the tasks with AI-ranked values
        updated_tasks = []
        for task in task_list:
            for ranked_task in ai_result:
                if task.text.lower().strip() == ranked_task["text"].lower().strip():
                    updated_task = task.model_copy()
                    updated_task.urgency = ranked_task["urgency"]
                    updated_task.importance = ranked_task["importance"]
                    updated_task.quadrant = ranked_task["quadrant"]
                    updated_tasks.append(updated_task)

        print("✅ Final Updated Tasks:", updated_tasks)

        # Store tasks in-memory
        tasks.clear()
        tasks.extend(updated_tasks)

        return updated_tasks

    except Exception as e:
        print("❌ Backend Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoint to get all tasks
@app.get("/tasks")
def get_tasks():
    try:
        print("📥 Fetching Tasks...")
        return tasks  # Returns in-memory tasks
    except Exception as e:
        print("❌ Error fetching tasks:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoint to delete a task
@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    try:
        global tasks
        tasks = [task for task in tasks if task.id != task_id]
        print(f"🗑️ Deleted Task: {task_id}")
        return {"message": f"Task {task_id} deleted successfully"}
    except Exception as e:
        print("❌ Error deleting task:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Run the app on Railway
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Backend running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)