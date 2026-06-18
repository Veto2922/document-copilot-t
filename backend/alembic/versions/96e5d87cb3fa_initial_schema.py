"""initial_schema

Revision ID: 96e5d87cb3fa
Revises: 
Create Date: 2026-06-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '96e5d87cb3fa'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable Vector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # 2. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # 3. Create source_documents table
    op.create_table(
        'source_documents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ticker', sa.String(length=10), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('filing_type', sa.String(length=20), nullable=False),
        sa.Column('filing_date', sa.Date(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('accession_number', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('accession_number')
    )
    op.create_index('ix_source_documents_ticker', 'source_documents', ['ticker'], unique=False)
    
    # 4. Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_name', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            'search_vector', 
            postgresql.TSVECTOR(), 
            sa.Computed("to_tsvector('english', content)", persisted=True), 
            nullable=True
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['source_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'], unique=False)
    
    # 5. Create GIN index for search_vector and HNSW index for embedding vector
    op.create_index(
        'ix_document_chunks_search_vector',
        'document_chunks',
        ['search_vector'],
        unique=False,
        postgresql_using='gin'
    )
    op.create_index(
        'ix_document_chunks_embedding',
        'document_chunks',
        ['embedding'],
        unique=False,
        postgresql_using='hnsw',
        postgresql_ops={'embedding': 'vector_cosine_ops'}
    )
    
    # 6. Create chat_threads table
    op.create_table(
        'chat_threads',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_threads_user_id', 'chat_threads', ['user_id'], unique=False)
    
    # 7. Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('thread_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['chat_threads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_thread_id', 'chat_messages', ['thread_id'], unique=False)
    
    # 8. Create message_citations table
    op.create_table(
        'message_citations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.UUID(), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_message_citations_chunk_id', 'message_citations', ['chunk_id'], unique=False)
    op.create_index('ix_message_citations_message_id', 'message_citations', ['message_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_message_citations_message_id', table_name='message_citations')
    op.drop_index('ix_message_citations_chunk_id', table_name='message_citations')
    op.drop_table('message_citations')
    op.drop_index('ix_chat_messages_thread_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_index('ix_chat_threads_user_id', table_name='chat_threads')
    op.drop_table('chat_threads')
    op.drop_index('ix_document_chunks_embedding', table_name='document_chunks')
    op.drop_index('ix_document_chunks_search_vector', table_name='document_chunks')
    op.drop_index('ix_document_chunks_document_id', table_name='document_chunks')
    op.drop_table('document_chunks')
    op.drop_index('ix_source_documents_ticker', table_name='source_documents')
    op.drop_table('source_documents')
    op.drop_table('users')
    op.execute("DROP EXTENSION IF EXISTS vector;")
