"""Exercise native guidance directly and through an importing library module."""
import json
import numpy as np
from MDAnalysis.lib.util import check_box
from MDAnalysis.lib import distances

expected = "Box is None [AIDEAL fix:box_cannot_be_none] Ensure the input 'box' is a valid array-like object representing unit cell dimensions, not None."
observed = {}
for name, call in [
    ('direct', lambda: check_box(None)),
    ('dependent_module', lambda: distances.transform_RtoS(np.array([[1., 2., 3.]]), None)),
]:
    try:
        call()
    except ValueError as error:
        assert str(error) == expected
        observed[name] = str(error)
    else:
        raise AssertionError('Expected the native None-box diagnostic')
box = np.array([10., 20., 30., 90., 90., 90.])
kind, lengths = check_box(box)
assert kind == 'ortho' and lengths.dtype == np.float32
np.testing.assert_array_equal(lengths, [10., 20., 30.])
np.testing.assert_allclose(distances.transform_RtoS(np.array([[1., 2., 3.]]), box), [[.1, .1, .1]])
try:
    check_box(np.array([10., 20., 30.]))
except ValueError as error:
    assert '[AIDEAL fix:' not in str(error)
    observed['nearby_negative'] = str(error)
else:
    raise AssertionError('Expected original invalid-shape diagnostic')
print(json.dumps({'messages': observed, 'valid_kind': kind, 'valid_lengths': lengths.tolist(),
                  'dependent_function_binding': distances.check_box is check_box}))
