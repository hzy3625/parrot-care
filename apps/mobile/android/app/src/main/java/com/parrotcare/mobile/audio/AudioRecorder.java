package com.parrotcare.mobile.audio;

import android.media.MediaRecorder;

import java.io.File;
import java.io.IOException;

public final class AudioRecorder {
    private MediaRecorder recorder;
    private File outputFile;

    public void start(File target) throws IOException {
        if (recorder != null) {
            throw new IllegalStateException("Recorder is already running");
        }
        outputFile = target;
        recorder = new MediaRecorder();
        recorder.setAudioSource(MediaRecorder.AudioSource.MIC);
        recorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
        recorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
        recorder.setAudioSamplingRate(16_000);
        recorder.setAudioEncodingBitRate(32_000);
        recorder.setOutputFile(target.getAbsolutePath());
        recorder.prepare();
        recorder.start();
    }

    public File stop() {
        if (recorder == null) {
            return null;
        }
        try {
            recorder.stop();
            return outputFile;
        } catch (RuntimeException invalidRecording) {
            if (outputFile != null) {
                outputFile.delete();
            }
            return null;
        } finally {
            recorder.release();
            recorder = null;
            outputFile = null;
        }
    }

    public void cancel() {
        File cancelledRecording = stop();
        if (cancelledRecording != null) {
            cancelledRecording.delete();
        }
    }

    public boolean isRecording() {
        return recorder != null;
    }
}
