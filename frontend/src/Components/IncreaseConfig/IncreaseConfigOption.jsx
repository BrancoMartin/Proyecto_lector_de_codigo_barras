import { useState, useEffect } from "react";
import axios from "axios";
import "./IncreaseConfigOption.css";
import Nav from "../Nav/nav";
import ModalChat from "../ModalChat/ModalChat";

function IncreaseConfigOption() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [priceRules, setPriceRules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Agregar mensaje del usuario
    const userMessage = inputValue;
    setMessages((prev) => [...prev, { type: "user", text: userMessage }]);
    setInputValue("");
    setLoading(true);
    setError("");

    try {
      // Enviar al servidor
      const response = await axios.put("/api/ai/chat/", {
        user_message: userMessage,
        conversation_history: messages,
      });

      console.log("RESPONSE", response);

      // Agregar respuesta del asistente
      setMessages((prev) => [
        ...prev,
        { type: "assistant", text: response.data.response },
      ]);

      // Si se guardó una regla, actualizar la lista
      if (response.data.saved_rule) {
        setPriceRules((prev) => [...prev, response.data.saved_rule]);
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail || "Error al procesar el mensaje";
      setError(errorMsg);
      setMessages((prev) => [
        ...prev,
        { type: "error", text: `Error: ${errorMsg}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRule = async (ruleId) => {
    try {
      await axios.delete(`/api/pricing/rules/${ruleId}`);
      setPriceRules((prev) => prev.filter((rule) => rule.id !== ruleId));
    } catch (err) {
      setError("No se pudo eliminar la regla");
    }
  };

  return (
    <section className="option-panel">
      <Nav />

      <div className="increase-config-container">
        <div className="config-header">
          <h2>Configuración de Precios con IA</h2>
          <p>
            Habla con nuestro asistente para configurar cómo aumentan tus
            precios
          </p>
        </div>

        <div className="config-content">
          {/* Chat area */}
          <div className="chat-section">
            <div className="chat-messages">
              {messages.length === 0 && (
                <div className="welcome-message">
                  <p>¡Hola! Soy tu asistente de precios.</p>
                  <p>
                    Cuéntame cómo quieres aumentar tus precios. Por ejemplo:
                  </p>
                  <ul>
                    <li>"Aumenta 15% los productos de Samsung"</li>
                    <li>"Los productos de plástico llevan 10% más"</li>
                    <li>"El proveedor Sony tiene 20% de aumento"</li>
                  </ul>
                </div>
              )}
              {messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.type}`}>
                  <p>{msg.text}</p>
                </div>
              ))}
              {loading && (
                <div className="message assistant loading">
                  <p>Procesando...</p>
                </div>
              )}
            </div>

            <form onSubmit={handleSendMessage} className="chat-form">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Escribe el porcentaje de aumento y a que categoria aplicarlo..."
                disabled={loading}
              />
              <button type="submit" disabled={loading || !inputValue.trim()}>
                Enviar
              </button>
            </form>

            {error && <p className="error-message">{error}</p>}
          </div>

          {/* Rules list */}
          <div className="rules-section">
            <h3>Reglas Activas ({priceRules.length})</h3>
            {priceRules.length === 0 ? (
              <p className="no-rules">No hay reglas configuradas aún</p>
            ) : (
              <div className="rules-list">
                {priceRules.map((rule) => (
                  <div key={rule.id} className="rule-card">
                    <div className="rule-info">
                      <strong>{rule.category}</strong>
                      <p>{rule.attribute}</p>
                      <span className="percentage">
                        +{rule.increase_percentage}%
                      </span>
                    </div>
                    <button
                      onClick={() => handleDeleteRule(rule.id)}
                      className="delete-btn"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

export default IncreaseConfigOption;
