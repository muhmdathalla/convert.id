from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

@dataclass
class ConversionResult:
    success: bool
    output_path: Optional[Path]
    original_size: int
    converted_size: int
    format_from: str
    format_to: str
    message: str = ""
    extra: Optional[Dict[str, Any]] = None

    @property
    def compression_ratio(self) -> float:
        if self.original_size == 0 or self.converted_size == 0:
            return 0.0
        return (1.0 - (self.converted_size / self.original_size)) * 100.0


class BaseEngine(ABC):
    name: str = "BaseEngine"
    supported_inputs: List[str] = []
    supported_outputs: List[str] = []

    @abstractmethod
    def convert(self, input_path: Path, output_path: Path, **kwargs) -> ConversionResult:
        pass

    def can_handle(self, input_ext: str, output_ext: str) -> bool:
        inp = input_ext.lower().lstrip(".")
        out = output_ext.lower().lstrip(".")
        return (inp in self.supported_inputs) and (out in self.supported_outputs)
