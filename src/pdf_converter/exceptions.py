"""Domain exceptions raised by :mod:`pdf_converter`."""


class PDFConverterError(Exception):
    """Base class for errors that the command-line interface can report cleanly."""


class ExtractionError(PDFConverterError):
    """Raised when a PDF backend cannot extract text."""


class UnknownExtractorError(PDFConverterError, ValueError):
    """Raised when an unsupported extraction backend is requested."""


class OutputWriteError(PDFConverterError):
    """Raised when converted content cannot be written."""


class PDFMoveError(PDFConverterError):
    """Raised when the source PDF cannot be moved."""
