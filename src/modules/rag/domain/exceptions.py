"""Custom domain exceptions for the RAG module."""


class RAGException(Exception):
    """Base exception for RAG errors."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class UnsupportedDocumentException(RAGException):
    """Raised when an uploaded file format is not supported."""
    pass


class DocumentParsingException(RAGException):
    """Raised when a document loader fails to parse file contents."""
    pass


class VectorStoreException(RAGException):
    """Raised when an operation on the vector store fails."""
    pass


class RerankerException(RAGException):
    """Raised when the reranking model fails to score results."""
    pass
