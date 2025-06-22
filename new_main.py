import streamlit as st
from datetime import datetime
import asyncio
from scripts.voice_nika import VoiceToTextConverter

# ─────────────────── DB setup ───────────────────
from db.session import AsyncSessionLocal, init_db
from db.crud import NoteRepository


# Инициализируем базу один раз при первом запуске
@st.cache_resource(show_spinner="Подготовка базы данных…")
def _prepare_database():
    asyncio.run(init_db())

_prepare_database()

# ─────────────────── helpers ───────────────────

def _run(coro):
    """Безопасно запускаем async‑корутины из sync‑контекста Streamlit."""
    return asyncio.run(coro)


def add_note(**fields):
    async def _add():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            return await repo.add(**fields, as_dict=True)
    return _run(_add())


def update_note(note_id: int, new_text: str):
    async def _upd():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            return await repo.update(note_id, text=new_text, as_dict=True)
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

# ─────────────────── UI ───────────────────

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

# ──────────────── session_state ────────────────
if "voice_converter" not in st.session_state:
    st.session_state.voice_converter = VoiceToTextConverter()
if "recognized_text" not in st.session_state:
    st.session_state.recognized_text = ""
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
# Для редактирования
if "editing_note_id" not in st.session_state:
    st.session_state.editing_note_id = None

# ─────────────────── Заголовок ───────────────────
st.markdown(
    '<h1 class="main-title">Личный дневник с эмоциональной окраской текста</h1>',
    unsafe_allow_html=True,
)
st.markdown("---")

# ─────────────────── Основной контейнер ───────────────────
col1, col2 = st.columns([0.4, 0.6], gap="large")

with col1:
    st.subheader("Формат записи")

    mode = st.selectbox(
        "Выберите тип записи:", ["✏️ Текст", "🎤 Аудио"], index=0,
    )

    if mode == "✏️ Текст":
        with st.form("text_entry_form", clear_on_submit=True):
            note_content = st.text_area(
                "Ваша запись:", placeholder="Опишите свои мысли и чувства...", height=250
            )
            submitted = st.form_submit_button("📝 Создать заметку", type="primary", use_container_width=True)
            if submitted and note_content.strip():
                add_note(text=note_content, emotion="✏️", score=None, source="text", audio_path=None)
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
                    "Распознанный текст:", value=st.session_state.recognized_text, height=150
                )
                submitted = st.form_submit_button("📝 Создать заметку", type="primary", use_container_width=True)
                if submitted and note_content.strip():
                    add_note(text=note_content, emotion="🎤", score=None, source="voice", audio_path=None)
                    st.session_state.recognized_text = ""
                    st.rerun()

with col2:
    st.subheader("История записей")
    notes = list_notes(limit=100)

    if not notes:
        st.info("Здесь будут появляться ваши записи")
    else:
        for note in notes:  # новые сверху
            nid = note["id"]
            disp = datetime.fromisoformat(note["created_at"]).strftime("%d.%m.%Y %H:%M")

            # Если в режиме редактирования этой заметки
            if st.session_state.editing_note_id == nid:
                with st.form(f"edit_form_{nid}"):
                    edited = st.text_area("Редактировать заметку:", value=note['text'], height=150)
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Сохранить"):  # сохраняем
                        update_note(nid, edited)
                        st.session_state.editing_note_id = None
                        st.rerun()
                    if c2.form_submit_button("Отмена"):  # отменяем
                        st.session_state.editing_note_id = None
                        st.rerun()
                st.markdown("---")
                continue

            # Отображение карточки
            with st.container():
                st.markdown(
                    f"""
                    <div class=\"note-card\">   
                      <div style=\"display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;\">  
                        <div style=\"display:flex;align-items:center;gap:0.5rem;\">  
                          <span style=\"font-size:1.5rem;\">{note.get('emotion','😊')}</span>  
                          <h4 style=\"margin:0;\">Запись от {disp}</h4>  
                        </div>  
                        <small style=\"color:#666;\">#ID {nid}</small>  
                      </div>  
                      <div style=\"white-space:pre-wrap;padding:0.5rem 0;line-height:1.6;\">{note['text']}</div>  
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Кнопки действий
                edit_col, btn_col, empty = st.columns([0.1,2.5,0.1])
                with btn_col:
                    if st.button("🗑️", key=f"del-{nid}"):
                        delete_note(nid)
                        st.rerun()
                with edit_col:
                    if st.button("✏️", key=f"edit-{nid}"):
                        st.session_state.editing_note_id = nid
                        st.rerun()
                st.markdown("---")
