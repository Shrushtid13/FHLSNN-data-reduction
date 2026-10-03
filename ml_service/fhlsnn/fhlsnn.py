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
from typing import Optional


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

    # ── internal reset / rebuild ───────────────────────────────────────────

    def _reset(self):
        """Reset all learned state (sklearn contract: fit() is not incremental)."""
        self.segments_ = []
        self.n_segments_ = 0
        self._V = np.empty((0, 1))
        self._W = np.empty((0, 1))
        self._cls = np.empty((0,), dtype=int)
        self._last_zero_mem_frac = 0.0

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
        Fixed: return 1 when y·γ ≥ 1 (issue_2_mfhlsnn_f_zero=False).
        """
        val = y * self.gamma
        if val <= 0.0:
            return 0.0
        if 0.0 < val < 1.0:
            return val
        # val >= 1:
        return 0.0 if self.issue_2_mfhlsnn_f_zero else 1.0

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
        V  = self._V   # (m, n)
        W  = self._W
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
        f_val = np.where(
            val <= 0.0, 0.0,
            np.where(
                val < 1.0, val,
                0.0 if self.issue_2_mfhlsnn_f_zero else 1.0
            )
        )
        return 1.0 - f_val

    # ── public API ─────────────────────────────────────────────────────────

    def get_stored_vectors_count(self) -> int:
        """PRD 4.4: point-segment (V==W) counts as 1; two-endpoint segment counts as 2."""
        if len(self._V) == 0 or self._V.ndim < 2:
            return 0
        point_seg = np.all(np.isclose(self._V, self._W), axis=1)
        return int(np.sum(~point_seg) * 2 + np.sum(point_seg))

    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> 'FHLSNN':
        """Incremental learning (processes a batch of patterns without resetting)."""
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

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Vectorised prediction with tie-break by nearest segment distance.

        Tie-break rule (PRD 4.1): when all memberships are zero, or when
        multiple segments share the maximum membership, use the one whose
        exact segment is closest to R. The fraction of patterns where
        all memberships were zero is stored in self._last_zero_mem_frac.
        """
        if self.n_segments_ == 0:
            raise RuntimeError("Model has not been fitted or has zero segments.")

        n  = len(X)
        out = np.empty(n, dtype=self._cls.dtype)
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

        self._last_zero_mem_frac = zero_count / max(n, 1)
        return out

    def winning_segment(self, X: np.ndarray) -> list:
        """Index of the winning segment for each row in X.

        Returns list of int indices into self.segments_.
        Used by M3 (segment-level pruning) and explainability agent.
        """
        if self.n_segments_ == 0:
            return []
        result = []
        for R in X:
            mems    = self._vec_memberships(R)
            max_mem = float(mems.max())
            if max_mem <= self.collinearity_tol:
                dists = self._vec_segment_distances(R)
                j    = int(np.argmin(dists))
            else:
                candidates = np.where(mems >= max_mem - self.collinearity_tol)[0]
                if len(candidates) == 1:
                    j = int(candidates[0])
                else:
                    dists = self._vec_segment_distances(R)
                    j    = int(candidates[np.argmin(dists[candidates])])
            result.append(j)
        return result

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
