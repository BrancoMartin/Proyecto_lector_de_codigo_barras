import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import "./start.css";
import AgentChat from "../Components/AgentChat/AgentChat";

function Start() {
  const [showAgent, setShowAgent] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="start-page">
      <header className="start-header">
        <h1>Sistema de Administración</h1>
        <p>Elige una acción para gestionar tu inventario y ventas</p>
      </header>

      <div className="start-actions">
        <button onClick={() => navigate("/add-product")}>
          Agregar Producto
        </button>
        <button onClick={() => navigate("/sales-history")}>
          Historial de Ventas
        </button>
        <button onClick={() => navigate("/scan-products")}>
          Escanear Productos
        </button>
      </div>

      {/* Botón flotante del agente IA */}
      <div className="agent-button-container">
        <button
          className="agent-button"
          onClick={() => setShowAgent(!showAgent)}
          title="¿Querés configurar el aumento de precios? Hablá con nuestro agente."
        >
          <span className="agent-icon">🤖</span>
        </button>
        <div className="agent-tooltip">
          ¿Querés configurar el aumento de precios? Hablá con nuestro agente.
        </div>
      </div>

      {/* Panel lateral del chat */}
      {showAgent && <AgentChat onClose={() => setShowAgent(false)} />}
    </div>
  );
}

export default Start;
