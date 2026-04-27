import { useState } from "react";
import axios from "axios";
import Nav from "../Nav/nav";
import "./AddProductOption.css";

function AddProductOption() {
  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    console.log("Datos a enviar:", { barcode, name, price, description });

    setMessage("");
    setError("");

    try {
      const response = await axios.post("/api/products/", {
        barcode,
        name,
        price,
        description,
      });
      console.log("RESPUESTA", response.data);
      setMessage(`Producto creado: ${response.data.name}`);
      setBarcode("");
      setName("");
      setPrice("");
      setDescription("");
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo crear el producto");
    }
  };

  return (
    <section className="option-panel">
      <Nav />

      <form onSubmit={handleSubmit} className="option-form">
        <div className="box-title">
          <h2 className="title">Agregar productos</h2>
          <p className="description">
            Ingresa los datos del producto para crear un nuevo registro en el
            inventario.
          </p>
        </div>
        <div className="form-fields">
          <label className="label-add-product">
            Código de barras
            <input
              type="text"
              value={barcode}
              onChange={(e) => setBarcode(e.target.value)}
              placeholder="Código de barras"
            />
          </label>
          <label className="label-add-product">
            Nombre
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Nombre del producto"
            />
          </label>
          <label className="label-add-product">
            Precio
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="Precio"
            />
          </label>
          <label className="label-add-product">
            Descripción
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descripción opcional"
            />
          </label>
        </div>
        <button className="button" type="submit">
          Guardar producto
        </button>
        {message && <p className="success-message">{message}</p>}
        {error && <p className="error-message">{error}</p>}
      </form>
    </section>
  );
}

export default AddProductOption;
