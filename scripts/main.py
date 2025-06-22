import streamlit as st
from datetime import datetime
from voice_nika import VoiceToTextConverter


st.set_page_config(
    layout="wide",
    page_title="Личный дневник с эмоциональной окраской текста",
    page_icon="📔"
)

st.markdown("""
<style>
    /* Основной макет */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-start;
        gap: 2rem;
    }

    /* Левая панель */
    .left-panel {
        width: 40%;
    }

    /* Правая панель */
    .right-panel {
        width: 60%;
        max-height: 80vh;
        overflow-y: auto;
        padding-right: 1rem;
    }

    /* Заметки */
    .note-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid #4e8cff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Кнопки */
    .stButton>button {
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
    }

    /* Поле ввода */
    .stTextArea textarea {
        min-height: 200px !important;
    }

    /* Заголовок */
    .main-title {
        color: #4e8cff !important;
        margin-bottom: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

if 'notes' not in st.session_state:
    st.session_state.notes = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'input_mode' not in st.session_state:
    st.session_state.input_mode = "text"
if 'voice_converter' not in st.session_state:
    st.session_state.voice_converter = VoiceToTextConverter()
if 'recognized_text' not in st.session_state:
    st.session_state.recognized_text = ""
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False


st.markdown('<h1 class="main-title">Личный дневник с эмоциональной окраской текста</h1>', unsafe_allow_html=True)
st.markdown("---")

# Основной контейнер
col1, col2 = st.columns([0.4, 0.6], gap="large")

with col1:
    st.subheader("Формат записи")

    input_mode = st.selectbox(
        "Выберите тип записи:",
        ["✏️ Текст", "🎤 Аудио"],
        index=0,
        label_visibility="collapsed"
    )

    if input_mode == "✏️ Текст":
        with st.form("text_entry_form", clear_on_submit=True):
            note_content = st.text_area(
                "Ваша запись:",
                placeholder="Опишите свои мысли и чувства...",
                height=250,
                label_visibility="collapsed"
            )

            submitted = st.form_submit_button(
                "📝 Создать заметку",
                type="primary",
                use_container_width=True
            )

            if submitted and note_content.strip():
                new_note = {
                    "type": "text",
                    "content": note_content,
                    "time": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "emotion": "✏️"
                }
                st.session_state.notes.append(new_note)
                st.rerun()


    else:
        if not st.session_state.is_recording:
            if st.button("🎤 Начать голосовую запись", use_container_width=True):
                st.session_state.is_recording = True
                st.rerun()
        else:
            with st.spinner("Запись... Говорите сейчас (10 сек)"):
                audio_data = st.session_state.voice_converter.record_voice()
                st.session_state.recognized_text = st.session_state.voice_converter.audio_to_text(audio_data)
                st.session_state.is_recording = False
                st.rerun()

        if st.session_state.recognized_text:
            with st.form("audio_entry_form", clear_on_submit=True):
                note_content = st.text_area(
                    "Распознанный текст:",
                    value=st.session_state.recognized_text,
                    height=150,
                    label_visibility="collapsed"
                )
                
                submitted = st.form_submit_button(
                    "📝 Создать заметку",
                    type="primary",
                    use_container_width=True
                )
                
                if submitted and note_content.strip():
                    new_note = {
                        "type": "text",
                        "content": note_content,
                        "time": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        "emotion": "🎤"
                    }
                    st.session_state.notes.append(new_note)
                    st.session_state.recognized_text = ""
                    st.rerun()

                submitted = st.form_submit_button(
                    "📝 Создать заметку",
                    type="primary",
                    use_container_width=True
                )

                if submitted and note_content.strip():
                    new_note = {
                        "type": "text",
                        "content": note_content,
                        "time": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        "emotion": "🎤"
                    }
                    st.session_state.notes.append(new_note)
                    st.session_state.recognized_text = ""
                    st.rerun()

with col2:
    st.subheader("История записей")

    if not st.session_state.notes:
        st.info("Здесь будут появляться ваши записи")
    else:
        for i, note in enumerate(reversed(st.session_state.notes)):
            with st.container():
                st.markdown(f"""
                <div class="note-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 1.5rem;">{note.get('emotion', '😊')}</span>
                            <h4 style="margin: 0;">Запись от {note["time"]}</h4>
                        </div>
                        <small style="color: #666;">#{len(st.session_state.notes) - i}</small>
                    </div>
                    <div style="white-space: pre-wrap; padding: 0.5rem 0; line-height: 1.6;">{note["content"]}</div>
                    <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                        <button onclick="alert('Редактирование пока в разработке')" style="background: none; border: none; cursor: pointer; color: #4e8cff;">✏️</button>
                        <button onclick="alert('Удаление пока в разработке')" style="background: none; border: none; cursor: pointer; color: #ff4e4e;">🗑</button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
