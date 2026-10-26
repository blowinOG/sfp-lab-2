from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def write_event(
    db: Session,
    event_type: str,
    *,
    actor_id: int | None = None,
    client_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> AuditEvent:
    """Единая точка записи аудита. НИКОГДА не передавай сюда пароли/токены/хэши."""
    event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        client_id=client_id,
        ip=ip,
        user_agent=user_agent,
        metadata_json=metadata or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event