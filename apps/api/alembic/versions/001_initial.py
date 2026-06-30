"""create initial tables

Revision ID: initial
Revises:
Create Date: 2026-06-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(64), primary_key=True),
        sa.Column("nickname", sa.String(100)),
        sa.Column("phone", sa.String(30), unique=True, index=True),
        sa.Column("email", sa.String(100), unique=True, index=True),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("subscription_status", sa.String(30), server_default="free"),
        sa.Column("notification_email", sa.Boolean, server_default="true"),
        sa.Column("notification_browser", sa.Boolean, server_default="true"),
        sa.Column("email_verified", sa.Boolean, server_default="false"),
        sa.Column("dnd_start", sa.Time, nullable=True),
        sa.Column("dnd_end", sa.Time, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "parrots",
        sa.Column("parrot_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id")),
        sa.Column("name", sa.String(100)),
        sa.Column("species", sa.String(100)),
        sa.Column("age", sa.Integer),
        sa.Column("gender", sa.String(30)),
        sa.Column("weight", sa.DECIMAL(6, 2)),
        sa.Column("has_plucking_history", sa.Boolean, server_default="false"),
        sa.Column("has_night_fright_history", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "devices",
        sa.Column("device_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id")),
        sa.Column("device_type", sa.String(50)),
        sa.Column("device_name", sa.String(100)),
        sa.Column("status", sa.String(30), server_default="offline"),
        sa.Column("last_online_time", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "media_events",
        sa.Column("event_id", sa.String(64), primary_key=True),
        sa.Column("parrot_id", sa.String(64), sa.ForeignKey("parrots.parrot_id")),
        sa.Column("device_id", sa.String(64), sa.ForeignKey("devices.device_id")),
        sa.Column("event_time", sa.DateTime, index=True),
        sa.Column("event_type", sa.String(100)),
        sa.Column("media_type", sa.String(30)),
        sa.Column("audio_url", sa.Text),
        sa.Column("video_url", sa.Text),
        sa.Column("duration", sa.DECIMAL(8, 2)),
        sa.Column("confidence", sa.DECIMAL(5, 4)),
        sa.Column("is_abnormal", sa.Boolean, server_default="false"),
        sa.Column("risk_level", sa.String(30)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "user_feedback",
        sa.Column("feedback_id", sa.String(64), primary_key=True),
        sa.Column("event_id", sa.String(64), sa.ForeignKey("media_events.event_id")),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id")),
        sa.Column("feedback_type", sa.String(50)),
        sa.Column("feedback_label", sa.String(100)),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "behavior_daily_stats",
        sa.Column("stat_id", sa.String(64), primary_key=True),
        sa.Column("parrot_id", sa.String(64), sa.ForeignKey("parrots.parrot_id")),
        sa.Column("stat_date", sa.DateTime, index=True),
        sa.Column("chirp_count", sa.Integer, server_default="0"),
        sa.Column("scream_count", sa.Integer, server_default="0"),
        sa.Column("night_activity_count", sa.Integer, server_default="0"),
        sa.Column("active_minutes", sa.Integer, server_default="0"),
        sa.Column("quiet_minutes", sa.Integer, server_default="0"),
        sa.Column("abnormal_event_count", sa.Integer, server_default="0"),
        sa.Column("health_score", sa.Integer, server_default="100"),
    )

    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id"), index=True),
        sa.Column("notification_type", sa.String(50)),
        sa.Column("title", sa.String(200)),
        sa.Column("content", sa.Text),
        sa.Column("is_read", sa.Boolean, server_default="false"),
        sa.Column("related_parrot_id", sa.String(64), sa.ForeignKey("parrots.parrot_id"), nullable=True),
        sa.Column("related_event_id", sa.String(64), sa.ForeignKey("media_events.event_id"), nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column("read_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("token_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id"), index=True),
        sa.Column("token", sa.String(128), unique=True, index=True),
        sa.Column("email", sa.String(100)),
        sa.Column("expires_at", sa.DateTime),
        sa.Column("is_used", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("used_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "password_reset_rate_limits",
        sa.Column("limit_id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(100), index=True),
        sa.Column("request_time", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("password_reset_rate_limits")
    op.drop_table("password_reset_tokens")
    op.drop_table("notifications")
    op.drop_table("behavior_daily_stats")
    op.drop_table("user_feedback")
    op.drop_table("media_events")
    op.drop_table("devices")
    op.drop_table("parrots")
    op.drop_table("users")
