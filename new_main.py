import streamlit as st
from datetime import datetime
import asyncio
from scripts.voice_nika import VoiceToTextConverter
from scripts.emotion_class import Emotion_detector
from db.session import AsyncSessionLocal, init_db
from db.crud import NoteRepository


@st.cache_resource(show_spinner="Подготовка базы данных…")
def _prepare_database():
    asyncio.run(init_db())

_prepare_database()


def _run(coro):
    return asyncio.run(coro)


def add_note(**fields):
    async def _add():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            return await repo.add(**fields, as_dict=True)
    return _run(_add())


def update_note(note_id: int, new_text: str, emotion:str):
    async def _upd():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            return await repo.update(note_id, text=new_text, emotion=emotion, as_dict=True)
    return _run(_upd())


def delete_note(note_id: int):
    async def _del():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            await repo.delete(note_id)
    _run(_del())


def list_notes(limit: int = 100):
    async def _list():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            return await repo.list(limit=limit, as_dict=True)
    return _run(_list())


st.set_page_config(
    layout="wide",
    page_title="Личный дневник с эмоциональной окраской текста",
    page_icon="📔",
)

st.markdown(
    """
<style>
    /* Основной макет */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-start;
        gap: 2rem;
    }
    /* Левая панель */
    .left-panel { width: 40%; }
    /* Правая панель */
    .right-panel { width: 60%; max-height: 80vh; overflow-y: auto; padding-right: 1rem; }
    /* Заметки */
    .note-card {
        background: #f8f9fa; border-radius: 10px; padding: 1.5rem;
        margin-bottom: 1.5rem; border-left: 4px solid #4e8cff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button { transition: all 0.2s; }
    .stButton>button:hover { transform: translateY(-2px); }
    .stTextArea textarea { min-height: 200px !important; }
    .main-title { color: #4e8cff !important; margin-bottom: 0.5rem !important; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<h1 class="main-title">Личный дневник с эмоциональной окраской текста</h1>', unsafe_allow_html=True)
st.markdown("---")

if 'notes' not in st.session_state:
    st.session_state.notes = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'input_mode' not in st.session_state:
    st.session_state.input_mode = "text"
if "voice_converter" not in st.session_state:
    st.session_state.voice_converter = VoiceToTextConverter()
if "e_detector" not in st.session_state:
    st.session_state.e_detector = Emotion_detector()
if "recognized_text" not in st.session_state:
    st.session_state.recognized_text = ""
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "editing_note_id" not in st.session_state:
    st.session_state.editing_note_id = None

name2smile = {
  "joy": ["😊", "src/joy.jpg"],
  "interest": ["🤔", "src/joy.jpg"],
  "surpise": ["😲", "src/joy.jpg"],
  "sadness": ["😢", "src/joy.jpg"],
  "anger": ["😡", "src/angry.jpg"],
  "disgust": ["🤢", "src/joy.jpg"],
  "fear": ["😨", "src/joy.jpg"],
  "guilt": ["😔", "src/joy.jpg"],
  "neutral": ["😐", "src/joy.jpg"]
}

col1, col2 = st.columns([0.4, 0.6], gap="large")

with col1:
    st.subheader("Формат записи")

    mode = st.selectbox(
        "Выберите тип записи:", ["✏️ Текст", "🎤 Аудио"], index=0, label_visibility="collapsed"
    )

    if mode == "✏️ Текст":
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
                use_container_width=True)
            
            if submitted and note_content.strip():
                emotion = st.session_state.e_detector.start(note_content)
                add_note(text=note_content, emotion=emotion, score=None, source="text", audio_path=None)
                st.rerun()

    else:
            if not st.session_state.get('is_recording', False):
                if st.button("🎤 Начать голосовую запись", use_container_width=True):
                    st.session_state.is_recording = True
                    st.session_state.voice_converter = VoiceToTextConverter() #дважды инициализируем
                    st.session_state.voice_converter.start_recording()
                    st.rerun()
            else:
                if st.button("⏹️ Остановить запись", type="primary", use_container_width=True):
                    st.session_state.voice_converter.stop_recording()
                    
                    with st.spinner("Обработка записи..."):
                        try:
                            audio_data = st.session_state.voice_converter.get_audio_data()
                            if audio_data is not None:
                                try:
                                    st.session_state.recognized_text = st.session_state.voice_converter.audio_to_text(audio_data)
                                    st.success("✅ Запись успешно распознана!")
                                except RuntimeError as e:
                                    st.error(f"❌ Ошибка: {str(e)}")
                            else:
                                st.warning("⚠️ Не удалось получить аудиоданные")
                        except Exception as e:
                            st.error(f"⛔ Ошибка обработки: {str(e)}")
                        finally:
                            st.session_state.is_recording = False
                            st.rerun()
                
                
                if st.session_state.get('is_recording', False):
                    st.warning("🎙️ Идёт запись... Говорите чётко в микрофон")
                    st.caption("Нажмите '⏹️ Остановить запись' когда закончите")
                
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
                        emotion = st.session_state.e_detector.start(note_content)
                        add_note(text=note_content, emotion=emotion, score=None, source="audio", audio_path=None)
                        st.session_state.recognized_text = ""
                        st.rerun()

with col2:
    st.subheader("История записей")
    notes = list_notes(limit=100)

    if not notes:
        st.info("Здесь будут появляться ваши записи")
    else:
        for note in notes:

            nid = note["id"]
            disp = datetime.fromisoformat(note["created_at"]).strftime("%d.%m.%Y %H:%M")

            
            if st.session_state.editing_note_id == nid:
                with st.form(f"edit_form_{nid}"):
                    edited_text = st.text_area("Редактировать заметку:", value=note['text'], height=150)
                    emotion = st.session_state.e_detector.start(edited_text)

                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Сохранить"):
                        update_note(nid, edited_text, emotion)
                        st.session_state.editing_note_id = None
                        st.rerun()
                    if c2.form_submit_button("Отмена"):
                        st.session_state.editing_note_id = None
                        st.rerun()
                st.markdown("---")
                continue

            with st.container():
                st.image(name2smile[note.get('emotion', '😊')][1], width=800)
                st.markdown(
                    f"""
                               <div class=\"note-card\">   
                                 <div style=\"display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;\">  
                                   <div style=\"display:flex;align-items:center;gap:0.5rem;\">  
                                     <span style=\"font-size:1.5rem;\">{name2smile[note.get('emotion', '😊')][0]}</span>  
                                     <h4 style=\"margin:0;\">Запись от {disp}</h4>  
                                   </div>  
                                   <small style=\"color:#666;\">#ID {nid}</small>  
                                 </div>  
                                 <div style=\"white-space:pre-wrap;padding:0.5rem 0;line-height:1.6;\">{note['text']}</div>  
                               </div>
                               """,
                    unsafe_allow_html=True,
                )
                edit_col, btn_col, empty = st.columns([0.1, 2.5, 0.1])
                with btn_col:
                    if st.button("🗑", key=f"del-{nid}"):
                        delete_note(nid)
                        st.rerun()
                with edit_col:
                    if st.button("✏️", key=f"edit-{nid}"):
                        st.session_state.editing_note_id = nid
                        st.rerun()
                st.markdown("---")

