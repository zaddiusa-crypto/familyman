"""Initial multi-tenant schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE role_enum AS ENUM ('super_admin', 'lodge_admin', 'member')")
    op.execute("CREATE TYPE user_status_enum AS ENUM ('pending', 'approved', 'rejected', 'suspended')")
    op.execute("CREATE TYPE application_status_enum AS ENUM ('pending', 'approved', 'rejected')")
    op.execute("CREATE TYPE message_status_enum AS ENUM ('sent', 'delivered', 'read')")
    op.execute("CREATE TYPE media_type_enum AS ENUM ('image', 'video', 'document', 'voice')")
    op.execute("CREATE TYPE notification_priority_enum AS ENUM ('high', 'normal', 'low')")
    op.execute("CREATE TYPE payment_status_enum AS ENUM ('pending', 'completed', 'failed', 'refunded')")
    op.execute("CREATE TYPE sync_status_enum AS ENUM ('pending', 'processing', 'completed', 'failed')")

    # lodges table
    op.create_table(
        'lodges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('country', sa.String(2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='KES'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='Africa/Nairobi'),
        sa.Column('settings', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_lodges_code')
    )
    op.create_index('ix_lodges_code', 'lodges', ['code'], unique=True)

    # users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(30)),
        sa.Column('country_code', sa.String(5)),
        sa.Column('role', sa.Enum('super_admin', 'lodge_admin', 'member', name='role_enum'), nullable=False, server_default='member'),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'suspended', name='user_status_enum'), nullable=False, server_default='pending'),
        sa.Column('language', sa.String(5), nullable=False, server_default='en'),
        sa.Column('fcm_tokens', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
        sa.Column('telegram_chat_id', sa.String(50)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    op.create_index('ix_users_lodge_id', 'users', ['lodge_id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])

    # applications table
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('dob', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id_number', sa.String(50), nullable=False),
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('birth_town', sa.String(100), nullable=False),
        sa.Column('nickname', sa.String(50)),
        sa.Column('country', sa.String(2), nullable=False),
        sa.Column('phone', sa.String(30), nullable=False),
        sa.Column('business_type', sa.String(100)),
        sa.Column('business_location', sa.String(200)),
        sa.Column('nearest_lodge', sa.String(200), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='application_status_enum'), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('review_notes', sa.Text()),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_applications_lodge_status', 'applications', ['lodge_id', 'status'])

    # chats table
    op.create_table(
        'chats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('member_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True)),
        sa.Column('subject', sa.String(200)),
        sa.Column('last_message_at', sa.DateTime(timezone=True)),
        sa.Column('last_message_preview', sa.Text()),
        sa.Column('unread_admin', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unread_member', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chats_lodge_member', 'chats', ['lodge_id', 'member_id'])
    op.create_index('ix_chats_lodge_admin', 'chats', ['lodge_id', 'admin_id'], postgresql_where=sa.text('admin_id IS NOT NULL'))

    # messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('media_url', sa.String(500)),
        sa.Column('media_type', sa.Enum('image', 'video', 'document', 'voice', name='media_type_enum')),
        sa.Column('reply_to_id', postgresql.UUID(as_uuid=True)),
        sa.Column('status', sa.Enum('sent', 'delivered', 'read', name='message_status_enum'), nullable=False, server_default='sent'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_for', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reply_to_id'], ['messages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_chat_created', 'messages', ['chat_id', 'created_at'])
    op.create_index('ix_messages_lodge_sender', 'messages', ['lodge_id', 'sender_id'])

    # notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('priority', sa.Enum('high', 'normal', 'low', name='notification_priority_enum'), nullable=False, server_default='normal'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('sent_via', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'], postgresql_where=sa.text("is_read = false"))
    op.create_index('ix_notifications_lodge_created', 'notifications', ['lodge_id', 'created_at'])

    # announcements table
    op.create_table(
        'announcements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('media_urls', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),
        sa.Column('target_roles', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{"member"}'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_announcements_lodge_published', 'announcements', ['lodge_id', 'is_published'])

    # fee_schedules table
    op.create_table(
        'fee_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fee_schedules_lodge_active', 'fee_schedules', ['lodge_id', 'is_active'])

    # payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fee_schedule_id', postgresql.UUID(as_uuid=True)),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'refunded', name='payment_status_enum'), nullable=False, server_default='pending'),
        sa.Column('method', sa.String(30)),
        sa.Column('reference', sa.String(100)),
        sa.Column('paid_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fee_schedule_id'], ['fee_schedules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payments_lodge_user', 'payments', ['lodge_id', 'user_id'])

    # sync_outbox table
    op.create_table(
        'sync_outbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('table_name', sa.String(50), nullable=False),
        sa.Column('operation', sa.String(10), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('idempotency_key', sa.String(100), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='sync_status_enum'), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uq_sync_outbox_idempotency')
    )
    op.create_index('ix_outbox_status_created', 'sync_outbox', ['status', 'created_at'])

    # audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lodge_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('target_type', sa.String(50)),
        sa.Column('target_id', postgresql.UUID(as_uuid=True)),
        sa.Column('old_values', postgresql.JSONB()),
        sa.Column('new_values', postgresql.JSONB()),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lodge_id'], ['lodges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_lodge_created', 'audit_logs', ['lodge_id', 'created_at'])

    # Enable Row Level Security
    tables = [
        'users', 'applications', 'chats', 'messages', 'notifications',
        'announcements', 'fee_schedules', 'payments', 'sync_outbox', 'audit_logs'
    ]
    for table in tables:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
        op.execute(f'''
            CREATE POLICY {table}_lodge_isolation ON {table}
            USING (lodge_id = current_setting('app.current_lodge_id')::uuid)
        ''')

    # Function to set tenant context
    op.execute("""
        CREATE OR REPLACE FUNCTION set_tenant_context(lodge_id uuid)
        RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_lodge_id', lodge_id::text, FALSE);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)


def downgrade() -> None:
    op.execute('DROP FUNCTION IF EXISTS set_tenant_context(uuid)')
    
    tables = [
        'audit_logs', 'sync_outbox', 'payments', 'fee_schedules',
        'announcements', 'notifications', 'messages', 'chats',
        'applications', 'users', 'lodges'
    ]
    for table in tables:
        op.execute(f'DROP POLICY IF EXISTS {table}_lodge_isolation ON {table}')
        op.execute(f'ALTER TABLE {table} DISABLE ROW LEVEL SECURITY')

    op.drop_table('audit_logs')
    op.drop_table('sync_outbox')
    op.drop_table('payments')
    op.drop_table('fee_schedules')
    op.drop_table('announcements')
    op.drop_table('notifications')
    op.drop_table('messages')
    op.drop_table('chats')
    op.drop_table('applications')
    op.drop_table('users')
    op.drop_table('lodges')

    op.execute("DROP TYPE IF EXISTS role_enum")
    op.execute("DROP TYPE IF EXISTS user_status_enum")
    op.execute("DROP TYPE IF EXISTS application_status_enum")
    op.execute("DROP TYPE IF EXISTS message_status_enum")
    op.execute("DROP TYPE IF EXISTS media_type_enum")
    op.execute("DROP TYPE IF EXISTS notification_priority_enum")
    op.execute("DROP TYPE IF EXISTS payment_status_enum")
    op.execute("DROP TYPE IF EXISTS sync_status_enum")