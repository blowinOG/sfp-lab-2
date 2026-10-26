import uuid

from ariadne import MutationType, ObjectType, QueryType, convert_kwargs_to_snake_case
from graphql import GraphQLError
from sqlalchemy.orm import Session

from app.audit.service import write_event
from app.core.jwt import create_access_token
from app.core.passwords import (
    WeakPasswordError,
    hash_password,
    validate_policy,
)
from app.models.audit_event import AuditEvent
from app.models.oauth_client import OAuthClient
from app.models.user import User

query = QueryType()
mutation = MutationType()

user_type = ObjectType("User")
client_type = ObjectType("Client")
audit_event_type = ObjectType("AuditEvent")


# --- Полевые резолверы (snake_case -> camelCase) ---

@user_type.field("isActive")
def _user_is_active(obj: User, _info) -> bool:
    return obj.is_active


@user_type.field("isAdmin")
def _user_is_admin(obj: User, _info) -> bool:
    return obj.is_admin


@user_type.field("createdAt")
def _user_created_at(obj: User, _info) -> str:
    return obj.created_at.isoformat()


@client_type.field("clientId")
def _client_client_id(obj: OAuthClient, _info) -> str:
    return obj.client_id


@client_type.field("isConfidential")
def _client_is_confidential(obj: OAuthClient, _info) -> bool:
    return obj.is_confidential


@client_type.field("redirectUris")
def _client_redirect_uris(obj: OAuthClient, _info) -> list[str]:
    return list(obj.redirect_uris or [])


@client_type.field("createdAt")
def _client_created_at(obj: OAuthClient, _info) -> str:
    return obj.created_at.isoformat()


@audit_event_type.field("eventType")
def _audit_event_type(obj: AuditEvent, _info) -> str:
    return obj.event_type


@audit_event_type.field("actorId")
def _audit_actor_id(obj: AuditEvent, _info):
    return obj.actor_id


@audit_event_type.field("clientId")
def _audit_client_id(obj: AuditEvent, _info):
    return obj.client_id


@audit_event_type.field("userAgent")
def _audit_user_agent(obj: AuditEvent, _info):
    return obj.user_agent


@audit_event_type.field("metadata")
def _audit_metadata(obj: AuditEvent, _info) -> dict:
    return obj.metadata_json or {}


@audit_event_type.field("createdAt")
def _audit_created_at(obj: AuditEvent, _info) -> str:
    return obj.created_at.isoformat()


# --- Query ---

@query.field("me")
def resolve_me(_obj, info):
    user = info.context.get("user")
    if user is None:
        raise GraphQLError("Authentication required")
    return user


@query.field("users")
@convert_kwargs_to_snake_case
def resolve_users(_obj, info, search=None, limit=50, offset=0):
    db: Session = info.context["db"]
    q = db.query(User)
    if search:
        q = q.filter(User.email.ilike(f"%{search}%"))
    return q.order_by(User.id.asc()).offset(offset).limit(limit).all()


@query.field("clients")
def resolve_clients(_obj, info):
    db: Session = info.context["db"]
    return db.query(OAuthClient).order_by(OAuthClient.id.asc()).all()


@query.field("auditEvents")
@convert_kwargs_to_snake_case
def resolve_audit_events(_obj, info, event_type=None, limit=50, offset=0):
    db: Session = info.context["db"]
    q = db.query(AuditEvent)
    if event_type:
        q = q.filter(AuditEvent.event_type == event_type)
    q = q.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
    return q.offset(offset).limit(limit).all()


# --- Mutation ---

@mutation.field("registerUser")
def resolve_register_user(_obj, info, email, password):
    db: Session = info.context["db"]
    if db.query(User).filter(User.email == email).first():
        raise GraphQLError("Email already registered")

    try:
        validate_policy(password, user_inputs=[email])
    except WeakPasswordError as exc:
        raise GraphQLError(str(exc))

    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    write_event(db, "user.created", actor_id=user.id, metadata={"email": user.email})
    return {"accessToken": create_access_token(sub=user.email), "tokenType": "bearer"}


@mutation.field("createClient")
@convert_kwargs_to_snake_case
def resolve_create_client(_obj, info, name, is_confidential=True):
    db: Session = info.context["db"]
    client = OAuthClient(
        client_id=str(uuid.uuid4()),
        name=name,
        is_confidential=is_confidential,
        redirect_uris=[],
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    actor = info.context.get("user")
    write_event(
        db, "client.created",
        actor_id=actor.id if actor else None,
        client_id=client.client_id,
        metadata={"name": client.name, "is_confidential": client.is_confidential},
    )
    return client


@mutation.field("disableUser")
@convert_kwargs_to_snake_case
def resolve_disable_user(_obj, info, user_id):
    db: Session = info.context["db"]
    target = db.query(User).filter(User.id == user_id).one_or_none()
    if target is None:
        raise GraphQLError("User not found")

    target.is_active = False
    db.commit()
    db.refresh(target)

    actor = info.context.get("user")
    write_event(db, "user.disabled", actor_id=actor.id if actor else None,
                metadata={"target_user_id": target.id, "target_email": target.email})
    return target