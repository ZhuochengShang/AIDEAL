from MDAnalysis.lib.util import check_box
import numpy as np

# Use a valid box array instead of None or an empty/invalid structure
# The GRO fixture has valid dimensions
box_dims = np.array([50.0, 50.0, 50.0, 90.0, 90.0, 90.0], dtype=np.float32)
boxtype, checked_box = check_box(box_dims)

# Verify the output based on the documented contract
if boxtype == 'ortho':
    assert checked_box.shape == (3,)
    assert np.all(checked_box > 0)
elif boxtype == 'tri_vecs':
    assert checked_box.shape == (3, 3)
else:
    raise ValueError("Unknown boxtype returned")

print(f"__CHECK__ python:MDAnalysis.lib.util.check_box {boxtype} {checked_box.shape}")