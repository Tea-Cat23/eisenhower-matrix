"use client";

import React, { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";

// Define Quadrant type
type Quadrant = "Do Now" | "Schedule" | "Delegate" | "Eliminate";

// Define colors for each quadrant
const colors: Record<Quadrant, string> = {
  "Do Now": "#4CAF50",  // Green
  Schedule: "#FFEB3B",  // Yellow
  Delegate: "#03A9F4",  // Blue
  Eliminate: "#F44336", // Red
};

// Define Task Interface
interface Task {
  id: string;
  text: string;
  urgency?: number;
  importance?: number;
  quadrant?: Quadrant;
}

// API Base URL (Update with correct backend URL)
const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://eisenhower-matrix-backend-production-2c44.up.railway.app";

const EisenhowerMatrix = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskText, setTaskText] = useState("");

  useEffect(() => {
    console.log("🚀 Loaded Tasks:", tasks);
  }, [tasks]);

  // **Add Task Function**
  const addTask = async () => {
    if (!taskText.trim()) return; // Prevent empty tasks

    const newTask: Task = {
      id: uuidv4(),
      text: taskText.trim(),
      urgency: 5,
      importance: 5,
      quadrant: undefined, // Let GPT-4o assign the correct quadrant
    };

    try {
      console.log("📡 Sending Task to Backend:", newTask);

      const response = await fetch(`${API_URL}/rank-tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([...tasks, newTask]), // Send all tasks for AI reevaluation
      });

      if (!response.ok) throw new Error(`Failed to fetch ranking: ${response.statusText}`);

      const rankedTasks: Task[] = await response.json();
      console.log("📥 Received Ranked Tasks:", rankedTasks);

      // Ensure tasks are correctly assigned to quadrants
      setTasks(
        rankedTasks.map((task) => ({
          ...task,
          quadrant: (task.quadrant as Quadrant) || "Eliminate", // Default to 'Eliminate' if missing
        }))
      );
    } catch (error) {
      console.error("❌ Error ranking tasks:", error);
    }

    setTaskText(""); // Reset input field
  };

  // **Remove Completed Task**
  const removeTask = (taskId: string) => {
    setTasks((prevTasks) => prevTasks.filter((task) => task.id !== taskId));
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>🚀 Eisenhower Matrix AI</h1>

      <div style={styles.inputContainer}>
        <input
          value={taskText}
          onChange={(e) => setTaskText(e.target.value)}
          placeholder="Enter a task..."
          style={styles.input}
        />
        <button onClick={addTask} style={styles.button}>
          Add Task
        </button>
      </div>

      {/* ** Eisenhower Matrix Grid ** */}
      <div style={styles.matrix}>
        {(["Do Now", "Schedule", "Delegate", "Eliminate"] as Quadrant[]).map((quadrant, index) => (
          <div key={index} style={{ ...styles.quadrant, backgroundColor: colors[quadrant] }}>
            <h2 style={styles.quadrantTitle}>{quadrant}</h2>
            <div style={styles.taskContainer}>
              {tasks
                .filter((task) => task.quadrant === quadrant)
                .map((task) => (
                  <div key={task.id} style={styles.task}>
                    <input type="checkbox" onChange={() => removeTask(task.id)} style={styles.checkbox} />
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