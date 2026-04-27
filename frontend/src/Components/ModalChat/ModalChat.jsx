import { useState } from "react";
import axios from "axios";

function ModalChat({ onClose }) {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post("/api/ai/chat_category/", {
        user_message: prompt,
        conversation_history: [],
      });
      // Cerrar el modal después de enviar
      if (onClose) onClose();
    } catch (err) {
      console.log("error al querer crear la categoria mandando el prompt", err);
      // Opcional: cerrar el modal incluso en error, o manejar el error
      if (onClose) onClose();
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="">
        Hable con el chat diciendole suelen aumentar los precios de los
        productos
      </label>
      <input
        placeholder="ej: Suelen aumentarme por marca y por material"
        onChange={(e) => setPrompt(e.target.value)}
      />
      <button className="button" type="submit">
        Enviar
      </button>
    </form>
  );
}

export default ModalChat;
