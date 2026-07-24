class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class ValidationError(Exception):
    pass


class IntegrationConfigError(Exception):
    pass


class ExternalServiceError(Exception):
    pass


class ExternalAuthError(ExternalServiceError):
    pass


class ExternalRateLimitError(ExternalServiceError):
    pass
