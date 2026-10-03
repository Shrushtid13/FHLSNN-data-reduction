"""
test_fhlsnn.py – unit tests for the FHLSNN classifier.

Every test section cites the PRD requirement it covers.
Hand-computed expected values are derived below each test; do NOT adjust
expected values to match the code – fix the code instead.
"""

import numpy as np
import pytest
from ml_service.fhlsnn.fhlsnn import FHLSNN
from sklearn.datasets import load_iris
from sklearn.preprocessing import MinMaxScaler


# ═══════════════════════════════════════════════════════════════════════════
# A.  MEMBERSHIP FUNCTIONS – hand-computed values (PRD 4.1 Gate A)
# ═══════════════════════════════════════════════════════════════════════════

class TestMembership2001:
    """[2001] fhlsnn2001 variant."""

    def test_on_segment_returns_1(self):
        # R exactly on segment → x == l → f = 0 → membership = 1.
        m = FHLSNN(gamma=1.0, membership_type='fhlsnn2001')
        V, W = np.array([0.0, 0.0]), np.array([0.2, 0.0])
        R = np.array([0.1, 0.0])
        assert np.isclose(m._scalar_membership(R, V, W), 1.0), "On-segment must be 1.0"

    def test_issue1_as_printed(self):
        # PRD 4.1 hand-computed (a): V=(0,0) W=(0.2,0) R=(0.3,0)
        # l1=0.1, l2=0.3, l=0.2, x=0.4
        # As printed: f = x·γ = 0.4 → membership = 0.6
        m = FHLSNN(gamma=1.0, membership_type='fhlsnn2001', issue_1_f_uses_x_gamma=True)
        V, W = np.array([0.0, 0.0]), np.array([0.2, 0.0])
        R    = np.array([0.3, 0.0])
        assert np.isclose(m._scalar_membership(R, V, W), 0.6), "As-printed: expected 0.6"

    def test_issue1_fixed(self):
        # Fixed: f = (x−l)·γ = 0.2 → membership = 0.8
        m = FHLSNN(gamma=1.0, membership_type='fhlsnn2001', issue_1_f_uses_x_gamma=False)
        V, W = np.array([0.0, 0.0]), np.array([0.2, 0.0])
        R    = np.array([0.3, 0.0])
        assert np.isclose(m._scalar_membership(R, V, W), 0.8), "Fixed: expected 0.8"


class TestMembership2003:
    """[2003] mfhlsnn2003_height variant."""

    def test_issue3_as_printed_h_line(self):
        # PRD 4.1 hand-computed (d): V=(0,0) W=(0.1,0) R=(0.9,0.01)
        # l=0.1, h (distance to infinite line y=0) = 0.01
        # f(0.01,γ=1) = 0.01 → membership = 0.99
        m = FHLSNN(gamma=1.0, membership_type='mfhlsnn2003_height',
                   issue_3_mfhlsnn_h_line=True)
        V, W = np.array([0.0, 0.0]), np.array([0.1, 0.0])
        R    = np.array([0.9, 0.01])
        assert np.isclose(m._scalar_membership(R, V, W), 0.99)

    def test_issue2_as_printed_far_away(self):
        # When y·γ ≥ 1, as-printed returns 0, fixed returns 1.
        m_issue = FHLSNN(gamma=1.0, membership_type='mfhlsnn2003_height',
                         issue_2_mfhlsnn_f_zero=True)
        m_fixed = FHLSNN(gamma=1.0, membership_type='mfhlsnn2003_height',
                         issue_2_mfhlsnn_f_zero=False)
        V, W = np.array([0.0, 0.0]), np.array([0.1, 0.0])
        R = np.array([5.0, 0.0])   # far away, h=0, zz=min(l1,l2)=4.9 → y·γ≥1
        assert np.isclose(m_issue._scalar_membership(R, V, W), 1.0)   # issue: f=0 → 1−0=1
        # note: far away R has large zz -> y*gamma >= 1 -> issue2 gives f=0 -> mem=1 (as printed)
        # fixed: y·γ ≥ 1 → f=1 → mem=0
        assert np.isclose(m_fixed._scalar_membership(R, V, W), 0.0)


class TestMembership2014:
    """[2014] mfhlsnn2014_midpoint variant – PRD 4.1 hand-computed (c)."""

    def test_correct_midpoint(self):
        # V=(0.2,0.2), W=(0.4,0.2), R=(0.3,0.3)
        # True midpoint = (0.3, 0.2); l3 = ||(0.3,0.3)-(0.3,0.2)|| = 0.1
        # y = min(l1+l2, 0.1); l1=||(0.4,0.2)-(0.3,0.3)||=√0.02≈0.1414
        #                        l2=||(0.2,0.2)-(0.3,0.3)||=√0.02≈0.1414
        # l1+l2 ≈ 0.2828 → min = 0.1 → f(0.1,γ=1)=0.1 → mem=0.9
        m = FHLSNN(gamma=1.0, membership_type='mfhlsnn2014_midpoint',
                   issue_4_midpoint_printed=False, issue_2_mfhlsnn_f_zero=False)
        V, W = np.array([0.2, 0.2]), np.array([0.4, 0.2])
        R    = np.array([0.3, 0.3])
        assert np.isclose(m._scalar_membership(R, V, W), 0.9), \
            f"Correct midpoint: got {m._scalar_membership(R, V, W)}"

    def test_printed_midpoint(self):
        # Printed midpoint = |(W−V)/2| = |(0.2,0)/2| = (0.1, 0) (absolute value, not a point)
        # l3 = ||(0.1,0)-(0.3,0.3)|| = √(0.04+0.09) ≈ 0.3606
        # y = min(0.2828, 0.3606) = 0.2828
        # f(0.2828,γ=1) = 0.2828 → mem ≈ 0.7172
        m = FHLSNN(gamma=1.0, membership_type='mfhlsnn2014_midpoint',
                   issue_4_midpoint_printed=True, issue_2_mfhlsnn_f_zero=False)
        V, W = np.array([0.2, 0.2]), np.array([0.4, 0.2])
        R    = np.array([0.3, 0.3])
        l3_printed = np.linalg.norm(np.abs((W - V) / 2.0) - R)
        l1 = np.linalg.norm(W - R)
        l2 = np.linalg.norm(V - R)
        y_expected = min(l1 + l2, l3_printed)
        expected = 1.0 - float(np.clip(y_expected * 1.0, 0, 1))
        assert np.isclose(m._scalar_membership(R, V, W), expected, atol=1e-5)

    def test_min_is_always_l3(self):
        """Issue 5: by the triangle inequality l3 ≤ (l1+l2)/2 ≤ l1+l2, so
        min(l1+l2, l3) == l3 always.  Verify numerically."""
        rng = np.random.RandomState(0)
        m = FHLSNN(gamma=1.0, membership_type='mfhlsnn2014_midpoint',
                   issue_4_midpoint_printed=False, issue_5_min_redundant=True)
        for _ in range(1000):
            V = rng.rand(4)
            W = rng.rand(4)
            R = rng.rand(4)
            mid = (V + W) / 2.0
            l1  = np.linalg.norm(W - R)
            l2  = np.linalg.norm(V - R)
            l3  = np.linalg.norm(mid - R)
            assert min(l1 + l2, l3) == l3 or np.isclose(l1 + l2, l3), \
                "Counterexample found: l3 > l1+l2"


class TestMembership2017:
    """[2017] efhlsnn2017_segment variant – PRD 4.1 hand-computed (b)."""

    # V=(0,0), W=(0.2,0)
    # (b) R=(0.3,0): closest endpoint W, dist=0.1 → f(0.1,γ=1)=0.1 → mem=0.9
    # (b) R=(-0.1,0): closest endpoint V, dist=0.1 → mem=0.9
    # (b) R=(0.1,0.05): t=0.5 → proj=(0.1,0), dist=0.05 → mem=0.95
    # (b) R=(0.1,0):  on segment → dist=0 → f(0,1)=0 → mem=1.0
    #
    # NOTE: issue_7_t_divides_by_l=True is "as printed".
    # These hand-computed values require the CORRECT t = dot/l²,
    # i.e. issue_7_t_divides_by_l=False.

    def _m(self, issue7=False):       # issue7=False = geometrically correct
        return FHLSNN(gamma=1.0, membership_type='efhlsnn2017_segment',
                      issue_7_t_divides_by_l=issue7, issue_2_mfhlsnn_f_zero=False)

    def test_beyond_W(self):
        m = self._m()
        V, W = np.array([0.0, 0.0]), np.array([0.2, 0.0])
        R    = np.array([0.3, 0.0])
        assert np.isclose(m._scalar_membership(R, V, W), 0.9)

    def test_beyond_V(self):
        m = self._m()
        V, W = np.array([0.0, 0.0]), np.array([0.2, 0.0])
        R    = np.array([-0.1, 0.0])
        assert np.isclose(m._scalar_membership(R, V, W), 0.9)

    def test_perpendicular(self):
        m = self._m()
        V, W = np.array([0.0, 0.0]), np.array([0.2, 0.0])
        R    = np.array([0.1, 0.05])
        assert np.isclose(m._scalar_membership(R, V, W), 0.95)

    def test_on_segment_is_1(self):
        m = self._m()
        V, W = np.array([0.0, 0.0]), np.array([0.2, 0.0])
        R    = np.array([0.1, 0.0])
        assert np.isclose(m._scalar_membership(R, V, W), 1.0)

    def test_issue7_divides_by_l_vs_l_squared(self):
        # With issue7=True (as printed): t = dot/l ; this is NOT in [0,1] in general
        # and may give wrong branch.  With issue7=False (fixed): t = dot/l²  ∈ [0,1].
        # For V=(0,0) W=(0.2,0) R=(0.1,0): l=0.2
        #   as printed:  t = (0.1*0.2)/(0.2) = 0.1   → t∈[0,1] → same proj → dist=0 → 1.0
        #   fixed:        t = (0.1*0.2)/(0.04) = 0.5  → same proj → dist=0 → 1.0
        # Difference shows at R=(0.15,0): l=0.2
        #   as printed:  t = (0.15*0.2)/(0.2) = 0.15  proj=(0.03,0) dist=||R-proj||≠0
        #   fixed:        t = (0.15*0.2)/(0.04)= 0.75  proj=(0.15,0) dist=0 → 1.0
        m_issue = self._m(issue7=True)
        m_fixed = self._m(issue7=False)
        V, W = np.array([0.0, 0.0]), np.array([0.2, 0.0])
        R    = np.array([0.15, 0.0])
        mem_issue = m_issue._scalar_membership(R, V, W)
        mem_fixed = m_fixed._scalar_membership(R, V, W)
        assert np.isclose(mem_fixed, 1.0), f"Fixed should be 1.0, got {mem_fixed}"
        assert not np.isclose(mem_issue, 1.0), \
            "As-printed should NOT be 1.0 (this is the behaviour difference)"

    def test_tie_break_segment_distance(self):
        """When multiple segments have max membership (e.g. 0.0), prediction
        should tie-break using the exact projection distance to the segment,
        not to the segment midpoint.

        Hand-computed scenario:
          seg0: V=(0,0), W=(2,0), class=0.  seg1: V=(0,1), W=(0,1), class=1 (point-seg).
          R = (0.1, 0.2).
          Projection distance to seg0: proj = (0.1, 0), dist = 0.2.
          Distance to seg1 (point): sqrt(0.1^2 + 0.8^2) = sqrt(0.65) ~ 0.806.
          Nearest segment is seg0 (class 0).
          If midpoint were used: mid0=(1,0) dist=sqrt(0.85), mid1=(0,1) dist=sqrt(0.65).
          Midpoint fallback would incorrectly pick seg1 (class 1).
        """
        m = FHLSNN(gamma=100.0)  # large gamma pushes all memberships to 0
        m.segments_ = [
            {'V': np.array([0.0, 0.0]), 'W': np.array([2.0, 0.0]), 'class': 0},
            {'V': np.array([0.0, 1.0]), 'W': np.array([0.0, 1.0]), 'class': 1},
        ]
        m.n_segments_ = 2
        m._rebuild_matrices()

        preds = m.predict(np.array([[0.1, 0.2]]))
        assert preds[0] == 0, \
            f"Expected class 0 (nearest segment), got class {preds[0]}"


# ═══════════════════════════════════════════════════════════════════════════
# B.  LEARNING PROCEDURE TESTS (PRD 4.1 Gate A)
# ═══════════════════════════════════════════════════════════════════════════

class TestFit:

    def test_expansion_then_restoration(self):
        """Extend a segment, then trigger intersection → undo extension.

        Class-0 segment (0,0)-(0.5,0); class-1 points at (0.25,-0.5) then (0.25,0.5).
        The learning algorithm processes patterns in ORDER (shuffle=False).
        Step 1: (0,0) → new class-0 point-seg.
        Step 2: (0.5,0) → extends class-0 seg to (0,0)-(0.5,0).
        Step 3: (0.25,-0.5) → new class-1 point-seg.
        Step 4: (0.25,0.5) → tries to extend class-1 seg vertically;
                the extended seg intersects class-0 → undo, new class-1 point-seg.
        Result: 1 class-0 segment + 2 class-1 point-segments = 3 segments.
        Using partial_fit to verify incremental behaviour.
        """
        m = FHLSNN(zeta=2.0, shuffle=False, use_intersection_test=True,
                   step4_intersection='skip', collinearity_tol=1e-5)
        
        # Steps 1 and 2
        m.partial_fit(np.array([[0.0, 0.0], [0.5, 0.0]]), np.array([0, 0]))
        
        # Steps 3 and 4
        m.partial_fit(np.array([[0.25, -0.5], [0.25, 0.5]]), np.array([1, 1]))

        c0_segs = [s for s in m.segments_ if s['class'] == 0]
        assert len(c0_segs) == 1, f"Expected 1 class-0 segment, got {len(c0_segs)}"
        assert np.allclose(c0_segs[0]['V'], [0.0, 0.0])
        assert np.allclose(c0_segs[0]['W'], [0.5, 0.0])

        c1_segs = [s for s in m.segments_ if s['class'] == 1]
        assert len(c1_segs) == 2, f"Expected 2 class-1 point-segs, got {len(c1_segs)}"
        
        # Check exact endpoints of the class-1 point-segments
        pts = sorted([tuple(s['V']) for s in c1_segs])
        assert np.allclose(pts[0], [0.25, -0.5]), f"Expected (0.25, -0.5), got {pts[0]}"
        assert np.allclose(pts[1], [0.25, 0.5]), f"Expected (0.25, 0.5), got {pts[1]}"
        for s in c1_segs:
            assert np.allclose(s['V'], s['W']), "Class-1 segments must be point-segs"

    def test_old_backup_is_a_copy(self):
        """old_V_backup and old_W_backup must be copies, not references.

        Scenario: class-0 segment (0,0)-(0,0), class-1 segment (0.5,0)-(0.5,0).
        Then class-0 pattern at (0.6,0) tries to extend (0,0) to (0,0)-(0.6,0).
        The extended segment intersects the class-1 point at (0.5,0) (t1≈0.83, t2=0).
        Extension is undone → class-0 segment must return to (0,0)-(0,0).

        If old_W_backup were a reference (not a copy), the restore would write
        the already-modified value back, and the segment would NOT be (0,0)-(0,0).
        """
        X = np.array([
            [0.0, 0.0],   # class 0: point-seg
            [0.5, 0.0],   # class 1: point-seg
            [0.6, 0.0],   # class 0: tries to extend, triggers intersection → new point-seg
        ])
        y = np.array([0, 1, 0])

        m = FHLSNN(zeta=2.0, shuffle=False, use_intersection_test=True,
                   step4_intersection='skip')
        m.fit(X, y)

        c0_segs = [s for s in m.segments_ if s['class'] == 0]
        # We expect: original class-0 point-seg (0,0)-(0,0) UNCHANGED,
        # plus a new class-0 point-seg at (0.6,0).
        assert len(c0_segs) == 2, f"Expected 2 class-0 segs, got {len(c0_segs)}"
        pts = sorted([tuple(s['V']) for s in c0_segs])
        assert np.allclose(pts[0], (0.0, 0.0)), f"First class-0 seg wrong: {pts[0]}"
        assert np.allclose(pts[1], (0.6, 0.0)), f"Second class-0 seg wrong: {pts[1]}"

    def test_step4_skip_keeps_pattern(self):
        """PRD 4.1 step-4 scenario: with step4_intersection='skip',
        a newly created point-segment is NEVER intersection-tested.

        Setup: X=[(0,0)c0, (0.5,0)c0, (0.25,0)c1].
        - (0,0) → class-0 point-seg.
        - (0.5,0) → extends class-0 to (0,0)-(0.5,0).
        - (0.25,0) c1 → not covered by any class-1 seg; step 4 creates new c1 pt-seg.
          With 'skip': the new pt-seg is NOT tested for intersection → kept.
          With 'drop_new': the new pt-seg would be tested and dropped (it lies on c0).
        Result 'skip': 1 class-0 seg + 1 class-1 pt-seg = 2 segments.
        Result 'drop_new': 1 class-0 seg + 0 class-1 segs = 1 segment.
        """
        X = np.array([[0.0, 0.0], [0.5, 0.0], [0.25, 0.0]])
        y = np.array([0, 0, 1])

        m_skip = FHLSNN(zeta=2.0, shuffle=False, use_intersection_test=True,
                        step4_intersection='skip')
        m_skip.fit(X, y)
        assert m_skip.n_segments_ == 2, \
            f"'skip' must keep 2 segments (c0-seg + c1-pt), got {m_skip.n_segments_}"

        m_drop = FHLSNN(zeta=2.0, shuffle=False, use_intersection_test=True,
                        step4_intersection='drop_new')
        m_drop.fit(X, y)
        assert m_drop.n_segments_ == 1, \
            f"'drop_new' must drop the c1 pt-seg → 1 segment, got {m_drop.n_segments_}"
        assert m_drop.n_segments_ < m_skip.n_segments_, \
            "drop_new must produce fewer or equal segments than skip"

    def test_step4_drop_new_discards_pattern(self):
        """Alias for the above split-out drop_new test; kept for completeness."""
        X = np.array([[0.0, 0.0], [0.5, 0.0], [0.25, 0.0]])
        y = np.array([0, 0, 1])
        m = FHLSNN(zeta=2.0, shuffle=False, use_intersection_test=True,
                   step4_intersection='drop_new')
        m.fit(X, y)
        assert m.n_segments_ == 1, \
            f"'drop_new' must give 1 segment, got {m.n_segments_}"

    def test_collinearity_tolerance_wired(self):
        """PRD 4.1 tolerance-wiring: collinearity_tol controls when R is treated as
        collinear with an existing segment.

        The code uses the cross-product height formula:
            height = ||(W-V) × (R-V)|| / l
        R is treated as collinear when height < collinearity_tol.

        Points: (0,0), (0.1,0), (0.2, d) where d is the perpendicular offset.
        height of third point relative to segment (0,0)-(0.1,0) = d (if d<0.1).

        With d=1e-3 (h=1e-3):
          loose tol=1e-2: h < tol → collinear → 1 segment.
          strict tol=1e-4: h > tol → NOT collinear → 2 segments.
        """
        d = 1e-3   # perpendicular offset (height)
        X = np.array([[0.0, 0.0], [0.1, 0.0], [0.2, d]])
        y = np.array([0, 0, 0])

        m_loose = FHLSNN(zeta=2.0, collinearity_tol=1e-2, shuffle=False)
        m_loose.fit(X, y)
        assert m_loose.n_segments_ == 1, \
            f"Loose tol (1e-2): expected 1 segment (height {d:.0e} < tol), got {m_loose.n_segments_}"

        m_strict = FHLSNN(zeta=2.0, collinearity_tol=1e-4, shuffle=False)
        m_strict.fit(X, y)
        assert m_strict.n_segments_ == 2, \
            f"Strict tol (1e-4): expected 2 segments (height {d:.0e} > tol), got {m_strict.n_segments_}"

    def test_fit_resets_state(self):
        """sklearn contract: fit() must reset previously learned state.
        A model fitted on A then B must be identical to a fresh model fitted on B.
        """
        # Dataset A
        X_A = np.array([[0.0, 0.0], [0.5, 0.0]])
        y_A = np.array([0, 0])
        # Dataset B
        X_B = np.array([[1.0, 1.0], [1.5, 1.0], [1.0, 1.5]])
        y_B = np.array([1, 1, 2])

        m = FHLSNN(zeta=2.0, shuffle=False)
        m.fit(X_A, y_A)
        assert m.n_segments_ == 1
        
        m.fit(X_B, y_B)  # State should be reset
        
        m_fresh = FHLSNN(zeta=2.0, shuffle=False)
        m_fresh.fit(X_B, y_B)
        
        assert m.n_segments_ == m_fresh.n_segments_
        for s1, s2 in zip(m.segments_, m_fresh.segments_):
            assert np.allclose(s1['V'], s2['V'])
            assert np.allclose(s1['W'], s2['W'])
            assert s1['class'] == s2['class']


# ═══════════════════════════════════════════════════════════════════════════
# C.  TRAINING-ACCURACY ON IRIS (PRD 4.1 Gate A)
# ═══════════════════════════════════════════════════════════════════════════

class TestIrisTrainingAccuracy:

    @pytest.fixture(scope='class')
    def iris_scaled(self):
        iris = load_iris()
        X, y = iris.data, iris.target
        scaler = MinMaxScaler()
        return scaler.fit_transform(X), y

    def test_100pct_train_accuracy_fhlsnn2001(self, iris_scaled):
        """PRD 4.1: 2014 and 2017 papers report 100% training accuracy on Iris.

        Every training pattern must be covered by a same-class segment
        (membership ≥ 1 − tol).  Test with fhlsnn2001 at θ=0.4.
        """
        X, y = iris_scaled
        m = FHLSNN(zeta=0.4, gamma=1.0, membership_type='fhlsnn2001',
                   shuffle=True, random_state=42)
        m.fit(X, y)
        y_pred = m.predict(X)
        accuracy = np.mean(y_pred == y)
        assert accuracy == 1.0, \
            f"Training accuracy must be 100 %, got {accuracy:.4f}"

    def test_every_pattern_on_same_class_segment(self, iris_scaled):
        """Every training pattern must lie on a same-class segment (mem≈1.0)."""
        X, y = iris_scaled
        m = FHLSNN(zeta=0.4, gamma=1.0, membership_type='fhlsnn2001',
                   shuffle=True, random_state=42)
        m.fit(X, y)
        tol = m.collinearity_tol
        for i, (R, true_cls) in enumerate(zip(X, y)):
            # Check membership against all same-class segments
            max_mem = max(
                (m._scalar_membership(R, s['V'], s['W'])
                 for s in m.segments_ if s['class'] == true_cls),
                default=0.0
            )
            assert max_mem >= 1.0 - tol, \
                f"Pattern {i} (class {true_cls}): max_mem={max_mem:.6f} < 1−tol"


# ═══════════════════════════════════════════════════════════════════════════
# D.  VECTORISATION CORRECTNESS (predict == scalar loop)
# ═══════════════════════════════════════════════════════════════════════════

class TestVectorisedPredict:

    def test_vec_matches_scalar_iris(self):
        """Vectorised _vec_memberships must agree with _scalar_membership row-by-row."""
        iris = load_iris()
        X = MinMaxScaler().fit_transform(iris.data)
        y = iris.target

        for mt in ('fhlsnn2001', 'mfhlsnn2003_height'):
            m = FHLSNN(zeta=0.3, gamma=1.0, membership_type=mt,
                       shuffle=True, random_state=7)
            m.fit(X, y)
            # Rebuild matrices (already done in fit)
            for R in X[:20]:
                vec_mems = m._vec_memberships(R)
                for j, seg in enumerate(m.segments_):
                    sc = m._scalar_membership(R, seg['V'], seg['W'])
                    assert np.isclose(vec_mems[j], sc, atol=1e-9), \
                        f"{mt}: segment {j}: vec={vec_mems[j]:.9f} scalar={sc:.9f}"


# ═══════════════════════════════════════════════════════════════════════════
# E.  STORED-VECTORS COUNT (PRD 4.4)
# ═══════════════════════════════════════════════════════════════════════════

class TestStoredVectors:

    def test_point_segment_counts_once(self):
        """A point-segment (V == W) must count as 1 stored vector."""
        m = FHLSNN(zeta=0.0, shuffle=False)
        m.fit(np.array([[0.0], [1.0]]), np.array([0, 1]))
        # Both segments are point-segments
        assert m.n_segments_ == 2
        assert m.get_stored_vectors_count() == 2, \
            "Two point-segments → 2 stored vectors"

    def test_two_endpoint_segment_counts_twice(self):
        """A proper segment (V ≠ W) must count as 2 stored vectors."""
        m = FHLSNN(zeta=2.0, shuffle=False)
        m.fit(np.array([[0.0], [1.0]]), np.array([0, 0]))
        assert m.n_segments_ == 1
        assert m.get_stored_vectors_count() == 2, \
            "One two-endpoint segment → 2 stored vectors"

    def test_negative_reduction_not_clipped(self):
        """PRD 4.4: reduction_vs_raw can be negative (e.g. 45 segs on 75 patterns)."""
        from ml_service.benchmark.metrics import compute_reduction_metrics
        r = compute_reduction_metrics(n_train=10, stored_vectors=15)
        assert r['reduction_vs_raw'] < 0, "Negative reduction must not be clipped"
        assert np.isclose(r['reduction_vs_raw'], -0.5)


# ═══════════════════════════════════════════════════════════════════════════
# F.  HARNESS LEAKAGE TESTS (PRD 4.5)
# ═══════════════════════════════════════════════════════════════════════════

class TestHarnessLeakage:
    """The scaler's fit() and model's fit() must never see test or val data."""

    def test_no_test_index_in_fit_and_val_carved(self):
        """Records training indices passed to fit() for all methods.
        Asserts each is a subset of fit_idx (equal to fit_idx for unreduced)
        and that no validation or test index appears.
        """
        from ml_service.benchmark.harness import run_experiment
        from ml_service.benchmark.baselines import run_cnn, run_enn, run_kmeans_prototypes, run_random_subsampling
        from ml_service.reducers.m1_prefilter import run_m1_prefilter
        from ml_service.reducers.m3_prune import run_m3_prune
        from sklearn.datasets import load_iris

        iris = load_iris()
        X_orig, y_orig = iris.data, iris.target
        # Add an ID column to X_orig to track original indices perfectly
        ids = np.arange(len(X_orig)).reshape(-1, 1)
        X = np.hstack([X_orig, ids])
        y = y_orig

        # We will capture fit_idx, val_idx, test_idx inside the harness by patching
        # Instead of a heavy patch, we can use a custom model to capture what is passed to fit().
        # Since run_experiment scales X, the IDs will be scaled. We must unscale them to get indices.

        global_captured = []

        class TrackingFHLSNN(FHLSNN):
            def fit(self, X_fit, y_fit):
                global_captured.append((X_fit.copy(), y_fit.copy()))
                return super().fit(X_fit, y_fit)

        from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit
        skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=0)
        folds = list(skf.split(X, y))

        methods = {
            'unreduced': (None, None),
            'cnn': (run_cnn, None),
            'enn': (run_enn, None),
            'kmeans': (run_kmeans_prototypes, None),
            'random': (run_random_subsampling, None),
            'm1': (run_m1_prefilter, None),
            'm3': (None, lambda m, xv, yv: run_m3_prune(m, xv, yv, threshold=0)),
            'hybrid': (run_m1_prefilter, lambda m, xv, yv: run_m3_prune(m, xv, yv, threshold=0)),
        }

        for name, (pre, post) in methods.items():
            pre_params = {'keep_fraction': 0.5, 'interior_keep_rate': 0.0} if pre == run_m1_prefilter else \
                         {'ratio': 0.5} if pre == run_random_subsampling else \
                         {'k_per_class': 2} if pre == run_kmeans_prototypes else {}
            
            global_captured.clear()
            run_experiment(
                X, y,
                model_cls=TrackingFHLSNN,
                model_params={'zeta': 0.3, 'gamma': 1.0, 'membership_type': 'fhlsnn2001'},
                n_splits=3,
                random_state=0,
                pre_reducer_fn=pre,
                pre_reducer_params=pre_params,
                post_reducer_fn=post,
                post_reducer_params=None,
                tune_theta_gamma=False
            )
            
            assert len(global_captured) == 3, "Expected 3 folds"
            for fold_idx, (train_idx, test_idx) in enumerate(folds):
                sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=0)
                fit_rel, val_rel = next(sss.split(X[train_idx], y[train_idx]))
                actual_fit_idx = train_idx[fit_rel]
                actual_val_idx = train_idx[val_rel]
                actual_test_idx = test_idx

                X_passed, _ = global_captured[fold_idx]
                
                from sklearn.preprocessing import MinMaxScaler
                scaler = MinMaxScaler()
                scaler.fit(X[actual_fit_idx])
                X_passed_unscaled = scaler.inverse_transform(X_passed)
                
                passed_indices = set()
                # Fast row matching using the ID column (last column)
                for row in X_passed_unscaled:
                    idx = int(round(row[-1]))
                    passed_indices.add(idx)

                if name != 'kmeans':
                    assert passed_indices.issubset(set(actual_fit_idx)), f"{name} fold {fold_idx} passed indices not subset of fit_idx"
                    if name == 'unreduced':
                        assert passed_indices == set(actual_fit_idx), f"unreduced fold {fold_idx} passed indices != fit_idx"
                
                    intersection_val = passed_indices.intersection(set(actual_val_idx))
                    intersection_test = passed_indices.intersection(set(actual_test_idx))
                    assert len(intersection_val) == 0, f"{name} fold {fold_idx} leaked val indices!"
                    assert len(intersection_test) == 0, f"{name} fold {fold_idx} leaked test indices!"
