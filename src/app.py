import streamlit as st
from agente_respuestas import cargar_modelos, hacer_pregunta

# 1. Configuración avanzada de la página (Ancho amplio y colores)
st.set_page_config(
    page_title="Pegasus AI | Portal Interno", 
    page_icon="https://cdn-icons-png.flaticon.com/512/3233/3233483.png", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyectar un poco de CSS para ocultar el menú de Streamlit y mejorar el pie de página
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stChatInputContainer {padding-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

# 2. Inicializar modelos con caché (Ahora solo carga la base de datos de Pinecone)
@st.cache_resource(show_spinner=False)
def iniciar_ia():
    return cargar_modelos()

# 3. Barra lateral corporativa (Sidebar)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3233/3233483.png", width=100)
    st.title("Santo Pegasus")
    st.caption("Portal de Inteligencia Artificial")
    st.markdown("---")
    st.markdown("**Áreas conectadas:**")
    st.markdown("- 📚 Recursos Humanos\n- 💻 Back-end & Front-end\n- 🛡️ DevOps y Seguridad\n- 💳 Pagos y Finanzas")
    st.markdown("---")
    st.info("💡 **Tip:** Sé específico en tus preguntas para obtener mejores resultados.")

# 4. Diseño del área principal
st.title("Asistente Virtual Corporativo")
st.markdown("Consulta instantáneamente nuestra base de conocimiento interna, manuales de arquitectura y políticas de RRHH.")

# Cargar la base de datos silenciosamente con un spinner
with st.spinner("Conectando con la base de datos vectorial de Pegasus..."):
    db = iniciar_ia()  # <--- Recibimos únicamente 'db'

# =========================================================
# 5. Memoria del chat y contador de consultas
# =========================================================
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        {"rol": "assistant", "contenido": "¡Hola! Soy la IA de Santo Pegasus. ¿Qué manual o política necesitas consultar hoy?"}
    ]

if "contador_consultas" not in st.session_state:
    st.session_state.contador_consultas = 0

avatares = {
    "user": "🧑‍💻",
    "assistant": "https://cdn-icons-png.flaticon.com/512/3233/3233483.png"
}

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"], avatar=avatares[mensaje["rol"]]):
        st.markdown(mensaje["contenido"])

# =========================================================
# 6. Entrada del usuario protegida por límite
# =========================================================
if st.session_state.contador_consultas >= 10:
    st.error("🔒 Has alcanzado el límite de 10 consultas por sesión para proteger los recursos del sistema. Por favor, recarga la página para iniciar una nueva sesión.")
else:
    pregunta_usuario = st.chat_input("Ej: ¿Qué permisos tiene el rol ROLE_DOCTOR?")

    if pregunta_usuario:
        st.session_state.contador_consultas += 1
        
        with st.chat_message("user", avatar=avatares["user"]):
            st.markdown(pregunta_usuario)
        
        st.session_state.mensajes.append({"rol": "user", "contenido": pregunta_usuario})

        with st.chat_message("assistant", avatar=avatares["assistant"]):
            with st.spinner("Analizando documentos..."):
                # <--- Llamamos a hacer_pregunta pasando solo 'db' y la pregunta
                respuesta_ia = hacer_pregunta(db, pregunta_usuario)
                st.markdown(respuesta_ia)
                
        st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta_ia})