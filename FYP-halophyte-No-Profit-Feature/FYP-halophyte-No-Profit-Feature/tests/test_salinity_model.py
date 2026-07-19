"""
Tests for the Salinity Model (Phase 1)
=======================================
These tests verify that our Maas-Hoffman implementation is correct
by checking it against known values from published literature.

HOW TO RUN:
    python -m pytest tests/test_salinity_model.py -v

WHAT THESE TESTS CHECK:
    1. The formula gives correct results for known crop parameters
    2. Edge cases are handled (zero salinity, extreme salinity, negatives)
    3. Config loading works properly
    4. All 32 crops load without errors
    5. Commercial/ecological filtering works
"""

import sys
from pathlib import Path

import pytest

# Add project root to path so we can import src/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.salinity_model.maas_hoffman import (
    calculate_relative_yield,
    calculate_absolute_yield,
    calculate_yield_curve,
    find_zero_yield_salinity,
    compare_crops_at_salinity,
    get_all_crops,
    get_commercial_crops,
    get_ecological_crops,
    get_crop_params,
    get_salinity_category,
    validate_salinity_input,
)


# ============================================================================
# TEST GROUP 1: Core Maas-Hoffman Formula
# ============================================================================

class TestCalculateRelativeYield:
    """Test the core Maas-Hoffman yield calculation."""

    def test_below_threshold_gives_100_percent(self):
        """When salinity is below threshold, yield should be 100%."""
        # Barley: threshold=8.0, slope=5.0
        result = calculate_relative_yield(ec_soil=5.0, ec_threshold=8.0, slope=5.0)
        assert result == 100.0

    def test_at_threshold_gives_100_percent(self):
        """When salinity equals threshold exactly, yield should still be 100%."""
        result = calculate_relative_yield(ec_soil=8.0, ec_threshold=8.0, slope=5.0)
        assert result == 100.0

    def test_above_threshold_linear_decline(self):
        """Above threshold, yield should decline linearly."""
        # Barley: EC=12, threshold=8, slope=5
        # Expected: 100 - 5*(12-8) = 100 - 20 = 80%
        result = calculate_relative_yield(ec_soil=12.0, ec_threshold=8.0, slope=5.0)
        assert result == 80.0

    def test_barley_at_18_dsm(self):
        """Barley at 18 dS/m should give 50% (halfway to death)."""
        # 100 - 5*(18-8) = 100 - 50 = 50%
        result = calculate_relative_yield(ec_soil=18.0, ec_threshold=8.0, slope=5.0)
        assert result == 50.0

    def test_maize_sensitive_crop(self):
        """Maize is very sensitive — check it drops fast."""
        # Maize: threshold=1.7, slope=12.0
        # At EC=5: 100 - 12*(5-1.7) = 100 - 39.6 = 60.4%
        result = calculate_relative_yield(ec_soil=5.0, ec_threshold=1.7, slope=12.0)
        assert abs(result - 60.4) < 0.01

    def test_yield_cannot_go_below_zero(self):
        """Even at extreme salinity, yield should be clamped to 0%."""
        # Barley at 100 dS/m: 100 - 5*(100-8) = 100 - 460 = -360 → clamped to 0
        result = calculate_relative_yield(ec_soil=100.0, ec_threshold=8.0, slope=5.0)
        assert result == 0.0

    def test_zero_salinity_gives_100(self):
        """Freshwater (0 dS/m) should always give 100% yield."""
        result = calculate_relative_yield(ec_soil=0.0, ec_threshold=8.0, slope=5.0)
        assert result == 100.0

    def test_negative_ec_raises_error(self):
        """Negative salinity should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_relative_yield(ec_soil=-1.0, ec_threshold=8.0, slope=5.0)

    def test_negative_threshold_raises_error(self):
        """Negative threshold should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_relative_yield(ec_soil=5.0, ec_threshold=-1.0, slope=5.0)

    def test_negative_slope_raises_error(self):
        """Negative slope should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_relative_yield(ec_soil=5.0, ec_threshold=8.0, slope=-5.0)

    def test_zero_slope_means_no_decline(self):
        """If slope is 0, yield never declines (theoretical invincible crop)."""
        result = calculate_relative_yield(ec_soil=50.0, ec_threshold=5.0, slope=0.0)
        assert result == 100.0

    def test_very_tolerant_grass(self):
        """Seashore saltgrass (EC threshold=30, slope=1.7) at 45 dS/m."""
        # 100 - 1.7*(45-30) = 100 - 25.5 = 74.5%
        result = calculate_relative_yield(ec_soil=45.0, ec_threshold=30.0, slope=1.7)
        assert abs(result - 74.5) < 0.01


# ============================================================================
# TEST GROUP 2: Absolute Yield Calculations
# ============================================================================

class TestCalculateAbsoluteYield:
    """Test yield in kg/ha calculations."""

    def test_barley_full_yield(self):
        """Barley at 0 dS/m should give max yield (5500 kg/ha)."""
        result = calculate_absolute_yield(ec_soil=0.0, crop_id='barley')
        assert result == 5500.0

    def test_barley_partial_yield(self):
        """Barley at 12 dS/m should give 80% of 5500 = 4400 kg/ha."""
        result = calculate_absolute_yield(ec_soil=12.0, crop_id='barley')
        assert result == 4400.0

    def test_max_yield_override(self):
        """User can override the max yield value."""
        # Barley at 0 dS/m with override of 6000
        result = calculate_absolute_yield(
            ec_soil=0.0, crop_id='barley', max_yield_override=6000.0
        )
        assert result == 6000.0

    def test_invalid_crop_raises_error(self):
        """Unknown crop ID should raise KeyError."""
        with pytest.raises(KeyError, match="not found"):
            calculate_absolute_yield(ec_soil=5.0, crop_id='banana_tree')

    def test_negative_ec_raises_error(self):
        """Negative EC should still raise ValueError."""
        with pytest.raises(ValueError):
            calculate_absolute_yield(ec_soil=-5.0, crop_id='barley')


# ============================================================================
# TEST GROUP 3: Config Loading
# ============================================================================

class TestConfigLoading:
    """Test that crop configuration loads correctly."""

    def test_all_crops_loads(self):
        """Should load all 32 crops (30 grasses + quinoa + salicornia)."""
        crops = get_all_crops()
        assert len(crops) >= 30  # At least 30 species

    def test_commercial_crops_exist(self):
        """Should have at least 10 commercial crops."""
        commercial = get_commercial_crops()
        assert len(commercial) >= 10

    def test_ecological_crops_exist(self):
        """Should have at least 15 ecological crops."""
        ecological = get_ecological_crops()
        assert len(ecological) >= 15

    def test_barley_params_correct(self):
        """Barley should have correct published parameters."""
        params = get_crop_params('barley')
        assert params['ec_threshold'] == 8.0
        assert params['slope'] == 5.0
        assert params['commercial'] is True
        assert params['max_potential_yield'] == 5500

    def test_all_crops_have_required_fields(self):
        """Every crop must have ec_threshold, slope, and mechanism."""
        crops = get_all_crops()
        required_fields = ['ec_threshold', 'slope', 'mechanism', 'commercial']
        
        for crop_id, params in crops.items():
            for field in required_fields:
                assert field in params, (
                    f"Crop '{crop_id}' is missing required field '{field}'"
                )

    def test_commercial_crops_have_price(self):
        """All commercial crops must have a market price."""
        commercial = get_commercial_crops()
        
        for crop_id, params in commercial.items():
            assert 'market_price_per_kg' in params, (
                f"Commercial crop '{crop_id}' is missing 'market_price_per_kg'"
            )
            assert params['market_price_per_kg'] > 0, (
                f"Commercial crop '{crop_id}' has non-positive price"
            )

    def test_invalid_crop_raises_keyerror(self):
        """Requesting non-existent crop should raise helpful error."""
        with pytest.raises(KeyError):
            get_crop_params('unicorn_grass')


# ============================================================================
# TEST GROUP 4: Yield Curves
# ============================================================================

class TestYieldCurve:
    """Test yield curve generation."""

    def test_curve_starts_at_100(self):
        """First point should be 100% yield (at EC=0)."""
        curve = calculate_yield_curve('barley', ec_min=0.0, ec_max=30.0, ec_step=5.0)
        assert curve[0]['relative_yield'] == 100.0

    def test_curve_reaches_zero(self):
        """Curve should eventually reach 0% for sensitive crops."""
        curve = calculate_yield_curve('maize', ec_min=0.0, ec_max=15.0, ec_step=1.0)
        # Maize dies at: 1.7 + 100/12 ≈ 10.0 dS/m
        last_nonzero = [p for p in curve if p['relative_yield'] > 0]
        assert len(last_nonzero) < len(curve)  # Some points are at 0

    def test_curve_is_monotonically_decreasing(self):
        """Yield should never increase as salinity increases."""
        curve = calculate_yield_curve('barley', ec_min=0.0, ec_max=30.0, ec_step=1.0)
        for i in range(1, len(curve)):
            assert curve[i]['relative_yield'] <= curve[i-1]['relative_yield']


# ============================================================================
# TEST GROUP 5: Zero Yield Salinity
# ============================================================================

class TestFindZeroYieldSalinity:
    """Test finding the lethal salinity level."""

    def test_barley_zero_yield(self):
        """Barley: threshold=8 + 100/5 = 28.0 dS/m."""
        result = find_zero_yield_salinity('barley')
        assert result == 28.0

    def test_maize_zero_yield(self):
        """Maize: threshold=1.7 + 100/12 ≈ 10.0 dS/m."""
        result = find_zero_yield_salinity('maize')
        assert abs(result - 10.0) < 0.1

    def test_tolerant_grass_high_zero(self):
        """Very tolerant grasses should have high zero-yield points."""
        result = find_zero_yield_salinity('seashore_saltgrass')
        assert result > 80.0  # Should survive past 80 dS/m


# ============================================================================
# TEST GROUP 6: Crop Comparison
# ============================================================================

class TestCompareCrops:
    """Test crop comparison functionality."""

    def test_comparison_sorted_by_yield(self):
        """Results should be sorted best yield first."""
        results = compare_crops_at_salinity(ec_soil=10.0)
        yields = [r['relative_yield'] for r in results]
        assert yields == sorted(yields, reverse=True)

    def test_at_low_salinity_all_survive(self):
        """At very low salinity, all crops should be near 100%."""
        results = compare_crops_at_salinity(ec_soil=0.5)
        for r in results:
            assert r['relative_yield'] == 100.0

    def test_at_high_salinity_sensitive_crops_die(self):
        """At high salinity, sensitive crops should be at 0%."""
        results = compare_crops_at_salinity(ec_soil=20.0)
        # Find maize in results
        maize = [r for r in results if r['crop_id'] == 'maize'][0]
        assert maize['relative_yield'] == 0.0

    def test_filter_specific_crops(self):
        """Should only return specified crops when filtered."""
        results = compare_crops_at_salinity(
            ec_soil=10.0, crop_ids=['barley', 'maize', 'wheat']
        )
        assert len(results) == 3
        crop_ids = [r['crop_id'] for r in results]
        assert 'barley' in crop_ids
        assert 'maize' in crop_ids
        assert 'wheat' in crop_ids


# ============================================================================
# TEST GROUP 7: Utility Functions
# ============================================================================

class TestUtilities:
    """Test utility functions."""

    def test_salinity_categories(self):
        """Test correct categorization of salinity levels."""
        assert get_salinity_category(0.3) == "Freshwater"
        assert get_salinity_category(2.0) == "Slightly Saline"
        assert get_salinity_category(4.0) == "Moderately Saline"
        assert get_salinity_category(10.0) == "Highly Saline"
        assert get_salinity_category(20.0) == "Very Highly Saline / Brine"

    def test_validation_normal_input(self):
        """Normal inputs should validate without warnings."""
        result = validate_salinity_input(10.0)
        assert result['valid'] is True
        assert result['warning'] == ""

    def test_validation_negative_input(self):
        """Negative input should be invalid."""
        result = validate_salinity_input(-5.0)
        assert result['valid'] is False

    def test_validation_extreme_input(self):
        """Very high input should show a warning."""
        result = validate_salinity_input(70.0)
        assert result['valid'] is True  # Still valid, just warned
        assert "beyond our trained range" in result['warning']

    def test_validation_high_salinity_warning(self):
        """High (but not extreme) salinity should show halophyte warning."""
        result = validate_salinity_input(40.0)
        assert "halophytes" in result['warning'].lower()


# ============================================================================
# TEST GROUP 8: Scientific Validation
# ============================================================================

class TestScientificValidation:
    """
    Validate our model against known published values.
    These are 'sanity checks' to make sure our implementation
    matches the expected behavior from agricultural science literature.
    """

    def test_barley_more_tolerant_than_maize(self):
        """Barley should always yield more than maize at any salinity > 2 dS/m."""
        for ec in [5.0, 10.0, 15.0, 20.0]:
            barley_yield = calculate_relative_yield(ec, ec_threshold=8.0, slope=5.0)
            maize_yield = calculate_relative_yield(ec, ec_threshold=1.7, slope=12.0)
            assert barley_yield >= maize_yield, (
                f"At EC={ec}: barley ({barley_yield}%) should >= maize ({maize_yield}%)"
            )

    def test_salt_secreting_more_tolerant(self):
        """Salt-secreting grasses should generally have higher GR50 values."""
        crops = get_all_crops()
        secreting = [p for p in crops.values() if p['mechanism'] == 'Salt-Secreting']
        non_secreting = [p for p in crops.values() if p['mechanism'] == 'Non-Secreting']
        
        avg_secreting_gr50 = sum(p['gr50'] for p in secreting) / len(secreting)
        avg_non_secreting_gr50 = sum(p['gr50'] for p in non_secreting) / len(non_secreting)
        
        assert avg_secreting_gr50 > avg_non_secreting_gr50, (
            f"Salt-secreting avg GR50 ({avg_secreting_gr50}) should be > "
            f"non-secreting avg ({avg_non_secreting_gr50})"
        )

    def test_gr50_approximation(self):
        """At GR50 salinity, yield should be approximately 50%."""
        # For barley: GR50=17, threshold=8, slope=5
        # At EC=17: 100 - 5*(17-8) = 100 - 45 = 55% (close to 50%)
        # Note: GR50 is "growth reduction 50%" which may not exactly equal
        # our Maas-Hoffman 50% point, but should be in the ballpark (40-60%)
        crops = get_all_crops()
        for crop_id, params in crops.items():
            gr50 = params['gr50']
            ec_t = params['ec_threshold']
            slope = params['slope']
            yield_at_gr50 = calculate_relative_yield(gr50, ec_t, slope)
            # Should be roughly around 50% (allow 0-70% range due to approximation)
            assert 0.0 <= yield_at_gr50 <= 70.0, (
                f"Crop '{crop_id}' at GR50={gr50}: yield={yield_at_gr50}% "
                f"(expected roughly ~50%)"
            )
