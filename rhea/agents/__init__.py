"""
Custom Academy agents for Rhea.

This package contains custom Academy agents that extend Rhea's capabilities
beyond Galaxy tools, including peptide design, protein analysis, and more.
"""

from .peptide_design import (
    ForwardFoldingAgent,
    InverseFoldingAgent,
    QualityControlAgent,
    AnalysisAgent,
    PeptideDesignCoordinator,
)

__all__ = [
    "ForwardFoldingAgent",
    "InverseFoldingAgent",
    "QualityControlAgent",
    "AnalysisAgent",
    "PeptideDesignCoordinator",
]

