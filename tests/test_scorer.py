"""Tests for the technology-focused scoring engine."""

from __future__ import annotations

import pytest

from src.models import (
    AnalysisResult,
    CodeAnalysisResult,
    ConsistencyResult,
    DocAnalysisResult,
    GitForensicsResult,
    RedFlag,
    Severity,
)
from src.score.scorer import Scorer


@pytest.fixture
def scorer() -> Scorer:
    return Scorer()


def _make_result(
    total_files: int = 50,
    total_lines: int = 5000,
    api_wrapper_ratio: float = 0.1,
    has_tests: bool = True,
    has_ci_cd: bool = True,
    has_docs: bool = True,
    dependency_count: int = 20,
    total_commits: int = 200,
    unique_authors: int = 3,
    rush_commit_ratio: float = 0.0,
    consistency_score: float = 80.0,
    contradictions: int = 0,
    code_red_flags: list[RedFlag] | None = None,
    git_red_flags: list[RedFlag] | None = None,
) -> AnalysisResult:
    """Create an AnalysisResult with configurable parameters for testing."""
    return AnalysisResult(
        project_name="test-project",
        code_analysis=CodeAnalysisResult(
            total_files=total_files,
            total_lines=total_lines,
            languages={".py": 30, ".js": 15, ".ts": 5},
            api_wrapper_ratio=api_wrapper_ratio,
            has_tests=has_tests,
            has_ci_cd=has_ci_cd,
            has_documentation=has_docs,
            dependency_count=dependency_count,
            red_flags=code_red_flags or [],
        ),
        doc_analysis=DocAnalysisResult(),
        git_forensics=GitForensicsResult(
            total_commits=total_commits,
            unique_authors=unique_authors,
            rush_commit_ratio=rush_commit_ratio,
            red_flags=git_red_flags or [],
        ),
        consistency=ConsistencyResult(
            consistency_score=consistency_score,
            contradictions=["c"] * contradictions,
            verified_claims=["v"] * int(consistency_score / 10),
        ),
    )


class TestScorerBasic:
    """Basic scoring tests."""

    def test_healthy_project_scores_high(self, scorer: Scorer) -> None:
        """A project with good metrics should score 60+."""
        result = _make_result()
        score = scorer.score(result)
        assert score.overall_score >= 60
        assert score.grade in ("A", "B", "C")

    def test_api_wrapper_scores_low(self, scorer: Scorer) -> None:
        """A project with high API wrapper ratio should score poorly on originality."""
        result = _make_result(api_wrapper_ratio=0.8, total_lines=300)
        score = scorer.score(result)
        originality = next(d for d in score.dimensions if "Originality" in d.name)
        assert originality.score <= 30  # Lv.1-3 range for high wrapper ratio

    def test_no_tests_penalizes_implementation(self, scorer: Scorer) -> None:
        """Missing tests should reduce implementation depth score."""
        with_tests = _make_result(has_tests=True)
        without_tests = _make_result(has_tests=False)

        score_with = scorer.score(with_tests)
        score_without = scorer.score(without_tests)

        impl_with = next(d for d in score_with.dimensions if "Implementation" in d.name)
        impl_without = next(d for d in score_without.dimensions if "Implementation" in d.name)

        assert impl_with.score > impl_without.score


class TestTechLevelRatings:
    """10-level technology rating tests."""

    def test_tech_ratings_present(self, scorer: Scorer) -> None:
        """All 6 tech level ratings should be present."""
        result = _make_result()
        score = scorer.score(result)
        assert len(score.tech_ratings) == 6

    def test_ratings_have_levels_1_to_10(self, scorer: Scorer) -> None:
        """All ratings should have levels between 1 and 10."""
        result = _make_result()
        score = scorer.score(result)
        for rating in score.tech_ratings:
            assert 1 <= rating.level <= 10

    def test_wrapper_gets_low_originality_level(self, scorer: Scorer) -> None:
        """API wrapper should get originality level 1-2."""
        result = _make_result(api_wrapper_ratio=0.9, total_lines=200)
        score = scorer.score(result)
        originality_rating = next(
            r for r in score.tech_ratings if "Originality" in r.dimension
        )
        assert originality_rating.level <= 2

    def test_large_codebase_gets_higher_level(self, scorer: Scorer) -> None:
        """Large codebase with low wrapper ratio should get higher levels."""
        result = _make_result(total_lines=25000, api_wrapper_ratio=0.05, total_files=200)
        score = scorer.score(result)
        originality_rating = next(
            r for r in score.tech_ratings if "Originality" in r.dimension
        )
        assert originality_rating.level >= 6

    def test_each_rating_has_criteria(self, scorer: Scorer) -> None:
        """Each rating should include the full 10-level criteria list."""
        result = _make_result()
        score = scorer.score(result)
        for rating in score.tech_ratings:
            assert len(rating.criteria) == 10

    def test_rating_has_japanese_labels(self, scorer: Scorer) -> None:
        """Ratings should include Japanese dimension names."""
        result = _make_result()
        score = scorer.score(result)
        for rating in score.tech_ratings:
            assert rating.dimension_ja != ""


class TestNoTeamDimension:
    """Verify team evaluation has been removed."""

    def test_no_team_dimension(self, scorer: Scorer) -> None:
        """Team & Process dimension should NOT exist."""
        result = _make_result()
        score = scorer.score(result)
        team_dims = [d for d in score.dimensions if "Team" in d.name]
        assert len(team_dims) == 0

    def test_six_tech_dimensions(self, scorer: Scorer) -> None:
        """Should have exactly 6 technology-focused dimensions."""
        result = _make_result()
        score = scorer.score(result)
        assert len(score.dimensions) == 6
        dim_names = {d.name for d in score.dimensions}
        assert "Technical Originality" in dim_names
        assert "Technology Advancement" in dim_names
        assert "Implementation Depth" in dim_names
        assert "Architecture Quality" in dim_names
        assert "Claim Consistency" in dim_names
        assert "Security Posture" in dim_names


class TestRedFlags:
    """Red flag detection and impact tests."""

    def test_critical_flag_caps_score(self, scorer: Scorer) -> None:
        """A critical red flag should cap the overall score at 40."""
        critical_flag = RedFlag(
            category="code_originality",
            title="Pure API wrapper",
            description="Product is entirely an API wrapper.",
            severity=Severity.CRITICAL,
        )
        result = _make_result(code_red_flags=[critical_flag])
        score = scorer.score(result)
        assert score.overall_score <= 40
        assert score.grade in ("D", "F")

    def test_multiple_red_flags_aggregated(self, scorer: Scorer) -> None:
        """All red flags from all sources should be aggregated."""
        code_flag = RedFlag(
            category="code_quality",
            title="No tests",
            description="No test files.",
            severity=Severity.MEDIUM,
        )
        git_flag = RedFlag(
            category="git",
            title="Rush commits",
            description="Dense commit clusters.",
            severity=Severity.HIGH,
        )
        result = _make_result(code_red_flags=[code_flag], git_red_flags=[git_flag])
        score = scorer.score(result)
        assert len(score.red_flags) >= 2


class TestConsistency:
    """Consistency scoring tests."""

    def test_high_consistency_scores_well(self, scorer: Scorer) -> None:
        result = _make_result(consistency_score=90.0, contradictions=0)
        score = scorer.score(result)
        consistency_dim = next(d for d in score.dimensions if "Consistency" in d.name)
        assert consistency_dim.score >= 80

    def test_contradictions_reduce_score(self, scorer: Scorer) -> None:
        clean = _make_result(consistency_score=80.0, contradictions=0)
        dirty = _make_result(consistency_score=80.0, contradictions=5)

        score_clean = scorer.score(clean)
        score_dirty = scorer.score(dirty)

        cons_clean = next(d for d in score_clean.dimensions if "Consistency" in d.name)
        cons_dirty = next(d for d in score_dirty.dimensions if "Consistency" in d.name)

        assert cons_clean.score > cons_dirty.score


class TestGradeMapping:
    """Grade assignment tests."""

    def test_grade_f_for_terrible_project(self, scorer: Scorer) -> None:
        critical = RedFlag(
            category="test",
            title="Fake",
            description="Everything is fake.",
            severity=Severity.CRITICAL,
        )
        result = _make_result(
            total_files=2,
            total_lines=50,
            api_wrapper_ratio=0.9,
            has_tests=False,
            has_ci_cd=False,
            has_docs=False,
            total_commits=3,
            unique_authors=1,
            consistency_score=10.0,
            contradictions=5,
            code_red_flags=[critical],
        )
        score = scorer.score(result)
        assert score.grade in ("D", "F")
        assert score.overall_score <= 40

    def test_score_compute_is_idempotent(self, scorer: Scorer) -> None:
        result = _make_result()
        score1 = scorer.score(result)
        score2 = scorer.score(result)
        assert score1.overall_score == score2.overall_score
        assert score1.grade == score2.grade


class TestWeights:
    """Verify dimension weights sum to 1.0."""

    def test_weights_sum_to_one(self, scorer: Scorer) -> None:
        result = _make_result()
        score = scorer.score(result)
        total_weight = sum(d.weight for d in score.dimensions)
        assert abs(total_weight - 1.0) < 0.01
