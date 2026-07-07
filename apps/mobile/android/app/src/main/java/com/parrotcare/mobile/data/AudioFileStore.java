package com.parrotcare.mobile.data;

import android.content.Context;
import android.media.MediaMetadataRetriever;
import android.net.Uri;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.UUID;

public final class AudioFileStore {
    private final Context context;

    public AudioFileStore(Context context) {
        this.context = context.getApplicationContext();
    }

    public File audioDirectory() throws IOException {
        File directory = new File(context.getFilesDir(), "audio");
        if (!directory.exists() && !directory.mkdirs()) {
            throw new IOException("Cannot create audio directory");
        }
        return directory;
    }

    public File exportDirectory() throws IOException {
        File directory = new File(context.getFilesDir(), "exports");
        if (!directory.exists() && !directory.mkdirs()) {
            throw new IOException("Cannot create export directory");
        }
        return directory;
    }

    public File newRecordingFile() throws IOException {
        return new File(audioDirectory(), "recording-" + System.currentTimeMillis() + ".m4a");
    }

    public File copyFromUri(Uri uri) throws IOException {
        String name = "import-" + System.currentTimeMillis() + "-" + UUID.randomUUID() + ".audio";
        File target = new File(audioDirectory(), name);
        try (InputStream input = context.getContentResolver().openInputStream(uri);
             FileOutputStream output = new FileOutputStream(target)) {
            if (input == null) {
                throw new IOException("Cannot open selected audio");
            }
            byte[] buffer = new byte[8192];
            int read;
            while ((read = input.read(buffer)) != -1) {
                output.write(buffer, 0, read);
            }
        }
        if (target.length() <= 0) {
            deleteQuietly(target);
            throw new IOException("Selected audio is empty");
        }
        return target;
    }

    public long durationMs(File file) {
        MediaMetadataRetriever retriever = new MediaMetadataRetriever();
        try {
            retriever.setDataSource(file.getAbsolutePath());
            String duration = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION);
            if (duration == null || duration.length() == 0) {
                return 0L;
            }
            return Long.parseLong(duration);
        } catch (RuntimeException ignored) {
            return 0L;
        } finally {
            try {
                retriever.release();
            } catch (Exception ignored) {
                // Ignore release errors on platform implementations.
            }
        }
    }

    public String relativePath(File file) {
        String filesRoot = context.getFilesDir().getAbsolutePath();
        String absolute = file.getAbsolutePath();
        if (absolute.startsWith(filesRoot + File.separator)) {
            return absolute.substring(filesRoot.length() + 1);
        }
        return absolute;
    }

    public File resolve(String path) {
        if (path == null || path.length() == 0) {
            return null;
        }
        File candidate = new File(path);
        if (candidate.isAbsolute()) {
            return candidate;
        }
        return new File(context.getFilesDir(), path);
    }

    public void deleteQuietly(File file) {
        if (file != null && file.exists()) {
            file.delete();
        }
    }
}
