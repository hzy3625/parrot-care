package com.parrotcare.mobile.data;

import android.content.ContentValues;
import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import java.io.File;
import java.util.UUID;

public final class LocalStore extends SQLiteOpenHelper {
    private static final String DATABASE_NAME = "parrotcare.db";
    private static final int DATABASE_VERSION = 1;

    public LocalStore(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase database) {
        database.execSQL(
            "CREATE TABLE events (" +
                "id TEXT PRIMARY KEY," +
                "type TEXT NOT NULL," +
                "status TEXT NOT NULL," +
                "audio_path TEXT," +
                "created_at INTEGER NOT NULL" +
            ")"
        );
    }

    @Override
    public void onUpgrade(SQLiteDatabase database, int oldVersion, int newVersion) {
        // Add explicit forward-only migrations when DATABASE_VERSION changes.
    }

    public String saveRecording(File audioFile) {
        String id = UUID.randomUUID().toString();
        ContentValues values = new ContentValues();
        values.put("id", id);
        values.put("type", "unclassified");
        values.put("status", "pending");
        values.put("audio_path", audioFile.getAbsolutePath());
        values.put("created_at", System.currentTimeMillis());
        getWritableDatabase().insertOrThrow("events", null, values);
        return id;
    }
}
