from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    url: str
    key: str
    content_type: str
    size: int


class MediaDeleteResponse(BaseModel):
    message: str
