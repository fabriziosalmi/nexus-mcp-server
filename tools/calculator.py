# -*- coding: utf-8 -*-
# tools/calculator.py
import logging

def register_tools(mcp):
    """Registra i tool matematici con l'istanza del server MCP."""
    logging.info("=� Registrazione tool-set: Calcolatrice")

    @mcp.tool()
    def add(a: float, b: float) -> float:
        """
        Calcola la somma di due numeri (a + b).

        Args:
            a: Il primo addendo.
            b: Il secondo addendo.
        """
        return a + b

    @mcp.tool()
    def multiply(a: float, b: float) -> float:
        """
        Calcola il prodotto di due numeri (a * b).

        Args:
            a: Il primo fattore.
            b: Il secondo fattore.
        """
        return a * b