package com.parrotcare.mobile.audio;

import java.util.List;

public final class BaselineComparison {
    private BaselineComparison() {
    }

    public static Result compare(AudioFeatures current, List<AudioFeatures> references) {
        if (current == null || references == null || references.isEmpty()) {
            throw new IllegalArgumentException("至少需要一条日常基线");
        }

        double loudness = 0.0d;
        double peak = 0.0d;
        double activity = 0.0d;
        for (AudioFeatures reference : references) {
            loudness += reference.loudnessDb;
            peak += reference.peakDb;
            activity += reference.activityRatio;
        }
        int count = references.size();
        AudioFeatures average = new AudioFeatures(loudness / count, peak / count, activity / count, 0L);
        double loudnessDelta = current.loudnessDb - average.loudnessDb;
        double peakDelta = current.peakDb - average.peakDb;
        double activityDelta = current.activityRatio - average.activityRatio;

        int score = severity(Math.abs(loudnessDelta), 3.0d, 6.0d)
            + severity(Math.abs(peakDelta), 3.0d, 6.0d)
            + severity(Math.abs(activityDelta), 0.12d, 0.25d);
        String level = score >= 5 ? "变化明显" : score >= 2 ? "有一定变化" : "接近日常基线";
        return new Result(level, current, average, count, loudnessDelta, peakDelta, activityDelta);
    }

    private static int severity(double value, double medium, double high) {
        if (value >= high) return 2;
        if (value >= medium) return 1;
        return 0;
    }

    public static final class Result {
        public final String level;
        public final AudioFeatures current;
        public final AudioFeatures baseline;
        public final int referenceCount;
        public final double loudnessDelta;
        public final double peakDelta;
        public final double activityDelta;

        Result(String level, AudioFeatures current, AudioFeatures baseline, int referenceCount, double loudnessDelta, double peakDelta, double activityDelta) {
            this.level = level;
            this.current = current;
            this.baseline = baseline;
            this.referenceCount = referenceCount;
            this.loudnessDelta = loudnessDelta;
            this.peakDelta = peakDelta;
            this.activityDelta = activityDelta;
        }
    }
}
