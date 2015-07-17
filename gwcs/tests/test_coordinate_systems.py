# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import, division, unicode_literals, print_function

import numpy as np
from numpy.testing import assert_almost_equal, assert_allclose
from astropy.modeling import models
from astropy import units as u
from astropy import coordinates as coord
from .. import coordinate_frames as cf
from .. import wcs

icrs = coord.ICRS()
fk5 = coord.FK5()
cel1 = cf.CelestialFrame(reference_frame=icrs)
cel2 = cf.CelestialFrame(reference_frame=fk5)

spec1 = cf.SpectralFrame(name='freq', unit=[u.Hz,], axes_order=(2,))
spec2 = cf.SpectralFrame(name='wave', unit=[u.m,], axes_order=(2,))

comp1 = cf.CompositeFrame([cel1, spec1])
comp2 = cf.CompositeFrame([cel2, spec2])
comp = cf.CompositeFrame([comp1, comp2])

m1 = models.Shift(12.4) & models.Shift(-2)
m2 = models.Scale(2) & models.Scale(-2)
icrs = cf.CelestialFrame(reference_frame=coord.ICRS())
det = cf.Frame2D(name='detector', axes_order=(0, 1))
focal = cf.Frame2D(name='focal', axes_order=(0, 1), unit=(u.m, u.m))
pipe = [(det, m1),
        (focal, m2),
        (icrs, None)
        ]


def test_units():
    assert(comp1.unit == [u.deg, u.deg, u.Hz])
    assert(comp2.unit == [u.deg, u.deg, u.m])
    assert(comp.unit == [u.deg, u.deg, u.Hz, u.deg, u.deg, u.m])


def test_transform_to_spectral():
    spec = cf.SpectralFrame(name='wave', unit=u.micron, axes_order=(2,))
    w = wcs.WCS(output_frame=spec, forward_transform=models.Polynomial1D(1, c1=1))
    q = w.output_frame.transform_to(5, 'Hz')
    assert(q.unit == u.Hz)


def test_coordinates_spatial():
    w = wcs.WCS(forward_transform=pipe)
    sky_coo = w.output_frame.coordinates(1, 3)
    sky = w(1, 3)
    assert_allclose((sky_coo.ra.value, sky_coo.dec.value), sky)


def test_coordinates_spectral():
    spec = cf.SpectralFrame(name='wavelength', unit=(u.micron,),
                            axes_order=(0,), axes_names=('lambda',))
    w = wcs.WCS(forward_transform=models.Polynomial1D(1, c0=.2, c1=.3), output_frame=spec)
    x = np.arange(10)
    wave = w.output_frame.coordinates(x)
    assert_allclose(wave.value, w(x))
    wave = w.output_frame.coordinates(1.2)
    assert_allclose(wave.value, w(1.2))


def test_coordinates_composite():
    spec = cf.SpectralFrame(name='wavelength', unit=(u.micron,),
                            axes_order=(2,), axes_names=('lambda',))
    icrs = cf.CelestialFrame(reference_frame=coord.ICRS(), axes_order=(0,1))
    frame = cf.CompositeFrame([icrs, spec])
    transform = models.Mapping([0, 0, 1]) | models.Identity(2) & models.Polynomial1D(1, c0=.2, c1=.3)
    w = wcs.WCS(forward_transform=transform, output_frame=frame, input_frame=det)
    x = np.arange(3)
    result = w.output_frame.coordinates(x, x)
    assert_allclose(result[0].ra.value, w(x, x)[0])
    assert_allclose(result[0].ra.value, w(x, x)[1])
    assert_allclose(result[1].value, w(x, x)[2])
