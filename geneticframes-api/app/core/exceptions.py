"""
Custom exceptions for GeneticFrames API
"""

class GeneticFramesException(Exception):
    """Base exception for GeneticFrames application"""
    pass


class SpeciesNotFoundError(GeneticFramesException):
    """Raised when a species cannot be found in the database or external API"""
    def __init__(self, species_name: str):
        self.species_name = species_name
        self.message = f"Species '{species_name}' not found."
        super().__init__(self.message)


class NCBIConnectionError(GeneticFramesException):
    """Raised when there is an issue connecting to NCBI services"""
    def __init__(self, details: str = ""):
        self.message = "Failed to connect to NCBI services."
        if details:
            self.message += f" Details: {details}"
        super().__init__(self.message)


class DNAParsingError(GeneticFramesException):
    """Raised when DNA sequence cannot be parsed or analyzed"""
    def __init__(self, details: str = ""):
        self.message = "Error parsing DNA sequence."
        if details:
            self.message += f" Details: {details}"
        super().__init__(self.message)
