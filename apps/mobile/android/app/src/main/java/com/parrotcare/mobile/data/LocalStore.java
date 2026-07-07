package com.parrotcare.mobile.data;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public final class LocalStore extends SQLiteOpenHelper {
    private static final String DATABASE_NAME = "parrotcare.db";
    private static final int DATABASE_VERSION = 2;
    public static final String DEFAULT_PARROT_NAME = "默认鹦鹉";

    public LocalStore(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase database) {
        createParrots(database);
        createEvents(database);
        insertDefaultParrot(database);
    }

    @Override
    public void onUpgrade(SQLiteDatabase database, int oldVersion, int newVersion) {
        if (oldVersion < 2) {
            migrateToV2(database);
        }
    }

    private void migrateToV2(SQLiteDatabase database) {
        createParrots(database);
        String defaultParrotId = insertDefaultParrot(database);
        database.execSQL("ALTER TABLE events RENAME TO events_v1");
        createEvents(database);
        database.execSQL(
            "INSERT INTO events (id, parrot_id, category_id, status, purpose, audio_path, source, duration_ms, note, created_at, updated_at) " +
                "SELECT id, ?, type, status, 'abnormal', audio_path, 'recording', 0, '', created_at, created_at FROM events_v1",
            new Object[]{defaultParrotId}
        );
        database.execSQL("DROP TABLE events_v1");
    }

    private void createParrots(SQLiteDatabase database) {
        database.execSQL(
            "CREATE TABLE IF NOT EXISTS parrots (" +
                "id TEXT PRIMARY KEY," +
                "name TEXT NOT NULL," +
                "species TEXT NOT NULL DEFAULT ''," +
                "birthday TEXT NOT NULL DEFAULT ''," +
                "note TEXT NOT NULL DEFAULT ''," +
                "created_at INTEGER NOT NULL," +
                "updated_at INTEGER NOT NULL" +
            ")"
        );
    }

    private void createEvents(SQLiteDatabase database) {
        database.execSQL(
            "CREATE TABLE IF NOT EXISTS events (" +
                "id TEXT PRIMARY KEY," +
                "parrot_id TEXT NOT NULL," +
                "category_id TEXT NOT NULL," +
                "status TEXT NOT NULL," +
                "purpose TEXT NOT NULL," +
                "audio_path TEXT," +
                "source TEXT NOT NULL," +
                "duration_ms INTEGER NOT NULL DEFAULT 0," +
                "note TEXT NOT NULL DEFAULT ''," +
                "created_at INTEGER NOT NULL," +
                "updated_at INTEGER NOT NULL" +
            ")"
        );
    }

    private String insertDefaultParrot(SQLiteDatabase database) {
        String existing = findDefaultParrotId(database);
        if (existing != null) {
            return existing;
        }
        String id = UUID.randomUUID().toString();
        long now = System.currentTimeMillis();
        ContentValues values = new ContentValues();
        values.put("id", id);
        values.put("name", DEFAULT_PARROT_NAME);
        values.put("species", "");
        values.put("birthday", "");
        values.put("note", "自动创建，可在档案中修改。");
        values.put("created_at", now);
        values.put("updated_at", now);
        database.insertOrThrow("parrots", null, values);
        return id;
    }

    private String findDefaultParrotId(SQLiteDatabase database) {
        try (Cursor cursor = database.query(
            "parrots",
            new String[]{"id"},
            "name=?",
            new String[]{DEFAULT_PARROT_NAME},
            null,
            null,
            "created_at ASC",
            "1"
        )) {
            if (cursor.moveToFirst()) {
                return cursor.getString(0);
            }
        }
        return null;
    }

    public String ensureDefaultParrot() {
        return insertDefaultParrot(getWritableDatabase());
    }

    public String saveParrot(String name, String species, String birthday, String note) {
        String id = UUID.randomUUID().toString();
        long now = System.currentTimeMillis();
        ContentValues values = parrotValues(id, name, species, birthday, note, now, now);
        getWritableDatabase().insertOrThrow("parrots", null, values);
        return id;
    }

    public void updateParrot(ParrotProfile parrot) {
        ContentValues values = new ContentValues();
        values.put("name", parrot.name);
        values.put("species", parrot.species);
        values.put("birthday", parrot.birthday);
        values.put("note", parrot.note);
        values.put("updated_at", System.currentTimeMillis());
        getWritableDatabase().update("parrots", values, "id=?", new String[]{parrot.id});
    }

    private ContentValues parrotValues(String id, String name, String species, String birthday, String note, long createdAt, long updatedAt) {
        ContentValues values = new ContentValues();
        values.put("id", id);
        values.put("name", clean(name, DEFAULT_PARROT_NAME));
        values.put("species", clean(species, ""));
        values.put("birthday", clean(birthday, ""));
        values.put("note", clean(note, ""));
        values.put("created_at", createdAt);
        values.put("updated_at", updatedAt);
        return values;
    }

    public List<ParrotProfile> listParrots() {
        List<ParrotProfile> parrots = new ArrayList<>();
        try (Cursor cursor = getReadableDatabase().query(
            "parrots",
            null,
            null,
            null,
            null,
            null,
            "created_at ASC"
        )) {
            while (cursor.moveToNext()) {
                parrots.add(readParrot(cursor));
            }
        }
        if (parrots.isEmpty()) {
            ensureDefaultParrot();
            return listParrots();
        }
        return parrots;
    }

    public ParrotProfile getParrot(String id) {
        try (Cursor cursor = getReadableDatabase().query(
            "parrots",
            null,
            "id=?",
            new String[]{id},
            null,
            null,
            null
        )) {
            if (cursor.moveToFirst()) {
                return readParrot(cursor);
            }
        }
        return null;
    }

    public String saveEvent(String parrotId, String categoryId, String status, String purpose, String audioPath, String source, long durationMs, String note) {
        String id = UUID.randomUUID().toString();
        long now = System.currentTimeMillis();
        ContentValues values = eventValues(id, parrotId, categoryId, status, purpose, audioPath, source, durationMs, note, now, now);
        getWritableDatabase().insertOrThrow("events", null, values);
        return id;
    }

    public void updateEvent(ParrotEvent event) {
        ContentValues values = new ContentValues();
        values.put("parrot_id", event.parrotId);
        values.put("category_id", event.categoryId);
        values.put("status", event.status);
        values.put("purpose", event.purpose);
        values.put("note", event.note);
        values.put("updated_at", System.currentTimeMillis());
        getWritableDatabase().update("events", values, "id=?", new String[]{event.id});
    }

    public void deleteEvent(String id) {
        getWritableDatabase().delete("events", "id=?", new String[]{id});
    }

    public ParrotEvent getEvent(String id) {
        List<ParrotEvent> records = queryEvents("events.id=?", new String[]{id}, "events.created_at DESC");
        return records.isEmpty() ? null : records.get(0);
    }

    public List<ParrotEvent> listEvents(String parrotId, String categoryId, String purpose, String status) {
        List<String> clauses = new ArrayList<>();
        List<String> args = new ArrayList<>();
        addFilter(clauses, args, "events.parrot_id", parrotId);
        addFilter(clauses, args, "events.category_id", categoryId);
        addFilter(clauses, args, "events.purpose", purpose);
        addFilter(clauses, args, "events.status", status);
        String where = clauses.isEmpty() ? null : joinClauses(clauses);
        return queryEvents(where, args.toArray(new String[0]), "events.created_at DESC");
    }

    public List<ParrotEvent> recentEvents(int limit) {
        return queryEvents(null, new String[0], "events.created_at DESC LIMIT " + limit);
    }

    private List<ParrotEvent> queryEvents(String where, String[] args, String order) {
        List<ParrotEvent> events = new ArrayList<>();
        String sql =
            "SELECT events.id, events.parrot_id, parrots.name, events.category_id, events.status, events.purpose, " +
                "events.audio_path, events.source, events.duration_ms, events.note, events.created_at, events.updated_at " +
                "FROM events LEFT JOIN parrots ON parrots.id = events.parrot_id " +
                (where == null ? "" : "WHERE " + where + " ") +
                "ORDER BY " + order;
        try (Cursor cursor = getReadableDatabase().rawQuery(sql, args)) {
            while (cursor.moveToNext()) {
                events.add(readEvent(cursor));
            }
        }
        return events;
    }

    private void addFilter(List<String> clauses, List<String> args, String column, String value) {
        if (value != null && value.length() > 0 && !"all".equals(value)) {
            clauses.add(column + "=?");
            args.add(value);
        }
    }

    private String joinClauses(List<String> clauses) {
        StringBuilder builder = new StringBuilder();
        for (int index = 0; index < clauses.size(); index++) {
            if (index > 0) builder.append(" AND ");
            builder.append(clauses.get(index));
        }
        return builder.toString();
    }

    private ContentValues eventValues(String id, String parrotId, String categoryId, String status, String purpose, String audioPath, String source, long durationMs, String note, long createdAt, long updatedAt) {
        ContentValues values = new ContentValues();
        values.put("id", id);
        values.put("parrot_id", clean(parrotId, ensureDefaultParrot()));
        values.put("category_id", clean(categoryId, "unclassified"));
        values.put("status", clean(status, "pending"));
        values.put("purpose", clean(purpose, "abnormal"));
        values.put("audio_path", clean(audioPath, null));
        values.put("source", clean(source, "manual"));
        values.put("duration_ms", Math.max(durationMs, 0L));
        values.put("note", clean(note, ""));
        values.put("created_at", createdAt);
        values.put("updated_at", updatedAt);
        return values;
    }

    private ParrotProfile readParrot(Cursor cursor) {
        return new ParrotProfile(
            cursor.getString(cursor.getColumnIndexOrThrow("id")),
            cursor.getString(cursor.getColumnIndexOrThrow("name")),
            cursor.getString(cursor.getColumnIndexOrThrow("species")),
            cursor.getString(cursor.getColumnIndexOrThrow("birthday")),
            cursor.getString(cursor.getColumnIndexOrThrow("note")),
            cursor.getLong(cursor.getColumnIndexOrThrow("created_at")),
            cursor.getLong(cursor.getColumnIndexOrThrow("updated_at"))
        );
    }

    private ParrotEvent readEvent(Cursor cursor) {
        return new ParrotEvent(
            cursor.getString(0),
            cursor.getString(1),
            cursor.getString(2) == null ? DEFAULT_PARROT_NAME : cursor.getString(2),
            cursor.getString(3),
            cursor.getString(4),
            cursor.getString(5),
            cursor.getString(6),
            cursor.getString(7),
            cursor.getLong(8),
            cursor.getString(9),
            cursor.getLong(10),
            cursor.getLong(11)
        );
    }

    private String clean(String value, String fallback) {
        if (value == null) return fallback;
        String trimmed = value.trim();
        return trimmed.length() == 0 ? fallback : trimmed;
    }

    public static final class ParrotProfile {
        public final String id;
        public String name;
        public String species;
        public String birthday;
        public String note;
        public final long createdAt;
        public final long updatedAt;

        public ParrotProfile(String id, String name, String species, String birthday, String note, long createdAt, long updatedAt) {
            this.id = id;
            this.name = name;
            this.species = species;
            this.birthday = birthday;
            this.note = note;
            this.createdAt = createdAt;
            this.updatedAt = updatedAt;
        }
    }

    public static final class ParrotEvent {
        public final String id;
        public String parrotId;
        public final String parrotName;
        public String categoryId;
        public String status;
        public String purpose;
        public final String audioPath;
        public final String source;
        public final long durationMs;
        public String note;
        public final long createdAt;
        public final long updatedAt;

        public ParrotEvent(String id, String parrotId, String parrotName, String categoryId, String status, String purpose, String audioPath, String source, long durationMs, String note, long createdAt, long updatedAt) {
            this.id = id;
            this.parrotId = parrotId;
            this.parrotName = parrotName;
            this.categoryId = categoryId;
            this.status = status;
            this.purpose = purpose;
            this.audioPath = audioPath;
            this.source = source;
            this.durationMs = durationMs;
            this.note = note;
            this.createdAt = createdAt;
            this.updatedAt = updatedAt;
        }
    }
}
