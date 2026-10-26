from ariadne import SchemaDirectiveVisitor
from graphql import GraphQLError


class IsAuthenticatedDirective(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        original = field.resolve
        if original is None:
            return field

        def wrapped(root, info, **kwargs):
            if info.context.get("user") is None:
                raise GraphQLError("Authentication required")
            return original(root, info, **kwargs)

        field.resolve = wrapped
        return field


class IsAdminDirective(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        original = field.resolve
        if original is None:
            return field

        def wrapped(root, info, **kwargs):
            user = info.context.get("user")
            if user is None:
                raise GraphQLError("Authentication required")
            if not user.is_admin:
                raise GraphQLError("Admin only")
            return original(root, info, **kwargs)

        field.resolve = wrapped
        return field