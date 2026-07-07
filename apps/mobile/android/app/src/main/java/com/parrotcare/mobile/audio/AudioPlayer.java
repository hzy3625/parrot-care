package com.parrotcare.mobile.audio;

import android.media.MediaPlayer;

import java.io.File;
import java.io.IOException;

public final class AudioPlayer {
    private MediaPlayer player;
    private File currentFile;

    public void play(File file) throws IOException {
        if (isPlaying() && currentFile != null && currentFile.equals(file)) {
            pause();
            return;
        }
        stop();
        currentFile = file;
        player = new MediaPlayer();
        player.setDataSource(file.getAbsolutePath());
        player.setOnCompletionListener(done -> stop());
        player.prepare();
        player.start();
    }

    public void pause() {
        if (player != null && player.isPlaying()) {
            player.pause();
        }
    }

    public void stop() {
        if (player != null) {
            try {
                player.stop();
            } catch (RuntimeException ignored) {
                // Player may already be stopped; release below is still required.
            }
            player.release();
            player = null;
        }
        currentFile = null;
    }

    public boolean isPlaying() {
        return player != null && player.isPlaying();
    }
}
