package com.parrotcare.mobile.data;

import android.content.Context;
import android.net.Uri;
import android.util.Base64;

import com.parrotcare.mobile.data.LocalStore.ParrotEvent;
import com.parrotcare.mobile.data.LocalStore.ParrotProfile;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

public final class BackupStore {
    public static final class ImportResult {
        public int parrots;
        public int events;
        public int skipped;
    }

    private final Context context;
    private final LocalStore store;
    private final AudioFileStore files;

    public BackupStore(Context context, LocalStore store, AudioFileStore files) {
        this.context = context.getApplicationContext();
        this.store = store;
        this.files = files;
    }

    public File exportBackup() throws IOException {
        File target = new File(files.exportDirectory(), "parrot-care-backup-" + System.currentTimeMillis() + ".zip");
        List<ParrotProfile> parrots = store.listParrots();
        List<ParrotEvent> events = store.listEvents("all", "all", "all", "all");
        try (ZipOutputStream zip = new ZipOutputStream(new FileOutputStream(target))) {
            writeText(zip, "version.txt", "parrot-care-backup-v1\n");
            writeText(zip, "parrots.tsv", encodeParrots(parrots));
            writeText(zip, "events.tsv", encodeEvents(events));
            for (ParrotEvent event : events) {
                File audio = files.resolve(event.audioPath);
                if (audio == null || !audio.exists() || !audio.isFile()) {
                    continue;
                }
                zip.putNextEntry(new ZipEntry("audio/" + audio.getName()));
                try (InputStream input = new java.io.FileInputStream(audio)) {
                    byte[] buffer = new byte[8192];
                    int read;
                    while ((read = input.read(buffer)) != -1) {
                        zip.write(buffer, 0, read);
                    }
                }
                zip.closeEntry();
            }
        }
        return target;
    }

    public ImportResult importBackup(Uri uri) throws IOException {
        ImportResult result = new ImportResult();
        Map<String, byte[]> entries = readZip(uri);
        String version = text(entries, "version.txt");
        if (!version.startsWith("parrot-care-backup-v1")) {
            throw new IOException("备份版本不支持");
        }

        Map<String, String> parrotMap = new HashMap<>();
        String parrotsText = text(entries, "parrots.tsv");
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
            new java.io.ByteArrayInputStream(parrotsText.getBytes(StandardCharsets.UTF_8)),
            StandardCharsets.UTF_8
        ))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.trim().length() == 0) continue;
                String[] parts = line.split("\t", -1);
                if (parts.length < 5) {
                    result.skipped++;
                    continue;
                }
                String oldId = parts[0];
                String newId = store.saveParrot(dec(parts[1]), dec(parts[2]), dec(parts[3]), dec(parts[4]));
                parrotMap.put(oldId, newId);
                result.parrots++;
            }
        }

        String defaultParrotId = store.ensureDefaultParrot();
        String eventsText = text(entries, "events.tsv");
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
            new java.io.ByteArrayInputStream(eventsText.getBytes(StandardCharsets.UTF_8)),
            StandardCharsets.UTF_8
        ))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.trim().length() == 0) continue;
                String[] parts = line.split("\t", -1);
                if (parts.length < 9) {
                    result.skipped++;
                    continue;
                }
                try {
                    String parrotId = parrotMap.containsKey(parts[1]) ? parrotMap.get(parts[1]) : defaultParrotId;
                    String audioPath = "";
                    String audioName = dec(parts[6]);
                    if (audioName.length() > 0) {
                        byte[] audioBytes = entries.get("audio/" + audioName);
                        if (audioBytes == null) {
                            result.skipped++;
                            continue;
                        }
                        File copied = new File(files.audioDirectory(), "imported-" + UUID.randomUUID() + "-" + audioName);
                        try (FileOutputStream output = new FileOutputStream(copied)) {
                            output.write(audioBytes);
                        }
                        audioPath = files.relativePath(copied);
                    }
                    store.saveEvent(
                        parrotId,
                        dec(parts[2]),
                        dec(parts[3]),
                        dec(parts[4]),
                        audioPath,
                        dec(parts[5]),
                        Long.parseLong(parts[7]),
                        dec(parts[8])
                    );
                    result.events++;
                } catch (RuntimeException badRow) {
                    result.skipped++;
                }
            }
        }
        return result;
    }

    private Map<String, byte[]> readZip(Uri uri) throws IOException {
        Map<String, byte[]> entries = new HashMap<>();
        InputStream input = context.getContentResolver().openInputStream(uri);
        if (input == null) throw new IOException("无法打开备份文件");
        try (ZipInputStream zip = new ZipInputStream(input)) {
            ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                if (entry.isDirectory()) continue;
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                byte[] buffer = new byte[8192];
                int read;
                while ((read = zip.read(buffer)) != -1) {
                    bytes.write(buffer, 0, read);
                }
                entries.put(entry.getName(), bytes.toByteArray());
            }
        }
        return entries;
    }

    private void writeText(ZipOutputStream zip, String name, String text) throws IOException {
        zip.putNextEntry(new ZipEntry(name));
        zip.write(text.getBytes(StandardCharsets.UTF_8));
        zip.closeEntry();
    }

    private String encodeParrots(List<ParrotProfile> parrots) {
        StringBuilder builder = new StringBuilder();
        for (ParrotProfile parrot : parrots) {
            builder.append(parrot.id).append('\t')
                .append(enc(parrot.name)).append('\t')
                .append(enc(parrot.species)).append('\t')
                .append(enc(parrot.birthday)).append('\t')
                .append(enc(parrot.note)).append('\n');
        }
        return builder.toString();
    }

    private String encodeEvents(List<ParrotEvent> events) {
        StringBuilder builder = new StringBuilder();
        for (ParrotEvent event : events) {
            File audio = files.resolve(event.audioPath);
            String audioName = audio == null ? "" : audio.getName();
            builder.append(event.id).append('\t')
                .append(event.parrotId).append('\t')
                .append(enc(event.categoryId)).append('\t')
                .append(enc(event.status)).append('\t')
                .append(enc(event.purpose)).append('\t')
                .append(enc(event.source)).append('\t')
                .append(enc(audioName)).append('\t')
                .append(event.durationMs).append('\t')
                .append(enc(event.note)).append('\n');
        }
        return builder.toString();
    }

    private String text(Map<String, byte[]> entries, String name) throws IOException {
        byte[] data = entries.get(name);
        if (data == null) throw new IOException("备份缺少 " + name);
        return new String(data, StandardCharsets.UTF_8);
    }

    private String enc(String value) {
        String safe = value == null ? "" : value;
        return Base64.encodeToString(safe.getBytes(StandardCharsets.UTF_8), Base64.NO_WRAP);
    }

    private String dec(String value) {
        if (value == null || value.length() == 0) return "";
        return new String(Base64.decode(value, Base64.NO_WRAP), StandardCharsets.UTF_8);
    }
}
