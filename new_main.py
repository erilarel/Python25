"""
@file
@brief Веб-приложение Streamlit для ведения дневника эмоций с аналитикой.
@details
Позволяет создавать текстовые и аудиозаписи с автоматическим определением эмоции, просматривать и редактировать историю записей, а также проводить статистический анализ по эмоциям.
"""

import asyncio
from datetime import datetime, timezone
import pytz

import streamlit as st
import pandas as pd
import altair as alt

from scripts.voice_nika import VoiceToTextConverter
from scripts.emotion_class import EmotionDetector
from db.session import AsyncSessionLocal, init_db
from db.crud import NoteRepository

#: @brief Словарь соответствия эмоций и эмодзи/картинок.
name2smile = {
  "joy": ["😊", "src/joy.jpg"],
  "interest": ["🤔", "src/interest.jpg"],
  "surpise": ["😲", "src/surprised.jpg"],
  "sadness": ["😢", "src/sadness.jpg"],
  "anger": ["😡", "src/angry1.jpg"],
  "disgust": ["🤢", "src/disgust.jpg"],
  "fear": ["😨", "src/fear.jpg"],
  "guilt": ["😔", "src/guilt.jpg"],
  "neutral": ["😐", "src/norm1.jpg"]
}

# Эксперементальная функция цветов
def get_emotion_color(emotion: str) -> str:
    colors = {
        "anger": "#ff5252, #d32f2f",
        "disgust": "#8bc34a, #689f38",
        "joy": "#ffeb3b, #fbc02d",
        "neutral": "#bdbdbd, #757575",
        "sadness": "#64b5f6, #1976d2"
    }
    return colors.get(emotion, "#bdbdbd, #757575")

@st.cache_resource(show_spinner="Подготовка базы данных…")
def _prepare_database():
    """
    @brief Инициализация базы данных.
    @details
    Создаёт все таблицы в базе данных, если их ещё нет (через init_db).
    """
    asyncio.run(init_db())

def _run(coro):
    """
    @brief Запускает асинхронную корутину из синхронного контекста.
    @param coro Корутинная функция.
    @return Результат выполнения корутины.
    """
    return asyncio.run(coro)

def add_note(**fields):
    """
    @brief Добавляет новую заметку в базу данных.
    @param fields Аргументы для заметки (text, emotion и т.д.)
    @return Словарь с созданной заметкой (NoteDTO).
    """
    async def _add():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            return await repo.add(**fields, as_dict=True)
    return _run(_add())

def update_note(note_id: int, new_text: str, emotion: str):
    """
    @brief Обновляет текст и эмоцию заметки.
    @param note_id ID заметки.
    @param new_text Новый текст.
    @param emotion Новая эмоция.
    @return Обновлённая заметка (NoteDTO).
    """
    async def _upd():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            return await repo.update(note_id, text=new_text, emotion=emotion, as_dict=True)
    return _run(_upd())

def delete_note(note_id: int):
    """
    @brief Удаляет заметку по ID.
    @param note_id ID заметки.
    """
    async def _del():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            await repo.delete(note_id)
    _run(_del())

def list_notes(limit: int = 100):
    """
    @brief Получает список заметок.
    @param limit Максимальное число заметок.
    @return Список заметок (NoteDTO).
    """
    async def _list():
        async with AsyncSessionLocal() as session:
            repo = NoteRepository(session)
            return await repo.list(limit=limit, as_dict=True)
    return _run(_list())

# ----------------- UI (Streamlit) -----------------
_prepare_database()

st.set_page_config(
    layout="wide",
    page_title="Личный дневник с эмоциональной окраской текста",
    page_icon="📔",
)

st.markdown(
    """
    <style>
        [data-testid="stHorizontalBlock"] { align-items: flex-start; gap: 2rem; }
        .left-panel { width: 40%; }
        .right-panel { width: 60%; max-height: 80vh; overflow-y: auto; padding-right: 1rem; }
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

st.markdown(
    '<h1 class="main-title">Личный дневник с эмоциональной окраской текста</h1>',
    unsafe_allow_html=True
)
st.markdown("---")


# ----------------- Session state init -----------------
if 'notes' not in st.session_state:
    st.session_state.notes = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'input_mode' not in st.session_state:
    st.session_state.input_mode = "text"
if "voice_converter" not in st.session_state:
    st.session_state.voice_converter = VoiceToTextConverter()
if "e_detector" not in st.session_state:
    st.session_state.e_detector = EmotionDetector()
if "recognized_text" not in st.session_state:
    st.session_state.recognized_text = ""
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "editing_note_id" not in st.session_state:
    st.session_state.editing_note_id = None

# ---- Навигация страниц ----
st.sidebar.title("Навигация")
page = st.sidebar.radio("Выберите страницу", ["Дневник", "Аналитика"])


# ----------------- Основные разделы приложения -----------------
if page == "Дневник":
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
                    st.session_state.voice_converter = VoiceToTextConverter()  # дважды инициализируем
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
                                    st.session_state.recognized_text = st.session_state.voice_converter.audio_to_text(
                                        audio_data)
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
                # disp = datetime.fromisoformat(note["created_at"]).strftime("%d.%m.%Y %H:%M")

                moscow_tz = pytz.timezone('Europe/Moscow')
                created_at = datetime.fromisoformat(note["created_at"]).replace(tzinfo=timezone.utc)
                disp = created_at.astimezone(moscow_tz).strftime("%d.%m.%Y %H:%M")

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
                    # st.image(name2smile[note.get('emotion', '😊')][1], width=800)
                    # st.markdown(
                    #     f"""
                    #                <div class=\"note-card\">
                    #                  <div style=\"display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;\">
                    #                    <div style=\"display:flex;align-items:center;gap:0.5rem;\">
                    #                      <span style=\"font-size:1.5rem;\">{name2smile[note.get('emotion', '😊')][0]}</span>
                    #                      <h4 style=\"margin:0;\">Запись от {disp}</h4>
                    #                    </div>
                    #                    <small style=\"color:#666;\">#ID {nid}</small>
                    #                  </div>
                    #                  <div style=\"white-space:pre-wrap;padding:0.5rem 0;line-height:1.6;\">{note['text']}</div>
                    #                </div>
                    #                """,
                    #     unsafe_allow_html=True,
                    # )

                    current_emotion = note.get('emotion', 'neutral')
                    emotion_emoji = name2smile[current_emotion][0]
                    image_path = name2smile[current_emotion][1]

                    # Изображение-шапка с динамической шириной
                    st.image(
                        image_path,
                        use_container_width=True,
                        output_format='PNG'
                    )

                    # Карточка записи с оригинальным расположением смайла
                    st.markdown(
                        f"""
                        <div class="note-card">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
                                <div style="display:flex;align-items:center;gap:0.5rem;">
                                    <span style="font-size:1.8rem;">{emotion_emoji}</span>
                                    <h4 style="margin:0;">Запись от {disp}</h4>
                                </div>
                                <small style="color:#666;">#ID {nid}</small>
                            </div>
                            <div style="white-space:pre-wrap;padding:0.5rem 0;line-height:1.6;">{note['text']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
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


if page == "Аналитика":
    st.header("Аналитика заметок")
    notes = list_notes(limit=10000)
    if not notes:
        st.info("Нет заметок для анализа")
    else:
        df = pd.DataFrame(notes)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        df['hour'] = df['created_at'].dt.hour
        try:
            df['weekday'] = df['created_at'].dt.day_name(locale='ru_RU')
        except Exception:
            df['weekday'] = df['created_at'].dt.day_name()

        # 1. Распределение эмоций
        counts = df['emotion'].value_counts().rename_axis('emotion').reset_index(name='count')
        pie = alt.Chart(counts).mark_arc(innerRadius=50).encode(
            theta='count:Q', color='emotion:N', tooltip=['emotion', 'count']
        )
        st.subheader("Распределение эмоций")
        st.altair_chart(pie, use_container_width=True)

        # 2. Эмоции по дням недели
        st.subheader("Эмоции по дням недели")
        week_counts = df.groupby(['weekday', 'emotion']).size().reset_index(name='count')
        heat = alt.Chart(week_counts).mark_rect().encode(
            x=alt.X('weekday:N',
                    sort=['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']),
            y=alt.Y('emotion:N'),
            color='count:Q',
            tooltip=['weekday', 'emotion', 'count']
        )
        st.altair_chart(heat, use_container_width=True)

        # 3. Тренд количества записей и скользящее среднее (7 дней)
        daily = df.groupby('date').size().reset_index(name='count')
        daily['rolling'] = daily['count'].rolling(7, min_periods=1).mean()
        st.subheader("Тренд записей")
        line = alt.Chart(daily).mark_line(point=True).encode(
            x=alt.X('date:T', title='Дата'),
            y='count:Q',
            tooltip=['date', 'count']
        )
        roll = alt.Chart(daily).mark_line(strokeDash=[4, 2]).encode(
            x='date:T', y='rolling:Q', tooltip=['date', 'rolling']
        )
        st.altair_chart((line + roll), use_container_width=True)

        # 4. Боксплот длины текста по эмоциям
        st.subheader("Длина заметок по эмоциям")
        df['text_len'] = df['text'].str.len()
        box = alt.Chart(df).mark_boxplot().encode(
            x='emotion:N', y='text_len:Q', color='emotion:N', tooltip=['emotion', 'text_len']
        )
        st.altair_chart(box, use_container_width=True)

        # 5. Распределение по времени суток
        st.subheader("Распределение по часам")
        hour_counts = df['hour'].value_counts().sort_index().reset_index(name='count').rename(columns={'index': 'hour'})
        hist = alt.Chart(hour_counts).mark_bar().encode(
            x=alt.X('hour:O', title='Час суток'), y='count:Q', tooltip=['hour', 'count']
        )
        st.altair_chart(hist, use_container_width=True)

        # 6. Общая статистика
        st.subheader("Общая статистика")
        most_common = counts.loc[counts['count'].idxmax(), 'emotion']
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Всего записей", df.shape[0])
        col2.metric("Уникальных эмоций", df['emotion'].nunique())
        col3.metric("Чаще всего", most_common)
        col4.metric("Средняя длина", f"{df['text_len'].mean():.1f} символов")
