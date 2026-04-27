# 🤖 Guía de Uso - Agente Dinámico de IA

## Descripción General

El nuevo sistema incluye un **Agente de IA dinámico** que actúa como intermediario entre tu interfaz y los controllers del backend. El agente puede detectar automáticamente qué quieres hacer basándose en tu mensaje en lenguaje natural.

---

## 🎯 Cómo Usar

### 1. Acceder al Chat del Agente

- En la página principal, busca el **botón flotante con el ícono 🤖** en la esquina inferior derecha
- Al hacer click, se abrirá un panel lateral con un chat interactivo
- Verás un tooltip que dice: "¿Querés configurar el aumento de precios? Hablá con nuestro agente."

### 2. Ejemplos de Comandos

#### Crear Categorías

```
"Quiero crear una categoría llamada 'marca' con los atributos samsung, lg, sony"
"Crea una categoría de 'material' con plastico, metal y tela"
```

#### Agregar Atributos a Categoría Existente

```
"Agregá 'madera' a la categoría material"
"Quiero agregar nokia y motorola a marca"
```

#### Aumentar Precios

```
"Aumenta 20% los precios de samsung"
"Sube 15% los productos de marca sony"
```

#### Ver Categorías Configuradas

```
"Muestra las categorías"
"¿Qué categorías tengo?"
"Lista todas las categorías y sus atributos"
```

#### Consultas Generales (Asesor Financiero)

```
"¿Cuál es un buen margen de ganancia?"
"¿Cómo debo organizar mis precios?"
"¿Qué estrategia me recomendas?"
```

---

## 📋 Características

### ✅ Lo Que Puedes Hacer

1. **Crear categorías con atributos** - Define cómo se organizan tus productos
2. **Agregar atributos a categorías existentes** - Expande tus opciones
3. **Aumentar precios automáticamente** - Especifica categoría y porcentaje
4. **Ver todas tus categorías y atributos** - Consulta qué tienes configurado
5. **Obtener asesoramiento financiero** - Preguntas sobre estrategia de precios
6. **Mantener conversación contextual** - El agente recuerda el historial

### 🔄 Cómo Funciona

```
Tu Mensaje (lenguaje natural)
         ↓
   Agente LLM (detecta intención)
         ↓
  Ejecuta controller correspondiente
         ↓
  Respuesta procesada + confirmación
         ↓
  Mostrada en el chat
```

---

## 💾 Historial de Conversación

El historial se guarda automáticamente en tu navegador usando `localStorage`. Esto significa:

- ✅ El chat persiste si cierras el panel y lo vuelves a abrir
- ✅ El agente recuerda el contexto anterior
- ⚠️ Se borra si limpias los datos del navegador

---

## 🔧 Configuración Técnica

### Backend

- Endpoint: `POST /api/agent/chat`
- Requiere: `GROQ_API_KEY` en `.env`
- Modelo: `llama-3.1-8b-instant`
- Temperature: 0 (respuestas determinísticas)

### Frontend

- Componente: `AgentChat.jsx`
- Puerto: 5173 (Vite)
- Conexión: `http://localhost:8000/api/agent/chat`

---

## ⚡ Consejos de Uso

1. **Sé específico** - "Aumenta 20% samsung" es mejor que "aumenta precios"
2. **Menciona categoría y atributo** - Ayuda al agente a entender mejor
3. **Si falta info** - El agente te hará preguntas clarificadoras
4. **Consulta el historial** - Puedes revisar qué se ejecutó en el chat
5. **Error en intent** - Si el agente no entiende, reformula tu mensaje

---

## 🆘 Solución de Problemas

### El chat no se conecta

- Verifica que el backend esté corriendo en puerto 8000
- Revisa que `GROQ_API_KEY` esté configurado en `.env`

### El agente no ejecuta la acción

- Reformula tu mensaje de forma más clara
- Asegúrate de mencionar categoría y atributo cuando sea necesario
- Revisa que la categoría existe antes de agregar atributos

### Historial se borra

- Es normal si limpias el navegador
- Los datos están guardados en la base de datos, no se pierden

---

## 📝 Posibles Intenciones Detectadas

| Intención                | Ejemplo                                   |
| ------------------------ | ----------------------------------------- |
| `crear_categoria`        | "Crea categoría material con plastico..." |
| `agregar_atributo`       | "Agregá vidrio a material"                |
| `aumentar_precios`       | "Sube 20% samsung"                        |
| `listar_categorias`      | "Muestra categorías"                      |
| `consulta_general`       | "¿Cuál es buen margen?"                   |
| `informacion_incompleta` | Falta info, te pregunta                   |

---

**¡Listo! Comienza a usar el agente escribiendo un mensaje en el chat.** 🚀
