package com.parrotcare.mobile.data;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.res.AssetFileDescriptor;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;

import java.io.File;
import java.io.FileNotFoundException;

public final class SimpleFileProvider extends ContentProvider {
    @Override
    public boolean onCreate() {
        return true;
    }

    @Override
    public String getType(Uri uri) {
        String name = uri.getLastPathSegment();
        if (name != null && name.endsWith(".zip")) return "application/zip";
        return "application/octet-stream";
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs, String sortOrder) {
        File file = resolve(uri);
        MatrixCursor cursor = new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE});
        cursor.addRow(new Object[]{file.getName(), file.length()});
        return cursor;
    }

    @Override
    public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        if (!"r".equals(mode)) throw new FileNotFoundException("Read-only provider");
        File file = resolve(uri);
        if (!file.exists() || !file.isFile()) throw new FileNotFoundException(uri.toString());
        return ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY);
    }

    @Override
    public AssetFileDescriptor openAssetFile(Uri uri, String mode) throws FileNotFoundException {
        ParcelFileDescriptor descriptor = openFile(uri, mode);
        return new AssetFileDescriptor(descriptor, 0, AssetFileDescriptor.UNKNOWN_LENGTH);
    }

    @Override
    public Uri insert(Uri uri, ContentValues values) {
        throw new UnsupportedOperationException("insert");
    }

    @Override
    public int delete(Uri uri, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException("delete");
    }

    @Override
    public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException("update");
    }

    private File resolve(Uri uri) {
        String encoded = uri.getEncodedPath();
        String relative = encoded == null ? "" : Uri.decode(encoded);
        if (relative.startsWith("/")) relative = relative.substring(1);
        File root = getContext().getFilesDir();
        File candidate = new File(root, relative);
        try {
            String rootPath = root.getCanonicalPath();
            String candidatePath = candidate.getCanonicalPath();
            if (!candidatePath.startsWith(rootPath)) {
                throw new SecurityException("Path escapes app files");
            }
        } catch (java.io.IOException error) {
            throw new SecurityException("Invalid path");
        }
        return candidate;
    }
}
