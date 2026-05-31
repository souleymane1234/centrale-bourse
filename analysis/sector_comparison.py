"""Rétrocompatibilité : délègue au module de comparaison enrichi."""
from analysis.company_compare import build_compare_dashboard as build_sector_comparison

__all__ = ["build_sector_comparison"]
