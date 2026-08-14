package com.parrotcare.mobile.audio;

public final class AudioFeatures {
    public final double loudnessDb;
    public final double peakDb;
    public final double activityRatio;
    public final long decodedSamples;

    public AudioFeatures(double loudnessDb, double peakDb, double activityRatio, long decodedSamples) {
        this.loudnessDb = loudnessDb;
        this.peakDb = peakDb;
        this.activityRatio = activityRatio;
        this.decodedSamples = decodedSamples;
    }
}
