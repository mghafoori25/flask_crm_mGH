"""
Marshmallow schemas for CRM REST API.
Defines validation and JSON serialization formats.
"""
from marshmallow import Schema, fields, validate


class PaginationQuerySchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))


class CustomerSchema(Schema):
    id = fields.Int(dump_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    email = fields.Email(required=True, validate=validate.Length(max=255))
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))


class CustomerUpdateSchema(Schema):
    first_name = fields.Str(validate=validate.Length(min=1, max=120))
    last_name = fields.Str(validate=validate.Length(min=1, max=120))
    email = fields.Email(validate=validate.Length(max=255))
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))


class OrderSchema(Schema):
    id = fields.Int(dump_only=True)
    customer_id = fields.Int(required=True)
    order_date = fields.Date(required=True)
    status = fields.Str(required=True, validate=validate.OneOf(["Offen", "Bezahlt", "Storniert"]))
    total_amount = fields.Float(required=True)


class OrderUpdateSchema(Schema):
    order_date = fields.Date()
    status = fields.Str(validate=validate.OneOf(["Offen", "Bezahlt", "Storniert"]))
    total_amount = fields.Float()


class ContactSchema(Schema):
    id = fields.Int(dump_only=True)
    customer_id = fields.Int(required=True)
    user_id = fields.Int(dump_only=True)  # kommt aus current_user
    channel = fields.Str(required=True, validate=validate.OneOf(["Telefon", "E-Mail", "Meeting", "Chat"]))
    subject = fields.Str(allow_none=True, validate=validate.Length(max=255))
    notes = fields.Str(allow_none=True)
    contact_time = fields.DateTime(dump_only=True)