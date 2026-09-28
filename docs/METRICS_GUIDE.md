# Metrics and Figure Guide

## Rule for every reported result

Every report number or figure must have:

1. a named experiment;
2. a source data file;
3. a generation or calculation method;
4. a plain-language interpretation; and
5. a stated limitation.

If one of these is missing, the result is not ready for the report.

## Measurement metrics

### Range RMSE

Range root mean square error measures the typical size of range errors while giving larger errors more weight:

\[
\operatorname{RMSE}_r = \sqrt{\frac{1}{N}\sum_{k=1}^{N}(\hat r_k-r_k)^2}
\]

Here, `r` is evaluation-only ground-truth range and `r-hat` is camera-derived range. Smaller is better, but the test distances and visibility conditions must also be reported.

### Bearing MAE

Bearing mean absolute error is:

\[
\operatorname{MAE}_\theta = \frac{1}{N}\sum_{k=1}^{N}|\hat\theta_k-\theta_k|
\]

It reports the average absolute angular error in degrees or radians. The unit must always be shown.

### Detection precision and recall

- Precision asks: of all reported detections, how many were correct?
- Recall asks: of all real visible targets, how many were detected?

High precision with low recall can still cause frequent `PREDICT` or `SAFE STOP` transitions. A single confidence threshold should not be selected only from one scene.

## Formation metrics

### Spacing RMSE

Spacing RMSE compares the measured inter-robot spacing with the commanded spacing. It evaluates formation tracking, not perception alone.

### Minimum separation

Minimum separation is the smallest recorded distance between robots or obstacles. In simulation it is an evaluation metric, not proof of certified safety.

### Reacquisition time

Reacquisition time begins when an occlusion ends and stops when the detector and estimator satisfy the declared valid-track condition. That condition must be fixed before comparing runs.

### Supervisor state duration

Report how long the robot spent in `TRACK`, `PREDICT`, and `SAFE STOP`, along with transition counts and causes. A low spacing error is not enough if the robot spends an unacceptable time predicting without measurements.

## Computing metrics

- End-to-end latency: image timestamp to usable control output.
- Detection inference time: detector start to detector result.
- Camera delivery rate: received frames per second.
- Dropped-frame fraction: expected frames minus received frames, divided by expected frames.
- Real-time factor: simulated time divided by wall-clock time.
- CPU, RAM, GPU, and VRAM: report sampling method and peak or summary statistic.

The existing environment camera rate is a transport check. It is not detector throughput or closed-loop timing.

## Rearward error propagation

For the incremental chain, compare the same metric for Follower 1, Follower 2, and later followers under the same route and disturbances. Report both absolute values and the change from one position to the next.

Do not call the chain string stable or robust without a defined test and acceptance threshold.

## Figure checklist

Before placing a figure in the report, answer:

- What exact question does the figure answer?
- Which file contains the plotted data?
- Which script created it?
- What are the axes, units, sample count, and conditions?
- Is uncertainty or trial variation shown when relevant?
- What conclusion is supported?
- What stronger conclusion is not supported?
- Can Neeraj reproduce and explain it without reading generated prose?
