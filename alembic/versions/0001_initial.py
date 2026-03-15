"""initial

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums — one op.execute per DO block (asyncpg forbids multiple commands)
    op.execute("DO $$ BEGIN CREATE TYPE materialstatus AS ENUM ('uploaded','parsing','parsed','normalizing','normalized','extracting','topics_extracted','ready','failed'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE inputtype AS ENUM ('image','audio','text'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE subjecttype AS ENUM ('math','physics','chemistry','biology','programming','language','other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE tasktype AS ENUM ('flash','exercise'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE reviewverdict AS ENUM ('correct','incorrect','partial'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE TYPE progresslevel AS ENUM ('unknown','weak','learning','good','mastered'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # users
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            username VARCHAR(255),
            full_name VARCHAR(512),
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_telegram_id ON users (telegram_id)")

    # study_materials
    op.execute("""
        CREATE TABLE IF NOT EXISTS study_materials (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(512),
            status materialstatus NOT NULL,
            raw_text TEXT,
            normalized_text TEXT,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
    """)

    # material_assets
    op.execute("""
        CREATE TABLE IF NOT EXISTS material_assets (
            id UUID PRIMARY KEY,
            material_id UUID NOT NULL REFERENCES study_materials(id) ON DELETE CASCADE,
            input_type inputtype NOT NULL,
            file_path VARCHAR(1024),
            telegram_file_id VARCHAR(512),
            extracted_text TEXT,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)

    # topics
    op.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id UUID PRIMARY KEY,
            material_id UUID NOT NULL REFERENCES study_materials(id) ON DELETE CASCADE,
            name VARCHAR(512) NOT NULL,
            text TEXT NOT NULL,
            subject subjecttype NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)

    # topic_chunks
    op.execute("""
        CREATE TABLE IF NOT EXISTS topic_chunks (
            id UUID PRIMARY KEY,
            topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
            material_id UUID NOT NULL REFERENCES study_materials(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            char_start INTEGER NOT NULL,
            char_end INTEGER NOT NULL,
            source_asset_id UUID,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)

    # tutor_tasks
    op.execute("""
        CREATE TABLE IF NOT EXISTS tutor_tasks (
            id UUID PRIMARY KEY,
            topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type tasktype NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            explanation TEXT,
            difficulty INTEGER NOT NULL,
            hints JSONB NOT NULL DEFAULT '[]',
            created_at TIMESTAMPTZ NOT NULL
        )
    """)

    # review_logs
    op.execute("""
        CREATE TABLE IF NOT EXISTS review_logs (
            id UUID PRIMARY KEY,
            task_id UUID NOT NULL REFERENCES tutor_tasks(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            user_answer TEXT NOT NULL,
            verdict reviewverdict NOT NULL,
            score FLOAT NOT NULL,
            feedback TEXT,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)

    # user_topic_progress
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_topic_progress (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
            level progresslevel NOT NULL DEFAULT 'unknown',
            total_attempts INTEGER NOT NULL DEFAULT 0,
            correct_attempts INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ NOT NULL
        )
    """)

    # repetition_states
    op.execute("""
        CREATE TABLE IF NOT EXISTS repetition_states (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
            interval_days FLOAT NOT NULL DEFAULT 1.0,
            ease_factor FLOAT NOT NULL DEFAULT 2.5,
            next_review_at TIMESTAMPTZ NOT NULL,
            last_reviewed_at TIMESTAMPTZ,
            review_count INTEGER NOT NULL DEFAULT 0
        )
    """)

    # gamification_profiles
    op.execute("""
        CREATE TABLE IF NOT EXISTS gamification_profiles (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            xp INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            streak_days INTEGER NOT NULL DEFAULT 0,
            last_activity_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gamification_profiles")
    op.execute("DROP TABLE IF EXISTS repetition_states")
    op.execute("DROP TABLE IF EXISTS user_topic_progress")
    op.execute("DROP TABLE IF EXISTS review_logs")
    op.execute("DROP TABLE IF EXISTS tutor_tasks")
    op.execute("DROP TABLE IF EXISTS topic_chunks")
    op.execute("DROP TABLE IF EXISTS topics")
    op.execute("DROP TABLE IF EXISTS material_assets")
    op.execute("DROP TABLE IF EXISTS study_materials")
    op.execute("DROP TABLE IF EXISTS users")

    op.execute("DROP TYPE IF EXISTS progresslevel")
    op.execute("DROP TYPE IF EXISTS reviewverdict")
    op.execute("DROP TYPE IF EXISTS tasktype")
    op.execute("DROP TYPE IF EXISTS subjecttype")
    op.execute("DROP TYPE IF EXISTS inputtype")
    op.execute("DROP TYPE IF EXISTS materialstatus")
