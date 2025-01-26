import React, { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Task {
  id: string;
  text: string;
  urgency: number;
  importance: number;
  quadrant?: string;
}

const QUADRANTS = {
  "Do Now": "#4CAF50",
  "Schedule": "#FFEB3B",
  "Delegate": "#03A9F4",
  "Eliminate": "#F44336"
};

const EisenhowerMatrix: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskText, setTaskText] = useState("");

  useEffect(() => {
    console.log("📥 Loaded Tasks:", tasks);
  }, [tasks]);

  // Function to Fetch Tasks
  const fetchTasks = async () => {
    try {
      const response = await fetch(`${API_URL}/tasks`);
      if (!response.ok) throw new Error(`Failed to fetch tasks: ${response.statusText}`);

      const data: Task[] = await response.json();
      console.log("✅ Fetched Tasks:", data);

      setTasks(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("❌ Error fetching tasks:", error);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  // Generate UUID for tasks
  const generateUUID = () => {
    return crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
  };

  // Function to Add Task
  const addTask = async () => {
    if (!taskText.trim()) return;

    const newTask: Task = {
      id: generateUUID(),
      text: taskText.trim(),
      urgency: Math.floor(Math.random() * 5) + 1,
      importance: Math.floor(Math.random() * 5) + 1
    };

    console.log("📤 Sending Task to Backend:", newTask);

    try {
      const response = await fetch(`${API_URL}/rank-tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify([newTask])
      });

      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

      const rankedTasks: Task[] = await response.json();

      console.log("📥 Received Ranked Tasks:", rankedTasks);

      if (Array.isArray(rankedTasks) && rankedTasks.length > 0) {
        setTasks([...tasks, rankedTasks[0]]);
      } else {
        console.error("❌ AI did not return ranked tasks.");
      }
    } catch (error) {
      console.error("❌ Error ranking tasks:", error);
    }

    setTaskText("");
  };

  // Function to Delete Task
  const deleteTask = async (taskId: string) => {
    try {
      const response = await fetch(`${API_URL}/tasks/${taskId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Failed to delete task");

      setTasks(tasks.filter((task) => task.id !== taskId));
    } catch (error) {
      console.error("❌ Error deleting task:", error);
    }
  };

  return (
    <div style={{ textAlign: "center", padding: "20px", fontFamily: "Arial, sans-serif", backgroundColor: "#121212", minHeight: "100vh" }}>
      <h1 style={{ color: "white", fontSize: "24px", fontWeight: "bold", marginBottom: "20px" }}>🚀 Eisenhower Matrix AI</h1>
      
      <div style={{ marginBottom: "20px", display: "flex", justifyContent: "center", gap: "10px" }}>
        <input
          type="text"
          placeholder="Enter a task..."
          value={taskText}
          onChange={(e) => setTaskText(e.target.value)}
          style={{ padding: "10px", width: "300px", fontSize: "16px", borderRadius: "5px", border: "1px solid #ccc", backgroundColor: "white", color: "black", outline: "none" }}
        />
        <button onClick={addTask} style={{ padding: "10px 20px", backgroundColor: "#6200ea", color: "white", border: "none", cursor: "pointer", fontSize: "16px", borderRadius: "5px" }}>
          Add Task
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr", gap: "20px", width: "90%", margin: "auto" }}>
        {Object.keys(QUADRANTS).map((quadrant) => (
          <div key={quadrant} style={{ padding: "20px", color: "black", textAlign: "center", minHeight: "200px", borderRadius: "10px", boxShadow: "2px 2px 10px rgba(0, 0, 0, 0.3)", backgroundColor: QUADRANTS[quadrant as keyof typeof QUADRANTS] }}>
            <h2 style={{ fontSize: "22px", fontWeight: "bold", marginBottom: "10px", textTransform: "uppercase", color: "white" }}>{quadrant}</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {tasks.filter((task) => task.quadrant === quadrant).map((task) => (
                <div key={task.id} style={{ backgroundColor: "rgba(255, 255, 255, 0.9)", padding: "12px", borderRadius: "5px", fontSize: "16px", boxShadow: "1px 1px 5px rgba(0, 0, 0, 0.2)", textAlign: "center", fontWeight: "bold", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px" }}>
                  <input type="checkbox" onChange={() => deleteTask(task.id)} style={{ cursor: "pointer", transform: "scale(1.3)" }} />
                  {task.text}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};


// ** Styled Components **
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    textAlign: "center",
    padding: "20px",
    fontFamily: "Arial, sans-serif",
    backgroundColor: "#121212",
    minHeight: "100vh",
  },
  title: {
    color: "white",
    fontSize: "24px",
    fontWeight: "bold",
    marginBottom: "20px",
  },
  inputContainer: {
    marginBottom: "20px",
    display: "flex",
    justifyContent: "center",
    gap: "10px",
  },
  input: {
    padding: "10px",
    width: "300px",
    fontSize: "16px",
    borderRadius: "5px",
    border: "1px solid #ccc",
    backgroundColor: "white",
    color: "black",
    outline: "none",
  },
  button: {
    padding: "10px 20px",
    backgroundColor: "#6200ea",
    color: "white",
    border: "none",
    cursor: "pointer",
    fontSize: "16px",
    borderRadius: "5px",
  },
  matrix: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gridTemplateRows: "1fr 1fr",
    gap: "20px",
    width: "90%",
    margin: "auto",
  },
  quadrant: {
    padding: "20px",
    color: "black",
    textAlign: "center",
    minHeight: "200px",
    borderRadius: "10px",
    boxShadow: "2px 2px 10px rgba(0, 0, 0, 0.3)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
  },
  quadrantTitle: {
    fontSize: "22px",
    fontWeight: "bold",
    marginBottom: "10px",
    textTransform: "uppercase",
    color: "white",
  },
  taskContainer: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  task: {
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    padding: "12px",
    borderRadius: "5px",
    fontSize: "16px",
    boxShadow: "1px 1px 5px rgba(0, 0, 0, 0.2)",
    textAlign: "center",
    fontWeight: "bold",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "10px",
  },
  checkbox: {
    cursor: "pointer",
    transform: "scale(1.3)",
  },
};

export default EisenhowerMatrix;