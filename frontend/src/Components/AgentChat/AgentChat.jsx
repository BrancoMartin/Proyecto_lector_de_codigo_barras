import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./AgentChat.css";

function AgentChat({ onClose }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "assistant",
      text: "¡Hola! Soy tu asistente de precios. Puedo ayudarte a:\n\n• Crear categorías de aumento de precios\n• Agregar o modificar atributos\n• Aumentar precios por categoría\n• Listar categorías y atributos\n\n¿En qué puedo ayudarte?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [categories, setCategories] = useState();

  // Auto-scroll al final de los mensajes
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    async () => {
      const categories = await axios.get("/api/category");
      setCategories(categories);
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Enviar mensaje al agente
  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!input.trim()) return;

    // Agregar mensaje del usuario a la UI
    const userMessage = {
      id: messages.length + 1,
      type: "user",
      text: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      // Preparar historial de conversación para enviar al backend
      const conversationForBackend = conversationHistory.map((msg) => ({
        user: msg.user || "",
        assistant: msg.assistant || "",
      }));

      // Llamar al endpoint del agente
      const response = await axios.post(
        "http://localhost:8000/api/agent/chat",
        {
          message: input,
          conversation_history: conversationForBackend,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      const data = response.data;

      // Agregar respuesta del asistente
      const assistantMessage = {
        id: messages.length + 2,
        type: "assistant",
        text: data.message,
        actionExecuted: data.action_executed,
        success: data.success,
        actionData: data.data,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Actualizar historial de conversación
      const newHistory = [
        ...conversationHistory,
        {
          user: input,
          assistant: data.message,
        },
      ];
      setConversationHistory(newHistory);

      // Guardar historial en localStorage para persistencia
      localStorage.setItem("agentChatHistory", JSON.stringify(newHistory));
    } catch (error) {
      console.error("Error sending message to agent:", error);

      const errorMessage = {
        id: messages.length + 2,
        type: "assistant",
        text: "❌ Disculpa, ocurrió un error al procesar tu mensaje. Intenta nuevamente.",
        error: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // Cargar historial al montar el componente
  useEffect(() => {
    const savedHistory = localStorage.getItem("agentChatHistory");
    if (savedHistory) {
      try {
        setConversationHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error("Error loading chat history:", error);
      }
    }
  }, []);

  return (
    <aside className="agent-chat-panel">
      <div className="chat-header">
        <h3>Asistente de Precios</h3>
        <button className="close-btn" onClick={onClose} title="Cerrar chat">
          ✕
        </button>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message ${msg.type} ${msg.error ? "error" : ""}`}
          >
            <div className="message-content">
              {msg.type === "assistant" && <span className="avatar">🤖</span>}
              <div className="message-text">{msg.text}</div>
              {msg.type === "user" && <span className="avatar">👤</span>}
            </div>
            {msg.actionExecuted && (
              <div className="action-badge">
                {msg.success ? "✅" : "⚠️"} {msg.actionExecuted}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message assistant loading">
            <div className="message-content">
              <span className="avatar">🤖</span>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe tu mensaje aquí..."
          disabled={loading}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="send-btn"
        >
          {loading ? "..." : "Enviar"}
        </button>
      </form>
    </aside>
  );
}

export default AgentChat;
