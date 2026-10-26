from pathlib import Path

from ariadne import ScalarType, load_schema_from_path, make_executable_schema
from ariadne.asgi import GraphQL

from app.graphql import resolvers
from app.graphql.context import get_context_value
from app.graphql.directives import IsAdminDirective, IsAuthenticatedDirective

BASE_DIR = Path(__file__).parent
type_defs = load_schema_from_path(str(BASE_DIR / "schema.graphql"))

# Кастомный скаляр JSON из SDL -> python dict/list
json_scalar = ScalarType("JSON")

json_scalar.set_serializer(lambda value, *_args: value)
json_scalar.set_value_parser(lambda value, *_args: value)
json_scalar.set_literal_parser(lambda ast, *_args: getattr(ast, "value", None))

schema = make_executable_schema(
    type_defs,
    resolvers.query,
    resolvers.mutation,
    resolvers.user_type,
    resolvers.client_type,
    resolvers.audit_event_type,
    json_scalar,
    directives={
        "isAuthenticated": IsAuthenticatedDirective,
        "isAdmin": IsAdminDirective,
    },
)

graphql_app = GraphQL(schema, context_value=get_context_value, debug=True)