# profile-drag

To make good prediction of the position of the lower attachment point (connection harness/glider) it's necessary to know about all acting forces. All forces are split into drag (parallel to v_inf) and lift (perpendicular to v_inf)
- Lift of the wing:
		Predicted via the panel-method (para-bem) by summing pressure over all surfaces and computing the v_inf perpendicular part. Dependent on wake definitions.
- Induced drag:
		Predicted via the panel-method (para-bem) by summing pressure over all surfaces and computing the v_inf parallel part.
- Line drag are predicted with a specific cd-value for each line and is accessible via `lineset.get_drag`.
- Pilot drag:
		Best to predict with experiement / calibration.  s * rho * v**2 / 2  (s ~ 0.8, rho = 1.2, v ~ 11)
- Profile-drag:
		Lift and drag predicted by computing the potential-flow does not take viscous drag into account. A prediction can be made by using the known drag and a given glide-angle.

