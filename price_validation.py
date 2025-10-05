#!/usr/bin/env python3
"""
Sistema di validazione prezzi con rilevamento anomalie
Identifica split azionari, errori di cambio, e variazioni sospette
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import math


class AnomalyType(Enum):
    """Tipi di anomalie rilevabili"""
    NORMAL = "normal"
    HIGH_VARIATION = "high_variation"  # >20% <50%
    CRITICAL_VARIATION = "critical_variation"  # >50%
    POTENTIAL_SPLIT = "potential_split"
    POTENTIAL_REVERSE_SPLIT = "potential_reverse_split"
    CURRENCY_MISMATCH = "currency_mismatch"
    ZERO_OR_NEGATIVE = "zero_or_negative"


@dataclass
class ValidationResult:
    """Risultato validazione prezzo"""
    is_valid: bool
    anomaly_type: AnomalyType
    variation_pct: float
    confidence: float  # 0.0 - 1.0
    message: str
    suggested_action: str
    split_ratio: Optional[Tuple[int, int]] = None  # (from, to) es. (1, 4) = 1:4 split


class PriceValidator:
    """
    Validatore prezzi con rilevamento anomalie intelligente

    Features:
    - Rilevamento variazioni anomale (>20%, >50%)
    - Identificazione split azionari comuni (1:2, 1:3, 1:4, 1:10)
    - Rilevamento errori cambio valuta
    - Suggerimenti azioni correttive
    """

    # Soglie configurabili
    WARNING_THRESHOLD = 20.0  # % - variazione che genera warning
    CRITICAL_THRESHOLD = 50.0  # % - variazione critica
    SPLIT_TOLERANCE = 0.15  # Tolleranza per match ratio split

    # Ratios split comuni
    COMMON_SPLITS = [
        (1, 2),   # 1:2 split
        (1, 3),   # 1:3 split
        (1, 4),   # 1:4 split
        (1, 5),   # 1:5 split
        (1, 10),  # 1:10 split
        (2, 1),   # 2:1 reverse split
        (3, 1),   # 3:1 reverse split
        (4, 1),   # 4:1 reverse split
        (5, 1),   # 5:1 reverse split
        (10, 1),  # 10:1 reverse split
    ]

    def validate_price_update(
        self,
        old_price: float,
        new_price: float,
        asset_name: str = "",
        currency_old: Optional[str] = None,
        currency_new: Optional[str] = None
    ) -> ValidationResult:
        """
        Valida un aggiornamento di prezzo e rileva anomalie

        Args:
            old_price: Prezzo precedente
            new_price: Nuovo prezzo
            asset_name: Nome asset (per logging)
            currency_old: Valuta vecchia
            currency_new: Valuta nuova

        Returns:
            ValidationResult con analisi completa
        """

        # Check prezzi zero o negativi
        if new_price <= 0:
            return ValidationResult(
                is_valid=False,
                anomaly_type=AnomalyType.ZERO_OR_NEGATIVE,
                variation_pct=0.0,
                confidence=1.0,
                message=f"Prezzo non valido: {new_price}",
                suggested_action="Verifica che il simbolo sia corretto e l'asset sia ancora quotato"
            )

        if old_price <= 0:
            # Primo inserimento, accetta qualsiasi valore positivo
            return ValidationResult(
                is_valid=True,
                anomaly_type=AnomalyType.NORMAL,
                variation_pct=0.0,
                confidence=1.0,
                message="Primo prezzo inserito",
                suggested_action="Nessuna azione necessaria"
            )

        # Calcola variazione percentuale
        variation_pct = ((new_price - old_price) / old_price) * 100
        abs_variation = abs(variation_pct)

        # Check cambio valuta
        if currency_old and currency_new and currency_old != currency_new:
            return ValidationResult(
                is_valid=False,
                anomaly_type=AnomalyType.CURRENCY_MISMATCH,
                variation_pct=variation_pct,
                confidence=1.0,
                message=f"Cambio valuta rilevato: {currency_old} → {currency_new}",
                suggested_action="Verifica che il provider non abbia cambiato valuta di quotazione. "
                                "Potrebbe essere necessario convertire manualmente."
            )

        # Check split azionari
        split_result = self._check_split_pattern(old_price, new_price)
        if split_result:
            anomaly_type, split_ratio, confidence, message = split_result
            return ValidationResult(
                is_valid=True,  # Split è valido ma richiede azione
                anomaly_type=anomaly_type,
                variation_pct=variation_pct,
                confidence=confidence,
                message=message,
                suggested_action="Verifica corporate actions su sito emittente. "
                                "Se confermato, aggiorna retroattivamente i record storici.",
                split_ratio=split_ratio
            )

        # Check variazioni critiche
        if abs_variation >= self.CRITICAL_THRESHOLD:
            return ValidationResult(
                is_valid=False,
                anomaly_type=AnomalyType.CRITICAL_VARIATION,
                variation_pct=variation_pct,
                confidence=0.9,
                message=f"Variazione critica: {variation_pct:+.2f}% "
                       f"({old_price:.2f} → {new_price:.2f})",
                suggested_action="VERIFICA OBBLIGATORIA: Controlla su Google Finance, "
                                "Bloomberg o sito emittente. Probabile errore dati o split."
            )

        # Check variazioni alte
        if abs_variation >= self.WARNING_THRESHOLD:
            return ValidationResult(
                is_valid=True,  # Accettabile ma sospetto
                anomaly_type=AnomalyType.HIGH_VARIATION,
                variation_pct=variation_pct,
                confidence=0.7,
                message=f"Variazione significativa: {variation_pct:+.2f}% "
                       f"({old_price:.2f} → {new_price:.2f})",
                suggested_action="Verifica consigliata su fonti esterne. "
                                "Potrebbe essere legittima (rally/crash) o errore."
            )

        # Variazione normale
        return ValidationResult(
            is_valid=True,
            anomaly_type=AnomalyType.NORMAL,
            variation_pct=variation_pct,
            confidence=1.0,
            message=f"Variazione normale: {variation_pct:+.2f}%",
            suggested_action="Nessuna azione necessaria"
        )

    def _check_split_pattern(
        self,
        old_price: float,
        new_price: float
    ) -> Optional[Tuple[AnomalyType, Tuple[int, int], float, str]]:
        """
        Verifica se il cambio prezzo corrisponde a uno split azionario

        Returns:
            (anomaly_type, split_ratio, confidence, message) o None
        """
        ratio = old_price / new_price

        # Check split comuni
        for from_val, to_val in self.COMMON_SPLITS:
            expected_ratio = from_val / to_val
            relative_error = abs(ratio - expected_ratio) / expected_ratio

            if relative_error <= self.SPLIT_TOLERANCE:
                is_reverse = to_val < from_val
                anomaly_type = (
                    AnomalyType.POTENTIAL_REVERSE_SPLIT if is_reverse
                    else AnomalyType.POTENTIAL_SPLIT
                )

                split_type = "reverse split" if is_reverse else "split"
                confidence = 1.0 - relative_error  # Più vicino = maggiore confidence

                message = (
                    f"Possibile {split_type} {from_val}:{to_val} rilevato "
                    f"(ratio {ratio:.2f}, atteso {expected_ratio:.2f})"
                )

                return (anomaly_type, (from_val, to_val), confidence, message)

        return None

    def batch_validate(
        self,
        price_updates: List[Dict[str, any]]
    ) -> List[ValidationResult]:
        """
        Valida un batch di aggiornamenti prezzi

        Args:
            price_updates: Lista di dict con chiavi:
                - id: ID asset
                - asset_name: Nome asset
                - old_price: Prezzo vecchio
                - new_price: Prezzo nuovo
                - currency_old: Valuta vecchia (opzionale)
                - currency_new: Valuta nuova (opzionale)

        Returns:
            Lista di ValidationResult
        """
        results = []

        for update in price_updates:
            result = self.validate_price_update(
                old_price=update['old_price'],
                new_price=update['new_price'],
                asset_name=update.get('asset_name', ''),
                currency_old=update.get('currency_old'),
                currency_new=update.get('currency_new')
            )
            results.append(result)

        return results

    def generate_report(
        self,
        results: List[ValidationResult],
        asset_names: Optional[List[str]] = None
    ) -> str:
        """
        Genera report testuale delle validazioni

        Args:
            results: Lista ValidationResult
            asset_names: Lista nomi asset (opzionale)

        Returns:
            Report formattato
        """
        if not results:
            return "Nessun aggiornamento da validare"

        lines = ["=" * 80]
        lines.append("📊 REPORT VALIDAZIONE PREZZI")
        lines.append("=" * 80)

        # Conteggi per tipo
        type_counts = {}
        for result in results:
            type_counts[result.anomaly_type] = type_counts.get(result.anomaly_type, 0) + 1

        lines.append(f"\nTotale aggiornamenti: {len(results)}")
        lines.append(f"  ✅ Normali: {type_counts.get(AnomalyType.NORMAL, 0)}")
        lines.append(f"  🟡 Warning: {type_counts.get(AnomalyType.HIGH_VARIATION, 0)}")
        lines.append(f"  🔴 Critici: {type_counts.get(AnomalyType.CRITICAL_VARIATION, 0)}")
        lines.append(f"  🔄 Split: {type_counts.get(AnomalyType.POTENTIAL_SPLIT, 0)}")
        lines.append(f"  ⚠️  Errori: {type_counts.get(AnomalyType.ZERO_OR_NEGATIVE, 0) + type_counts.get(AnomalyType.CURRENCY_MISMATCH, 0)}")

        # Dettagli anomalie
        anomalies = [r for r in results if r.anomaly_type != AnomalyType.NORMAL]

        if anomalies:
            lines.append("\n" + "=" * 80)
            lines.append("⚠️  ANOMALIE RILEVATE")
            lines.append("=" * 80)

            for i, result in enumerate(anomalies):
                asset = asset_names[i] if asset_names and i < len(asset_names) else f"Asset {i+1}"
                icon = self._get_icon(result.anomaly_type)

                lines.append(f"\n{icon} {asset}")
                lines.append(f"  Tipo: {result.anomaly_type.value}")
                lines.append(f"  Variazione: {result.variation_pct:+.2f}%")
                lines.append(f"  Confidence: {result.confidence*100:.0f}%")
                lines.append(f"  Messaggio: {result.message}")
                lines.append(f"  Azione: {result.suggested_action}")

                if result.split_ratio:
                    lines.append(f"  Split ratio: {result.split_ratio[0]}:{result.split_ratio[1]}")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)

    def _get_icon(self, anomaly_type: AnomalyType) -> str:
        """Restituisce emoji appropriata per tipo anomalia"""
        icons = {
            AnomalyType.NORMAL: "✅",
            AnomalyType.HIGH_VARIATION: "🟡",
            AnomalyType.CRITICAL_VARIATION: "🔴",
            AnomalyType.POTENTIAL_SPLIT: "🔄",
            AnomalyType.POTENTIAL_REVERSE_SPLIT: "🔄",
            AnomalyType.CURRENCY_MISMATCH: "💱",
            AnomalyType.ZERO_OR_NEGATIVE: "❌"
        }
        return icons.get(anomaly_type, "⚠️")


# Factory function
def create_validator(**kwargs) -> PriceValidator:
    """Crea un validatore con configurazione custom"""
    validator = PriceValidator()

    if 'warning_threshold' in kwargs:
        validator.WARNING_THRESHOLD = kwargs['warning_threshold']
    if 'critical_threshold' in kwargs:
        validator.CRITICAL_THRESHOLD = kwargs['critical_threshold']

    return validator


if __name__ == '__main__':
    # Test rapido
    validator = PriceValidator()

    test_cases = [
        {'old_price': 100.0, 'new_price': 110.0, 'asset_name': 'Normal +10%'},
        {'old_price': 100.0, 'new_price': 130.0, 'asset_name': 'High +30%'},
        {'old_price': 400.0, 'new_price': 100.0, 'asset_name': 'Split 1:4'},
        {'old_price': 100.0, 'new_price': 400.0, 'asset_name': 'Reverse 4:1'},
        {'old_price': 100.0, 'new_price': 250.0, 'asset_name': 'Critical +150%'},
    ]

    results = validator.batch_validate(test_cases)
    report = validator.generate_report(results, [tc['asset_name'] for tc in test_cases])
    print(report)
