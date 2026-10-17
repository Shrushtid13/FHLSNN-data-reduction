"""
FHLSNN / MFHLSNN / EFHLSNN unified classifier.

All segment endpoints are stored as NumPy matrices (m×n) for vectorised
distance/membership computation.  Per-segment Python loops in predict() are
not acceptable (PRD 4.1).

Paper references (all in /docs/papers):
  [2001] Kulkarni, Sontakke, Randale – IJCNN 2001  pp. 2918-2923
  [2003] Patil, Dhabe, Kulkarni, Sontakke – FUZZ-IEEE 2003  pp. 1418-1422
  [2014] Shinde & Kulkarni 2014
  [2017] Shinde & Kulkarni 2017 (EFHLSNN)

Issue flags (all default to "as printed"):
  issue_1_f_uses_x_gamma   – [2001] f uses x·γ instead of (x−l)·γ
  issue_2_mfhlsnn_f_zero   – [2003] f(y,γ) returns 0 when y·γ ≥ 1 instead of 1
  issue_3_mfhlsnn_h_line   – [2003] h = distance to infinite line (not segment)
  issue_4_midpoint_printed – [2014] midpoint printed as |(w−v)/2| instead of (v+w)/2
  issue_5_min_redundant    – [2014] min(l1+l2, l3) always == l3; keep the min as printed
  issue_7_t_divides_by_l   – [2017] t = Σ(x−v)(w−v)/l ; should divide by l² for t∈[0,1]

step4_intersection enum (PRD 4.1, issue 6):
  "skip"     – newly created point-segments are NOT intersection-tested [2017].
               **This is the default.** It never discards a training pattern.
  "swap_2014"– keep the new point segment even if it intersects (no-op resolve).
  "drop_new" – pop the newly created segment.  **Must not be used as default**
               because it discards training patterns.  Flag for guide review.

Tie-break / all-zero-membership rule (PRD 4.1):
  When all memberships equal zero (common when γ·distance ≥ 1) or when
  multiple segments tie, the one whose midpoint (V+W)/2 is nearest to R wins.
  The fraction of test patterns that hit the zero-membership path is stored
  in self._last_zero_mem_frac after each predict() call.
"""

import numpy as np
import time
from typing import Optional


def _grow_2d(arr: np.ndarray, new_cap: int) -> np.ndarray:
    out = np.empty((new_cap, arr.shape[1]), dtype=arr.dtype)
    out[:len(arr)] = arr
    return out


def _grow_1d(arr: np.ndarray, new_cap: int) -> np.ndarray:
    out = np.empty(new_cap, dtype=arr.dtype)
    out[:len(arr)] = arr
    return out


class FHLSNN:
    # ── construction ───────────────────────────────────────────────────────
    def __init__(
        self,
        zeta: float = 0.1,                      # segment-length bound (θ in [2003/2014])
        gamma: float = 1.0,                      # sensitivity parameter (γ)
        membership_type: str = 'fhlsnn2001',     # see module docstring
        use_intersection_test: bool = True,      # [2001] Table 2: often no effect
        collinearity_tol: float = 1e-5,          # PRD 4.1 issue 5; exposed as param
        step4_intersection: str = 'skip',        # enum: "skip" | "swap_2014" | "drop_new"
        issue_1_f_uses_x_gamma: bool = True,     # [2001] as printed
        issue_2_mfhlsnn_f_zero: bool = True,     # [2003] as printed
        issue_3_mfhlsnn_h_line: bool = True,     # [2003] as printed
        issue_4_midpoint_printed: bool = True,   # [2014] as printed
        issue_5_min_redundant: bool = True,      # [2014] as printed
        issue_7_t_divides_by_l: bool = True,     # [2017] as printed
        shuffle: bool = True,
        random_state: Optional[int] = None,
    ):
        allowed_s4 = {"skip", "swap_2014", "drop_new"}
        if step4_intersection not in allowed_s4:
            raise ValueError(f"step4_intersection must be one of {allowed_s4}")
        allowed_mt = {
            'fhlsnn2001', 'mfhlsnn2003_height',
            'mfhlsnn2014_midpoint', 'efhlsnn2017_segment',
        }
        if membership_type not in allowed_mt:
            raise ValueError(f"membership_type must be one of {allowed_mt}")

        self.zeta = zeta
        self.gamma = gamma
        self.membership_type = membership_type
        self.use_intersection_test = use_intersection_test
        self.collinearity_tol = collinearity_tol
        self.step4_intersection = step4_intersection
        self.issue_1_f_uses_x_gamma = issue_1_f_uses_x_gamma
        self.issue_2_mfhlsnn_f_zero = issue_2_mfhlsnn_f_zero
        self.issue_3_mfhlsnn_h_line = issue_3_mfhlsnn_h_line
        self.issue_4_midpoint_printed = issue_4_midpoint_printed
        self.issue_5_min_redundant = issue_5_min_redundant
        self.issue_7_t_divides_by_l = issue_7_t_divides_by_l
        self.shuffle = shuffle
        self.random_state = random_state

        # Learned state — reset in fit()
        self.segments_: list = []                # list of dicts {V, W, class}
        self.n_segments_: int = 0
        self._V: np.ndarray = np.empty((0, 1))  # (m, n) left endpoints
        self._W: np.ndarray = np.empty((0, 1))  # (m, n) right endpoints
        self._cls: np.ndarray = np.empty((0,), dtype=int)
        self._last_zero_mem_frac: float = 0.0
        self.inter_time_: float = 0.0

    # ── internal reset / rebuild ───────────────────────────────────────────

    def _reset(self):
        """Reset all learned state (sklearn contract: fit() is not incremental)."""
        self.segments_ = []
        self.n_segments_ = 0
        self._V = np.empty((0, 1))
        self._W = np.empty((0, 1))
        self._cls = np.empty((0,), dtype=int)
        self._last_zero_mem_frac = 0.0
        self.inter_time_ = 0.0

    def _rebuild_matrices(self):
        """Sync list-of-dicts → matrix arrays after fit, for vectorised predict."""
        if not self.segments_:
            return
        self._V   = np.array([s['V'] for s in self.segments_])   # (m, n)
        self._W   = np.array([s['W'] for s in self.segments_])
        self._cls = np.array([s['class'] for s in self.segments_], dtype=int)

    # ── scalar membership helpers (used only during fit for single patterns) ─

    def _f2001(self, x: float, l: float) -> float:
        """f() as defined in [2001].

        Issue 1: paper prints x·γ; alternative (x−l)·γ gives f=0 iff x=l.
        When x == l the pattern lies exactly on the segment → f must be 0.
        """
        if abs(x - l) < self.collinearity_tol:   # x == l → R on segment
            return 0.0
        val = (x * self.gamma) if self.issue_1_f_uses_x_gamma else ((x - l) * self.gamma)
        return float(np.clip(val, 0.0, 1.0))

    def _f_mfhlsnn(self, y: float) -> float:
        """f(y,γ) for [2003]/[2014]/[2017] variants.

        Issue 2 [2003]: paper prints 'y·γ if 0 < y·γ < 1, otherwise 0'.
        Literal reading: far patterns (y * gamma >= 1) get f=0 -> membership=1 (as printed).
        Applies ONLY to mfhlsnn2003_height. 2014 and 2017 variants use f with y*gamma clipped to [0,1].
        """
        val = y * self.gamma
        if val <= 0.0:
            return 0.0
        if 0.0 < val < 1.0:
            return val
        # val >= 1:
        if self.membership_type == 'mfhlsnn2003_height' and self.issue_2_mfhlsnn_f_zero:
            return 0.0
        return 1.0

    def _scalar_membership(self, R: np.ndarray, V: np.ndarray, W: np.ndarray) -> float:
        """Membership of single pattern R against segment [V, W].

        Used only during fit() for inclusion and collinearity tests.
        predict() uses the vectorised _vec_memberships() instead.
        """
        l1 = float(np.linalg.norm(W - R))
        l2 = float(np.linalg.norm(V - R))
        l  = float(np.linalg.norm(W - V))

        if self.membership_type == 'fhlsnn2001':
            return 1.0 - self._f2001(l1 + l2, l)
        elif self.membership_type == 'mfhlsnn2003_height':
            return self._mem_height(R, V, W, l1, l2, l)
        elif self.membership_type == 'mfhlsnn2014_midpoint':
            return self._mem_midpoint(R, V, W, l1, l2, l)
        elif self.membership_type == 'efhlsnn2017_segment':
            return self._mem_segment(R, V, W, l1, l2, l)
        raise ValueError(f"Unknown membership_type {self.membership_type}")

    def _mem_height(self, R, V, W, l1, l2, l) -> float:
        """[2003] triangle-height membership (Heron's formula).

        Issue 3: h = perpendicular distance to the *infinite* line through V, W.
        When issue_3=False h is clamped to the nearest point on the segment.
        """
        if l < self.collinearity_tol:      # degenerate point-segment
            return 1.0 - self._f_mfhlsnn(l1)

        s    = (l1 + l2 + l) / 2.0
        area = float(np.sqrt(max(0.0, s * (s - l1) * (s - l2) * (s - l))))
        h    = (2.0 * area) / l            # distance to infinite line

        if not self.issue_3_mfhlsnn_h_line:
            # Fix: project R onto segment; use endpoint distance if outside
            t = float(np.dot(R - V, W - V)) / (l * l)
            if t <= 0.0:
                h = l2
            elif t >= 1.0:
                h = l1
            # else: h stays (perpendicular distance is the segment distance)

        if h > self.collinearity_tol:      # R off the line
            return 1.0 - self._f_mfhlsnn(h)
        else:                              # [2003] h==0 case: R on the line
            return 1.0 - self._f_mfhlsnn(min(l1, l2))

    def _mem_midpoint(self, R, V, W, l1, l2, l) -> float:
        """[2014] midpoint-based membership.

        Issue 4: paper prints midpoint as |(w−v)/2|, not (v+w)/2.
        Issue 5: min(l1+l2, l3) is always l3 by the triangle inequality.
        """
        if self.issue_4_midpoint_printed:
            midpoint = np.abs((W - V) / 2.0)   # [2014] as printed
        else:
            midpoint = (V + W) / 2.0

        l3 = float(np.linalg.norm(midpoint - R))
        y  = min(l1 + l2, l3) if self.issue_5_min_redundant else l3
        return 1.0 - self._f_mfhlsnn(y)

    def _mem_segment(self, R, V, W, l1, l2, l) -> float:
        """[2017] shortest-distance-to-*segment* membership.

        Issue 7: paper prints t = Σ(x−v)(w−v)/l.  Correct formula divides by l²
        so that t ∈ [0,1] is the normalised projection parameter.  When
        issue_7=True we use l as printed; when False we divide by l².

        Note: the printed version with denom=l gives t values NOT in [0,1],
        so the branch selection (t<0 / t>1 / else) based on it is wrong
        for all points not very close to V.
        """
        if l < self.collinearity_tol:
            return 1.0 - self._f_mfhlsnn(l1)

        # Always divide by l² so t ∈ [0,1] controls projection branch correctly.
        # When issue_7=True we show the printed computation in the intermediate
        # variable t_printed for diagnostic purposes, but the branch we must use
        # for correct geometry is always t_correct.  The issue flag changes only
        # which t is used to select the branch.
        dot = float(np.dot(R - V, W - V))
        if self.issue_7_t_divides_by_l:
            t = dot / l          # [2017] as printed — denom is l, NOT l²
        else:
            t = dot / (l * l)   # geometrically correct

        if t <= 0.0:
            dist = l2            # closest point is V
        elif t >= 1.0:
            dist = l1            # closest point is W
        else:
            proj = V + t * (W - V)
            dist = float(np.linalg.norm(R - proj))

        return 1.0 - self._f_mfhlsnn(dist)

    # ── vectorised membership (used in predict / winning_segment) ─────────

    def _vec_memberships(self, R: np.ndarray) -> np.ndarray:
        """Return membership of a single pattern R against all m segments.

        Shape: (m,).  All operations are NumPy-vectorised; no Python loop over segments.
        """
        return self._vec_memberships_custom(R, self._V, self._W)

    def _vec_memberships_custom(self, R: np.ndarray, V: np.ndarray, W: np.ndarray) -> np.ndarray:
        """Return membership of single pattern R against arbitrary endpoint matrices V, W (m, n)."""
        if len(V) == 0:
            return np.empty((0,), dtype=np.float64)
        l1 = np.linalg.norm(W - R, axis=1)    # (m,)
        l2 = np.linalg.norm(V - R, axis=1)
        l  = np.linalg.norm(W - V, axis=1)
        mt = self.membership_type

        if mt == 'fhlsnn2001':
            x    = l1 + l2
            xl   = x - l
            on_  = np.abs(xl) < self.collinearity_tol
            val  = np.where(self.issue_1_f_uses_x_gamma, x * self.gamma, xl * self.gamma)
            val  = np.clip(val, 0.0, 1.0)
            val  = np.where(on_, 0.0, val)
            return 1.0 - val

        elif mt == 'mfhlsnn2003_height':
            safe_l = np.where(l < self.collinearity_tol, 1.0, l)
            s      = (l1 + l2 + l) / 2.0
            area2  = np.maximum(0.0, s * (s - l1) * (s - l2) * (s - l))
            h_line = (2.0 * np.sqrt(area2)) / safe_l
            h      = np.where(l < self.collinearity_tol, l1, h_line)

            if not self.issue_3_mfhlsnn_h_line:
                t    = np.einsum('mn,mn->m', R - V, W - V) / (safe_l * safe_l)
                h    = np.where(t <= 0.0, l2, np.where(t >= 1.0, l1, h))

            on_line = h <= self.collinearity_tol
            y       = np.where(on_line, np.minimum(l1, l2), h)
            return self._apply_f_mfhlsnn_vec(y)

        elif mt == 'mfhlsnn2014_midpoint':
            if self.issue_4_midpoint_printed:
                midpts = np.abs((W - V) / 2.0)
            else:
                midpts = (V + W) / 2.0
            l3 = np.linalg.norm(midpts - R, axis=1)
            y  = np.minimum(l1 + l2, l3) if self.issue_5_min_redundant else l3
            return self._apply_f_mfhlsnn_vec(y)

        elif mt == 'efhlsnn2017_segment':
            safe_l = np.where(l < self.collinearity_tol, 1.0, l)
            dot    = np.einsum('mn,mn->m', R - V, W - V)
            if self.issue_7_t_divides_by_l:
                t = dot / safe_l          # as printed
            else:
                t = dot / (safe_l * safe_l)  # correct
            proj   = V + t[:, None] * (W - V)
            d_perp = np.linalg.norm(R - proj, axis=1)
            dist   = np.where(l < self.collinearity_tol, l1,
                     np.where(t <= 0.0, l2,
                     np.where(t >= 1.0, l1, d_perp)))
            return self._apply_f_mfhlsnn_vec(dist)

        raise ValueError(f"Unknown membership_type {self.membership_type}")

    def _apply_f_mfhlsnn_vec(self, y: np.ndarray) -> np.ndarray:
        """Vectorised f_mfhlsnn, matches _f_mfhlsnn exactly."""
        val   = y * self.gamma
        f_zero = self.issue_2_mfhlsnn_f_zero if self.membership_type == 'mfhlsnn2003_height' else False
        f_val = np.where(
            val <= 0.0, 0.0,
            np.where(
                val < 1.0, val,
                0.0 if f_zero else 1.0
            )
        )
        return 1.0 - f_val

    def _single_intersection(self, V1: np.ndarray, W1: np.ndarray,
                             V2: np.ndarray, W2: np.ndarray) -> bool:
        """Original per-segment intersection test using np.linalg.lstsq (PRD 4.1)."""
        d1 = W1 - V1
        d2 = W2 - V2
        A  = np.column_stack((d1, -d2))
        b  = V2 - V1
        t_sol, residuals, _, _ = np.linalg.lstsq(A, b, rcond=None)
        res = (float(residuals[0]) if len(residuals)
               else float(np.linalg.norm(A @ t_sol - b) ** 2))

        if res >= self.collinearity_tol:
            return False

        t1, t2 = float(t_sol[0]), float(t_sol[1])
        tol    = self.collinearity_tol
        on_s1  = (-tol <= t1 <= 1.0 + tol)
        on_s2  = (-tol <= t2 <= 1.0 + tol)
        return on_s1 and on_s2

    def _check_intersection_batched(self, V1: np.ndarray, W1: np.ndarray,
                                   V2_all: np.ndarray, W2_all: np.ndarray) -> bool:
        """Batched closed-form 2x2 normal equations for intersection against all other segments (PRD Step 1a)."""
        K = len(V2_all)
        if K == 0:
            return False

        tol = self.collinearity_tol
        d1 = W1 - V1
        d2 = W2_all - V2_all
        b = V2_all - V1

        a11 = float(np.dot(d1, d1))
        a12 = -np.dot(d2, d1)
        a22 = np.sum(d2 * d2, axis=1)
        r1 = np.dot(b, d1)
        r2 = -np.sum(d2 * b, axis=1)
        det = a11 * a22 - a12 * a12

        # Degenerate cases: determinant ~ 0 or zero-length segments
        deg = (a11 < 1e-12) | (a22 < 1e-12) | (det <= 1e-12 * (a11 * a22))
        non_deg = ~deg

        if np.any(non_deg):
            inv_det = 1.0 / det[non_deg]
            t1 = (a22[non_deg] * r1[non_deg] - a12[non_deg] * r2[non_deg]) * inv_det
            t2 = (-a12[non_deg] * r1[non_deg] + a11 * r2[non_deg]) * inv_det
            diff = t1[:, None] * d1 - t2[:, None] * d2[non_deg] - b[non_deg]
            res = np.sum(diff * diff, axis=1)
            on_s1 = (-tol <= t1) & (t1 <= 1.0 + tol)
            on_s2 = (-tol <= t2) & (t2 <= 1.0 + tol)
            if np.any((res < tol) & on_s1 & on_s2):
                return True

        if np.any(deg):
            for k in np.where(deg)[0]:
                if self._single_intersection(V1, W1, V2_all[k], W2_all[k]):
                    return True

        return False

    # ── public API ─────────────────────────────────────────────────────────

    def get_stored_vectors_count(self) -> int:
        """PRD 4.4: point-segment (V==W) counts as 1; two-endpoint segment counts as 2."""
        if len(self._V) == 0 or self._V.ndim < 2:
            return 0
        point_seg = np.all(np.isclose(self._V, self._W), axis=1)
        return int(np.sum(~point_seg) * 2 + np.sum(point_seg))

    def _partial_fit_reference(self, X: np.ndarray, y: np.ndarray) -> 'FHLSNN':
        """Reference incremental learning (used only by equivalence tests)."""
        indices = np.arange(len(X))
        if self.shuffle:
            rng = np.random.RandomState(self.random_state)
            rng.shuffle(indices)

        for idx in indices:
            R   = X[idx]
            d_h = int(y[idx])

            class_segs = [s for s in self.segments_ if s['class'] == d_h]

            # ── step 1: already covered by a same-class segment? ─────────
            # membership ≥ 1−tol means R lies on segment [V, W].
            covered = any(
                self._scalar_membership(R, s['V'], s['W']) >= 1.0 - self.collinearity_tol
                for s in class_segs
            )
            if covered:
                continue

            # ── steps 2 & 3: try to extend an existing segment ───────────
            extended       = False
            extended_seg   = None
            old_V_backup   = None   # copy taken BEFORE the modification
            old_W_backup   = None

            for seg in class_segs:
                V_j = seg['V']
                W_j = seg['W']
                l1  = float(np.linalg.norm(W_j - R))
                l2  = float(np.linalg.norm(V_j - R))
                l   = float(np.linalg.norm(W_j - V_j))

                if l < self.collinearity_tol:
                    # ── step 3: point-segment → extend to R if length ≤ ζ ─
                    # Collinearity test is trivially satisfied when V == W.
                    new_l = float(np.linalg.norm(V_j - R))
                    if new_l <= self.zeta:
                        old_V_backup = V_j.copy()   # copy BEFORE modifying
                        old_W_backup = W_j.copy()
                        seg['W'] = R.copy()
                        extended = True
                        extended_seg = seg
                        break
                else:
                    # ── step 2: collinearity test for a proper segment ────
                    # Use cross-product area: ||(W-V) × (R-V)|| = l * height.
                    # If height < collinearity_tol, R is collinear with V and W.
                    # This is numerically stable unlike the perimeter formula.
                    n = len(R)
                    if n == 2:
                        # 2-D cross product magnitude
                        WmV = W_j - V_j
                        RmV = R - V_j
                        cross = abs(WmV[0] * RmV[1] - WmV[1] * RmV[0])
                    else:
                        # N-D: ||cross|| = ||WmV||*||RmV||*sin(theta)
                        WmV = W_j - V_j
                        RmV = R - V_j
                        # Use the formula: area = 0.5 * ||WmV × RmV||
                        # For n>3 use: cross_norm² = ||WmV||²||RmV||² - (WmV·RmV)²
                        dot = float(np.dot(WmV, RmV))
                        cross_sq = max(0.0, float(np.dot(WmV, WmV)) * float(np.dot(RmV, RmV)) - dot * dot)
                        cross = float(np.sqrt(cross_sq))

                    # height = cross / l ; R is collinear iff height < tol
                    height = cross / l if l > 0 else float('inf')

                    if height < self.collinearity_tol:
                        # R is collinear with V_j and W_j.
                        # Replace the nearer-side endpoint with R.
                        if l1 > l2:
                            # R is beyond V_j; new segment would be R–W_j
                            if np.linalg.norm(W_j - R) <= self.zeta:
                                old_V_backup = V_j.copy()
                                old_W_backup = W_j.copy()
                                seg['V'] = R.copy()
                                extended = True
                                extended_seg = seg
                                break
                        else:
                            # R is beyond W_j; new segment would be V_j–R
                            if np.linalg.norm(V_j - R) <= self.zeta:
                                old_V_backup = V_j.copy()
                                old_W_backup = W_j.copy()
                                seg['W'] = R.copy()
                                extended = True
                                extended_seg = seg
                                break

            # ── step 4: create a new point-segment ───────────────────────
            newly_created = False
            if not extended:
                new_seg = {'V': R.copy(), 'W': R.copy(), 'class': d_h}
                self.segments_.append(new_seg)
                extended_seg = new_seg
                newly_created = True

            # ── intersection test ─────────────────────────────────────────
            if not self.use_intersection_test:
                continue

            # Default "skip": newly created point-segments are not tested [2017].
            if newly_created and self.step4_intersection == 'skip':
                continue

            V1 = extended_seg['V']
            W1 = extended_seg['W']
            intersection_found = False

            import time
            t0_int = time.perf_counter()

            for other_seg in self.segments_:
                if other_seg is extended_seg or other_seg['class'] == d_h:
                    continue
                V2 = other_seg['V']
                W2 = other_seg['W']

                # Solve V1 + t1·d1 = V2 + t2·d2 in least-squares sense
                # [2001]: detect intersecting segments before finalising extension
                d1 = W1 - V1
                d2 = W2 - V2
                A  = np.column_stack((d1, -d2))
                b  = V2 - V1
                t_sol, residuals, _, _ = np.linalg.lstsq(A, b, rcond=None)
                res = (float(residuals[0]) if len(residuals)
                       else float(np.linalg.norm(A @ t_sol - b) ** 2))

                if res >= self.collinearity_tol:
                    continue    # lines do not intersect in this subspace

                t1, t2 = float(t_sol[0]), float(t_sol[1])
                tol    = self.collinearity_tol
                on_s1  = (-tol <= t1 <= 1.0 + tol)
                on_s2  = (-tol <= t2 <= 1.0 + tol)
                if on_s1 and on_s2:
                    intersection_found = True
                    break

            if intersection_found:
                if not newly_created:
                    # Undo extension: restore old endpoints, open a new point-segment
                    extended_seg['V'] = old_V_backup   # already a copy
                    extended_seg['W'] = old_W_backup
                    self.segments_.append({'V': R.copy(), 'W': R.copy(), 'class': d_h})
                else:
                    # step4_intersection action for newly created segments
                    if self.step4_intersection == 'drop_new':
                        # Discard the segment; this training pattern is lost.
                        # MUST NOT be the default (PRD 4.1 issue 6).
                        self.segments_.pop()
                    # "swap_2014": keep the point-segment as-is (no change needed)
                    # "skip": cannot reach here (guarded above)
            
            self.inter_time_ = getattr(self, 'inter_time_', 0.0) + (time.perf_counter() - t0_int)

        self.n_segments_ = len(self.segments_)
        self._rebuild_matrices()
        return self

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> 'FHLSNN':
        """Incremental learning - fast vectorized path (PRD Step 1a)."""
        indices = np.arange(len(X))
        if self.shuffle:
            rng = np.random.RandomState(self.random_state)
            rng.shuffle(indices)

        n_samples, n_features = X.shape
        init_cap = max(64, n_samples // 4)

        V_all = np.empty((init_cap, n_features), dtype=np.float64)
        W_all = np.empty((init_cap, n_features), dtype=np.float64)
        cls_all = np.empty(init_cap, dtype=np.int64)
        n_total = 0

        V_class = {}
        W_class = {}
        global_idx_class = {}
        count_class = {}

        if self.segments_:
            n_existing = len(self.segments_)
            if n_existing > init_cap:
                init_cap = n_existing * 2
                V_all = np.empty((init_cap, n_features), dtype=np.float64)
                W_all = np.empty((init_cap, n_features), dtype=np.float64)
                cls_all = np.empty(init_cap, dtype=np.int64)
            for s in self.segments_:
                c = int(s['class'])
                if c not in count_class:
                    c_cap = max(32, init_cap // 4)
                    V_class[c] = np.empty((c_cap, n_features), dtype=np.float64)
                    W_class[c] = np.empty((c_cap, n_features), dtype=np.float64)
                    global_idx_class[c] = np.empty(c_cap, dtype=np.int64)
                    count_class[c] = 0

                if count_class[c] >= len(V_class[c]):
                    new_ccap = len(V_class[c]) * 2
                    V_class[c] = _grow_2d(V_class[c], new_ccap)
                    W_class[c] = _grow_2d(W_class[c], new_ccap)
                    global_idx_class[c] = _grow_1d(global_idx_class[c], new_ccap)

                V_all[n_total] = s['V']
                W_all[n_total] = s['W']
                cls_all[n_total] = c

                c_idx = count_class[c]
                V_class[c][c_idx] = s['V']
                W_class[c][c_idx] = s['W']
                global_idx_class[c][c_idx] = n_total
                count_class[c] += 1
                n_total += 1

        for idx in indices:
            R = X[idx]
            d_h = int(y[idx])

            if d_h not in count_class:
                c_cap = max(32, init_cap // 4)
                V_class[d_h] = np.empty((c_cap, n_features), dtype=np.float64)
                W_class[d_h] = np.empty((c_cap, n_features), dtype=np.float64)
                global_idx_class[d_h] = np.empty(c_cap, dtype=np.int64)
                count_class[d_h] = 0

            m_c = count_class[d_h]
            V_c = V_class[d_h][:m_c]
            W_c = W_class[d_h][:m_c]

            # ── step 1: already covered by a same-class segment? ─────────
            if m_c > 0:
                mems = self._vec_memberships_custom(R, V_c, W_c)
                if np.any(mems >= 1.0 - self.collinearity_tol):
                    continue

            # ── steps 2 & 3: try to extend an existing segment ───────────
            extended = False
            extended_local_idx = None
            old_V_backup = None
            old_W_backup = None

            if m_c > 0:
                WmV = W_c - V_c
                RmV = R - V_c
                l1_vec = np.linalg.norm(W_c - R, axis=1)
                l2_vec = np.linalg.norm(V_c - R, axis=1)
                l_vec  = np.linalg.norm(WmV, axis=1)

                is_point = l_vec < self.collinearity_tol
                point_extendable = is_point & (l2_vec <= self.zeta)

                if n_features == 2:
                    cross_vec = np.abs(WmV[:, 0] * RmV[:, 1] - WmV[:, 1] * RmV[:, 0])
                else:
                    dot_vec = np.sum(WmV * RmV, axis=1)
                    WmV_sq  = np.sum(WmV * WmV, axis=1)
                    RmV_sq  = np.sum(RmV * RmV, axis=1)
                    cross_sq_vec = np.maximum(0.0, WmV_sq * RmV_sq - dot_vec * dot_vec)
                    cross_vec = np.sqrt(cross_sq_vec)

                safe_l = np.where(is_point, 1.0, l_vec)
                height_vec = np.where(is_point, float('inf'), cross_vec / safe_l)
                is_collinear = (~is_point) & (height_vec < self.collinearity_tol)

                cond_l1_greater = l1_vec > l2_vec
                new_len = np.where(cond_l1_greater, l1_vec, l2_vec)
                proper_extendable = is_collinear & (new_len <= self.zeta)

                extendable = point_extendable | proper_extendable

                if np.any(extendable):
                    extended_local_idx = int(np.argmax(extendable))
                    old_V_backup = V_c[extended_local_idx].copy()
                    old_W_backup = W_c[extended_local_idx].copy()

                    g_idx = global_idx_class[d_h][extended_local_idx]
                    if point_extendable[extended_local_idx]:
                        W_class[d_h][extended_local_idx] = R
                        W_all[g_idx] = R
                    elif cond_l1_greater[extended_local_idx]:
                        V_class[d_h][extended_local_idx] = R
                        V_all[g_idx] = R
                    else:
                        W_class[d_h][extended_local_idx] = R
                        W_all[g_idx] = R

                    extended = True

            # ── step 4: create a new point-segment ───────────────────────
            newly_created = False
            if not extended:
                newly_created = True
                if n_total >= len(V_all):
                    new_cap = len(V_all) * 2
                    V_all = _grow_2d(V_all, new_cap)
                    W_all = _grow_2d(W_all, new_cap)
                    cls_all = _grow_1d(cls_all, new_cap)

                if count_class[d_h] >= len(V_class[d_h]):
                    new_ccap = len(V_class[d_h]) * 2
                    V_class[d_h] = _grow_2d(V_class[d_h], new_ccap)
                    W_class[d_h] = _grow_2d(W_class[d_h], new_ccap)
                    global_idx_class[d_h] = _grow_1d(global_idx_class[d_h], new_ccap)

                c_idx = count_class[d_h]
                V_class[d_h][c_idx] = R
                W_class[d_h][c_idx] = R
                global_idx_class[d_h][c_idx] = n_total
                count_class[d_h] += 1

                V_all[n_total] = R
                W_all[n_total] = R
                cls_all[n_total] = d_h
                n_total += 1

            # ── intersection test ─────────────────────────────────────────
            if not self.use_intersection_test:
                continue

            if newly_created and self.step4_intersection == 'skip':
                continue

            t0_int = time.perf_counter()

            if extended:
                g_idx = global_idx_class[d_h][extended_local_idx]
                V1 = V_all[g_idx]
                W1 = W_all[g_idx]
            else:
                V1 = V_all[n_total - 1]
                W1 = W_all[n_total - 1]

            other_mask = (cls_all[:n_total] != d_h)
            K = int(np.sum(other_mask))
            intersection_found = False

            if K > 0:
                V2_all = V_all[:n_total][other_mask]
                W2_all = W_all[:n_total][other_mask]
                intersection_found = self._check_intersection_batched(V1, W1, V2_all, W2_all)

            self.inter_time_ = getattr(self, 'inter_time_', 0.0) + (time.perf_counter() - t0_int)

            if intersection_found:
                if not newly_created:
                    g_idx = global_idx_class[d_h][extended_local_idx]
                    V_class[d_h][extended_local_idx] = old_V_backup
                    W_class[d_h][extended_local_idx] = old_W_backup
                    V_all[g_idx] = old_V_backup
                    W_all[g_idx] = old_W_backup

                    if n_total >= len(V_all):
                        new_cap = len(V_all) * 2
                        V_all = _grow_2d(V_all, new_cap)
                        W_all = _grow_2d(W_all, new_cap)
                        cls_all = _grow_1d(cls_all, new_cap)

                    if count_class[d_h] >= len(V_class[d_h]):
                        new_ccap = len(V_class[d_h]) * 2
                        V_class[d_h] = _grow_2d(V_class[d_h], new_ccap)
                        W_class[d_h] = _grow_2d(W_class[d_h], new_ccap)
                        global_idx_class[d_h] = _grow_1d(global_idx_class[d_h], new_ccap)

                    c_idx = count_class[d_h]
                    V_class[d_h][c_idx] = R
                    W_class[d_h][c_idx] = R
                    global_idx_class[d_h][c_idx] = n_total
                    count_class[d_h] += 1

                    V_all[n_total] = R
                    W_all[n_total] = R
                    cls_all[n_total] = d_h
                    n_total += 1
                else:
                    if self.step4_intersection == 'drop_new':
                        count_class[d_h] -= 1
                        n_total -= 1

        self.n_segments_ = n_total
        self._V = V_all[:n_total].copy()
        self._W = W_all[:n_total].copy()
        self._cls = cls_all[:n_total].copy()
        self.segments_ = [{'V': self._V[i], 'W': self._W[i], 'class': int(self._cls[i])} for i in range(n_total)]
        return self

    def _fit_reference(self, X: np.ndarray, y: np.ndarray) -> 'FHLSNN':
        """Reference fit (calls _reset and _partial_fit_reference), used only by tests."""
        self._reset()
        return self._partial_fit_reference(X, y)

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'FHLSNN':
        """Single-pass online learning.

        Resets ALL learned state before running (sklearn estimator contract).
        For incremental learning, use partial_fit().

        Algorithm follows [2001] Section 3 (FHLSNN learning procedure),
        shared by all membership variants ([2003] uses same steps with
        the membership function swapped — PRD assumption logged as D4).
        """
        self._reset()
        return self.partial_fit(X, y)

    # ── predict / winning_segment ─────────────────────────────────────────

    def _vec_segment_distances(self, R: np.ndarray) -> np.ndarray:
        """Computes the exact geometric distance from R to every segment (PRD EFHLSNN-2017 style)."""
        WmV = self._W - self._V
        RmV = R - self._V
        l_sq = np.sum(WmV ** 2, axis=1)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            t = np.sum(WmV * RmV, axis=1) / l_sq
        t = np.where(l_sq == 0, 0.0, t)
        t_clip = np.clip(t, 0.0, 1.0)
        
        proj = self._V + t_clip[:, None] * WmV
        dists = np.linalg.norm(R - proj, axis=1)
        return dists

    def _predict_and_win(self, X: np.ndarray) -> tuple[np.ndarray, list]:
        """Returns (predicted_classes, winning_segment_indices) for X."""
        if self.n_segments_ == 0:
            raise RuntimeError("Model has not been fitted or has zero segments.")

        n  = len(X)
        out = np.empty(n, dtype=self._cls.dtype)
        winners = []
        zero_count = 0

        for i, R in enumerate(X):
            mems    = self._vec_memberships(R)   # (m,)
            max_mem = float(mems.max())

            if max_mem <= self.collinearity_tol:
                # All-zero membership: fall back to nearest segment distance
                zero_count += 1
                dists = self._vec_segment_distances(R)
                j    = int(np.argmin(dists))
            else:
                candidates = np.where(mems >= max_mem - self.collinearity_tol)[0]
                if len(candidates) == 1:
                    j = int(candidates[0])
                else:
                    dists = self._vec_segment_distances(R)
                    j    = int(candidates[np.argmin(dists[candidates])])
            out[i] = self._cls[j]
            winners.append(j)

        self._last_zero_mem_frac = zero_count / max(n, 1)
        return out, winners

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Vectorised prediction with tie-break by nearest segment distance.
        Tie-break rule (PRD 4.1): when all memberships are zero, or when
        multiple segments share the maximum membership, use the one whose
        exact segment is closest to R. The fraction of patterns where
        all memberships were zero is stored in self._last_zero_mem_frac.
        """
        out, _ = self._predict_and_win(X)
        return out

    def winning_segment(self, X: np.ndarray) -> list:
        """Index of the winning segment for each row in X.

        Returns list of int indices into self.segments_.
        Used by M3 (segment-level pruning) and explainability agent.
        """
        _, winners = self._predict_and_win(X)
        return winners

    def extract_rules(self) -> list:
        """Human-readable per-segment rules (PRD 6.3).

        Full rule extraction (PART quantisation per [2017] Section 6.3) is deferred
        until the EFHLSNN paper has been read (PRD instruction: do not implement
        rule extraction until the EFHLSNN paper has been read).
        """
        rules = []
        for seg in self.segments_:
            length = float(np.linalg.norm(seg['W'] - seg['V']))
            rules.append({
                'class':    seg['class'],
                'V':        seg['V'].tolist(),
                'W':        seg['W'].tolist(),
                'length':   length,
                'is_point': length < self.collinearity_tol,
            })
        return rules
