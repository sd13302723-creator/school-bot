# app/models/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    DIRECTOR = "director"
    DEPUTY = "deputy"          # Завуч (экспресс-замены за 5 секунд, контроль журналов)
    TEACHER = "teacher"        # Учитель (журнал за 10 секунд, фото-ДЗ с Offline-First)
    PARENT = "parent"          # Родитель (утренние статусы, чаты со скрытыми номерами)
    STUDENT = "student"        # Ученик (расписание, подготовка к ОРТ/НЦТ)
    SERVICE = "service"        # Школьные службы (вахта, столовая, секции)

class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"            # Бесплатный пробный период ( первые 30 дней )
    ACTIVE = "active"          # Платная подписка активна (ваш доход 77 сом/мес с пользователя)
    EXPIRED = "expired"        # Срок подписки истек

class User(Base):
    """Таблица пользователей (родители, учителя, завуч, директор, ученики)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи с профилями и подпиской
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    subscription = relationship("UserSubscription", back_populates="user", uselist=False)


class UserSubscription(Base):
    """Коммерческий модуль: персональная подписка каждого пользователя (77 сом/мес)"""
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)                  # Дата окончания триала или оплаченного месяца
    monthly_fee = Column(Float, default=77.00)                     # Фиксированная стоимость: 77 сом в месяц
    payment_bank_ref = Column(String(255), nullable=True)          # Чек/ID транзакции через MBANK, ЭЛКАР, QR, О!Деньги

    user = relationship("User", back_populates="subscription")


class TeacherProfile(Base):
    """Профиль учителя (предметы, классы)"""
    __tablename__ = "teacher_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(100), nullable=False)          # Например: Математика, Физика
    classes_assigned = Column(String(255), nullable=True)  # Закрепленные классы: 7-В, 8-Б

    user = relationship("User", back_populates="teacher_profile")


class StudentProfile(Base):
    """Профиль ученика (младшая/старшая школа, здоровье, доверенные лица)"""
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_name = Column(String(20), nullable=False, index=True)   # Класс, например: 1-А или 7-В
    parent_telegram_id = Column(Integer, nullable=True)         # Telegram ID родителя для связи и экстренных вызовов
    
    # Безопасность, медицина и логистика для младшей школы
    medical_notes = Column(Text, nullable=True)                 # Аллергии, особенности здоровья
    trusted_persons = Column(Text, nullable=True)               # Доверенные лица (ФИО + телефон бабушки/няни для забора)
    is_exempt_from_pe = Column(Boolean, default=False)          # Синий бейдж: Освобожден от физкультуры

    user = relationship("User", back_populates="student_profile")


class Schedule(Base):
    """Расписание уроков"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(20), nullable=False, index=True)
    lesson_number = Column(Integer, nullable=False)             # 1, 2, 3...
    subject = Column(String(100), nullable=False)
    teacher_name = Column(String(255), nullable=False)
    room = Column(String(50), nullable=False)                   # Кабинет (например, каб. 204)
    day_of_week = Column(String(20), nullable=False)            # Понедельник, Вторник...


class LessonReplacement(Base):
    """Таблица экспресс-замен завуча за 5 секунд"""
    __tablename__ = "lesson_replacements"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    class_name = Column(String(20), nullable=False)
    lesson_number = Column(Integer, nullable=False)
    original_subject = Column(String(100), nullable=False)
    replacement_subject = Column(String(100), nullable=True)
    replacement_teacher = Column(String(255), nullable=True)
    is_cancelled = Column(Boolean, default=False)               # Флаг отмены урока


class JournalEntry(Base):
    """Электронный журнал и дневник (с поддержкой Offline-First кэширования)"""
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    subject = Column(String(100), nullable=False)
    
    grade = Column(String(10), nullable=True)                   # Оценки: 2, 3, 4, 5
    attendance_status = Column(String(20), default="PRESENT")   # PRESENT (🟢), LATE (🟡), ABSENT (🔴), EXCUSED (🔵 Болеет)
    
    homework_text = Column(Text, nullable=True)
    homework_photo_url = Column(String(500), nullable=True)
    is_synced_offline = Column(Boolean, default=True)           # Флаг работы без интернета


class SchoolSummaryLog(Base):
    """Школьная сводка для директора (главные итоги дня простыми словами)"""
    __tablename__ = "school_summary_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    total_students = Column(Integer, default=0)
    present_students = Column(Integer, default=0)
    absent_students = Column(Integer, default=0)
    active_replacements_count = Column(Integer, default=0)
    journal_warnings = Column(Text, nullable=True)              # Предупреждения о незаполненных журналах


class SecureChatMapping(Base):
    """Безопасность: скрытие номеров телефонов в чатах и тревожные GSM-кнопки"""
    __tablename__ = "secure_chat_mappings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    masked_phone_alias = Column(String(100), nullable=False)     # Скрытый ID для защиты личных данных
    is_emergency_button_active = Column(Boolean, default=True)  # Доступ к прямой экстренной связи


class PsychologicalQuote(Base):
    """Психологическая поддержка и мотивационные цитаты для родителей и руководства"""
    __tablename__ = "psychological_quotes"

    id = Column(Integer, primary_key=True, index=True)
    target_role = Column(String(50), nullable=False)            # parent, director, teacher
    quote_text = Column(Text, nullable=False)                   # Например: «Ваш ребёнок — будущий гений! Вы замечательные родители!»
