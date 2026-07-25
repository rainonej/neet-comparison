"""Rank-to-seat allocation under national capacity accounting.

This is an accounting model: among a reference pool of appeared candidates, the top
``government_like_seats`` ranks get a government-like offer and the top
``government + private`` ranks get a private-like offer. Category/state quotas are
not fully modeled yet; TN medium associations enter via score shifts, not separate pools.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SeatCapacity:
    government_like_seats: int
    private_like_seats: int
    n_appeared: int

    @property
    def total_mbbs_seats(self) -> int:
        return self.government_like_seats + self.private_like_seats

    @property
    def government_cutoff_percentile(self) -> float:
        """Share of appeared who would receive a govt-like offer if ranked nationally."""
        return min(self.government_like_seats / max(self.n_appeared, 1), 1.0)

    @property
    def private_or_better_cutoff_percentile(self) -> float:
        return min(self.total_mbbs_seats / max(self.n_appeared, 1), 1.0)


@dataclass(frozen=True)
class OfferResult:
    government_offer: np.ndarray
    private_offer: np.ndarray
    any_mbbs_offer: np.ndarray
    accessible_seat: np.ndarray
    rank_percentile: np.ndarray


def capacity_from_config(config: dict) -> SeatCapacity:
    cap = config["nmc_capacity"]
    n = int(config["score_distribution"]["n_appeared"])
    return SeatCapacity(
        government_like_seats=int(cap["government_like_seats"]),
        private_like_seats=int(cap["private_like_seats"]),
        n_appeared=n,
    )


def allocate_offers(
    rank_percentile: np.ndarray,
    *,
    capacity: SeatCapacity,
    can_afford_private: bool | np.ndarray,
) -> OfferResult:
    """Allocate offers from rank percentiles (0 = best).

    ``rank_percentile`` is the fraction of the national pool strictly better
    (approximately). Offer if rank_percentile < cutoff share.
    """

    rp = np.asarray(rank_percentile, dtype=float)
    gov_cut = capacity.government_cutoff_percentile
    any_cut = capacity.private_or_better_cutoff_percentile
    government = rp < gov_cut
    private = (rp < any_cut) & ~government
    any_mbbs = government | private
    if isinstance(can_afford_private, (bool, np.bool_)):
        afford = np.full(rp.shape, bool(can_afford_private))
    else:
        afford = np.asarray(can_afford_private, dtype=bool)
    accessible = government | (private & afford)
    return OfferResult(
        government_offer=government,
        private_offer=private,
        any_mbbs_offer=any_mbbs,
        accessible_seat=accessible,
        rank_percentile=rp,
    )


def can_afford_private_fee(can_afford_flag: bool, config: dict) -> bool:
    fees = config["fees_inr_per_year"]
    tiers = config["household_resource_tiers_inr_per_year"]
    private_fee = float(fees["private_mbbs"])
    resources = (
        float(tiers["can_afford_private"]) if can_afford_flag else float(tiers["cannot_afford_private"])
    )
    return private_fee <= 0.5 * resources


__all__ = [
    "OfferResult",
    "SeatCapacity",
    "allocate_offers",
    "can_afford_private_fee",
    "capacity_from_config",
]
