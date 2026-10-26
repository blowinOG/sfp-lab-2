def gql(client, query, token=None, variables=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post("/graphql", json={"query": query, "variables": variables or {}}, headers=headers)


def test_me_requires_auth(client):
    r = gql(client, "{ me { email } }")
    body = r.json()
    assert body["errors"]
    assert "Authentication required" in body["errors"][0]["message"]


def test_users_requires_admin(client, registered_user):
    # Обычный пользователь -> «Admin only»
    r = gql(client, "{ users { id email } }", token=registered_user["token"])
    body = r.json()
    assert body.get("errors")
    assert "Admin only" in body["errors"][0]["message"]


def test_audit_login_success_written(client, registered_user):
    # Логинимся, затем читаем аудит через прямой доступ к БД через резолвер не выйдет —
    # но проверим через API /auth/login, а запись есть в БД. Проверим через GraphQL,
    # предварительно сделав пользователя админом вручную.
    import app.graphql.context as ctx
    from app.models.user import User

    db = ctx.SessionLocal()
    try:
        u = db.query(User).filter(User.email == registered_user["email"]).one()
        u.is_admin = True
        db.commit()
    finally:
        db.close()

    # Повторный логин, чтобы гарантированно был user.login.success
    client.post("/auth/login", json={"email": registered_user["email"], "password": registered_user["password"]})

    r = gql(client, '{ auditEvents(eventType: "user.login.success", limit: 10) { eventType } }',
            token=registered_user["token"])
    body = r.json()
    assert "errors" not in body, body
    assert len(body["data"]["auditEvents"]) >= 1