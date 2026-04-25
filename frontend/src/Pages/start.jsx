import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import "./start.css";
import ModalChat from "../Components/ModalChat/ModalChat";

function Start() {
  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Mostrar el modal solo la primera vez que se abre el componente
    if (!localStorage.getItem("IncreaseConfigModalShown")) {
      setShowModal(true);
    }
  }, []);

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
        <button onClick={() => navigate("/price-config")}>
          Configurar Aumentos
        </button>
      </div>
      {showModal && (
        <ModalChat
          onClose={() => {
            setShowModal(false);
            localStorage.setItem("IncreaseConfigModalShown", "true");
          }}
        />
      )}
    </div>
  );
}

export default Start;
