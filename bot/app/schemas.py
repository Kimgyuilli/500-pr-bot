from pydantic import BaseModel


class ErrorReport(BaseModel):
    errorType: str
    errorMessage: str
    stackTrace: str
    requestUrl: str
    timestamp: str
