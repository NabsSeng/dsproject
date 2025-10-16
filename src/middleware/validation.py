"""
Request validation middleware and error classes.
"""

from marshmallow import Schema, fields, ValidationError as MarshmallowValidationError

class ValidationError(Exception):
    """Custom validation error exception."""
    pass

class AttachmentSchema(Schema):
    """Schema for attachment validation."""
    name = fields.Str(required=True)
    url = fields.Str(required=True, validate=lambda x: x.startswith('data:'))

class TaskBasedRequestSchema(Schema):
    """Schema for task-based code generation request validation."""
    email = fields.Email(required=True)
    secret = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    task = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    round = fields.Int(required=True, validate=lambda x: x > 0)
    nonce = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    brief = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    checks = fields.List(fields.Str(), required=True, validate=lambda x: len(x) > 0)
    evaluation_url = fields.Url(required=True)
    attachments = fields.List(fields.Nested(AttachmentSchema), required=False, missing=[])

class LegacyCodeGenerationRequestSchema(Schema):
    """Schema for legacy code generation request validation (backwards compatibility)."""
    instructions = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    tests = fields.List(fields.Dict(), required=True, validate=lambda x: len(x) > 0)
    repository_name = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    license = fields.Str(required=False, missing='mit', validate=lambda x: x.lower() in ['mit', 'apache', 'gpl'])
    github_token = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    language = fields.Str(required=False, missing='javascript', validate=lambda x: x.lower() in ['javascript', 'html'])
    framework = fields.Str(required=False, missing='vanilla', validate=lambda x: x.lower() in ['vanilla', 'react', 'vue'])

def validate_request(schema_class):
    """Decorator to validate request data using marshmallow schema."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request
            
            try:
                schema = schema_class()
                data = schema.load(request.get_json() or {})
                return func(data, *args, **kwargs)
            except MarshmallowValidationError as e:
                raise ValidationError(f"Validation error: {e.messages}")
            except Exception as e:
                raise ValidationError(f"Invalid request data: {str(e)}")
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator