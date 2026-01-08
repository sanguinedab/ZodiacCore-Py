from contextlib import contextmanager

from sqlmodel import SQLModel, Session, create_engine


@contextmanager
def managed_db_session(url, connect_args=None):
    """管理数据库会话的生命周期"""
    extras = dict(connect_args=connect_args) if connect_args else {}
    engine = create_engine(url, **extras)

    try:
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            yield engine, session
    finally:
        engine.dispose()
