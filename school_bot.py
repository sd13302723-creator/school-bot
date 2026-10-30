# app/models/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    DIRECTOR = "director"          # Директор: Пульс школы, утренний дайджест в 08:30, генератор официальных PDF/Excel отчетов для ГОРОНО
    DEPUTY = "deputy"            # Завуч: Учителя и классы (занятость педагогов), экспресс-замена уроков за 5 секунд
    TEACHER = "teacher"          # Учитель: Журнал за 10 сек, мигающая красная кнопка экстренного вызова без интернета, фото-ДЗ (Offline-First)
    PARENT = "parent"            # Родитель: Утренние статусы логистики, медпрофиль, доверенные лица, чаты, нужды класса
    STUDENT = "student"          # Ученик: Расписание, ОРТ/НЦТ подготовка
    SERVICE = "service"          # Школьные службы: Столовая, спортивные секции и творческие кружки (танцы)

class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"              # Бесплатный пробный период (первые 30 дней)
    ACTIVE = "active"            # Платная подписка активна (77 сом/мес с пользователя)
    EXPIRED = "expired"          # Срок подписки истек

class User(Base):
    """Таблица пользователей (родители, учителя, завуч, директор, ученики, службы)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    subscription = relationship("UserSubscription", back_populates="user", uselist=False)

class UserSubscription(Base):
    """Коммерческий модуль: персональная подписка каждого пользователя (77 сом/мес после 30 дней триала)"""
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    monthly_fee = Column(Float, default=77.00)                     # 77 сом / мес
    payment_bank_ref = Column(String(255), nullable=True)          # Чек MBANK / ЭЛКАР / QR / О!Деньги

    user = relationship("User", back_populates="subscription")

class TeacherProfile(Base):
    """Профиль учителя (предметы, классы, персональный аватар)"""
    __tablename__ = "teacher_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(100), nullable=False)
    classes_assigned = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    user = relationship("User", back_populates="teacher_profile")

class StudentProfile(Base):
    """Профиль ученика: младшая/старшая школа, здоровье, доверенные лица, экстренная связь"""
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_name = Column(String(20), nullable=False, index=True)
    parent_phone = Column(String(20), nullable=False)             # Номер родителя для экстренной красной кнопки
    parent_telegram_id = Column(Integer, nullable=True)
    
    avatar_url = Column(String(500), nullable=True)                # Персональная аватарка ребенка с цитатой дня
    medical_notes = Column(Text, nullable=True)                 # Аллергии, особенности здоровья
    trusted_persons = Column(Text, nullable=True)               # Доверенные лица (ФИО + тел)
    is_exempt_from_pe = Column(Boolean, default=False)          # Синий бейдж: Освобожден от физкультуры
    is_emergency_button_active = Column(Boolean, default=True)  # Мигающая красная кнопка экстренного GSM-вызова без интернета

    user = relationship("User", back_populates="student_profile")

class Schedule(Base):
    """Расписание уроков"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(20), nullable=False, index=True)
    lesson_number = Column(Integer, nullable=False)
    subject = Column(String(100), nullable=False)
    teacher_name = Column(String(255), nullable=False)
    room = Column(String(50), nullable=False)
    day_of_week = Column(String(20), nullable=False)

class LessonReplacement(Base):
    """Экспресс-замена уроков за 5 секунд"""
    __tablename__ = "lesson_replacements"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    class_name = Column(String(20), nullable=False)
    lesson_number = Column(Integer, nullable=False)
    original_subject = Column(String(100), nullable=False)
    replacement_subject = Column(String(100), nullable=True)
    replacement_teacher = Column(String(255), nullable=True)
    is_cancelled = Column(Boolean, default=False)

class JournalEntry(Base):
    """Электронный журнал: оценки, посещаемость, фото-ДЗ с Offline-First"""
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    subject = Column(String(100), nullable=False)
    
    grade = Column(String(10), nullable=True)                     # Оценки: 2, 3, 4, 5
    attendance_status = Column(String(20), default="PRESENT")   # PRESENT, LATE, ABSENT, EXCUSED
    absence_reason = Column(String(100), nullable=True)           # «По болезни» или «По семейным обстоятельствам» (желтая отметка [ УБ ])
    
    homework_text = Column(Text, nullable=True)
    homework_photo_url = Column(String(500), nullable=True)
    is_synced_offline = Column(Boolean, default=True)           # Флаг локального кэширования (Offline-First)

class SchoolSummaryLog(Base):
    """Пульс школы / Утренний дайджест для директора в 08:30"""
    __tablename__ = "school_summary_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    total_students = Column(Integer, default=0)
    present_students = Column(Integer, default=0)
    absent_students = Column(Integer, default=0)
    active_replacements_count = Column(Integer, default=0)
    journal_warnings = Column(Text, nullable=True)                # Предупреждения по незаполненным журналам

class SecureChatMapping(Base):
    """Безопасные чаты, родительский комитет и скрытие номеров"""
    __tablename__ = "secure_chat_mappings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    masked_phone_alias = Column(String(100), nullable=False)     # Скрытие реальных телефонных номеров
    is_parent_committee = Column(Boolean, default=False)        # Флаг участника родительского комитета

class ClassNeeds(Base):
    """Нужды класса (сборы родительского комитета)"""
    __tablename__ = "class_needs"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(20), nullable=False, index=True)
    purpose = Column(String(255), nullable=False)                 # Цель (например, покупка учебных материалов)
    amount_per_student = Column(Float, nullable=False)            # Сумма с ученика
    total_collected = Column(Float, default=0.0)                  # Собрано
    total_target = Column(Float, nullable=False)                  # Всего требуется
    donors_count = Column(Integer, default=0)                     # Сколько сдали

class MonthlyPdfExportLog(Base):
    """Генератор официальных PDF/Excel отчетов для директора, завучей, учителей и ГОРОНО"""
    __tablename__ = "monthly_pdf_export_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_month = Column(String(20), nullable=False)
    report_type = Column(String(50), nullable=False)              # attendance, replacements, progress, girono_summary
    pdf_file_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
import time
import http.server
import socketserver
import os

# Простейший HTTP-сервер для удержания порта на Render
PORT = int(os.environ.get("PORT", 10000))
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(hotkey := f"Serving at port {PORT}")
    httpd.serve_forever()
    
